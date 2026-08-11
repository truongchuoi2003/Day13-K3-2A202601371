from __future__ import annotations

import os
import time
from dataclasses import dataclass

from . import metrics
from .mock_llm import FakeLLM
from .mock_rag import retrieve
from .pii import hash_user_id, scrub_text, summarize_text
from .prompt_management import resolve_prompt
from .tracing import get_langfuse_client, observe, propagate_attributes, tracing_enabled


@dataclass
class AgentResult:
    answer: str
    latency_ms: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    quality_score: float


class LabAgent:
    def __init__(self, model: str = "claude-sonnet-4-5") -> None:
        self.model = model
        self.llm = FakeLLM(model=model)

    @observe(name="chat-response", as_type="agent", capture_input=False, capture_output=False)
    def run(
        self,
        user_id: str,
        feature: str,
        session_id: str,
        message: str,
        correlation_id: str | None = None,
    ) -> AgentResult:
        started = time.perf_counter()
        langfuse_client = get_langfuse_client()
        trace_metadata = {
            "correlation_id": correlation_id or "unavailable",
            "route": "/chat",
            "feature": feature,
            "app_env": os.getenv("APP_ENV", "dev"),
        }
        trace_tags = ["lab", f"feature:{feature}", f"model:{self.model}"]

        if hasattr(langfuse_client, "start_as_current_observation"):
            result = self._run_with_v4_tracing(
                langfuse_client=langfuse_client,
                trace_metadata=trace_metadata,
                trace_tags=trace_tags,
                user_id=user_id,
                feature=feature,
                session_id=session_id,
                message=message,
                started=started,
            )
        else:  # pragma: no cover - compatibility for the lab's lightweight mock client
            result = self._run_with_legacy_trace_adapter(
                langfuse_client=langfuse_client,
                trace_metadata=trace_metadata,
                trace_tags=trace_tags,
                user_id=user_id,
                feature=feature,
                session_id=session_id,
                message=message,
                started=started,
            )

        metrics.record_request(
            latency_ms=result.latency_ms,
            cost_usd=result.cost_usd,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            quality_score=result.quality_score,
        )

        return result

    def _run_with_v4_tracing(
        self,
        *,
        langfuse_client,
        trace_metadata: dict[str, str],
        trace_tags: list[str],
        user_id: str,
        feature: str,
        session_id: str,
        message: str,
        started: float,
    ) -> AgentResult:
        safe_message = summarize_text(message)
        with propagate_attributes(
            trace_name="chat-response",
            user_id=hash_user_id(user_id),
            session_id=session_id,
            metadata=trace_metadata,
            tags=trace_tags,
            environment=os.getenv("APP_ENV", "dev"),
        ):
            # Explicit I/O keeps the root observation useful without exporting raw PII.
            langfuse_client.update_current_span(
                input={"message": safe_message, "feature": feature}
            )
            with langfuse_client.start_as_current_observation(
                as_type="retriever",
                name="retrieve-context",
                input={"query": safe_message},
            ) as retrieval:
                docs = retrieve(message)
                retrieval.update(
                    output={"documents": [summarize_text(doc) for doc in docs]},
                    metadata={"document_count": str(len(docs))},
                )

            prompt = resolve_prompt(
                langfuse_client,
                feature=feature,
                docs=docs,
                message=message,
                enabled=tracing_enabled(),
            )
            prompt_metadata = self._prompt_metadata(prompt, len(docs), safe_message)
            with langfuse_client.start_as_current_observation(
                as_type="generation",
                name="generate-response",
                input={"prompt": scrub_text(prompt.text)},
                model=self.model,
                metadata=prompt_metadata,
            ) as generation:
                response = self.llm.generate(prompt.text)
                cost_usd = self._estimate_cost(
                    response.usage.input_tokens, response.usage.output_tokens
                )
                generation.update(
                    output={"answer": summarize_text(response.text)},
                    usage_details={
                        "input": response.usage.input_tokens,
                        "output": response.usage.output_tokens,
                    },
                    cost_details={"total": cost_usd},
                    prompt=prompt.managed_prompt,
                )

            quality_score = self._heuristic_quality(message, response.text, docs)
            latency_ms = int((time.perf_counter() - started) * 1000)
            langfuse_client.update_current_span(
                output={"answer": summarize_text(response.text)},
                metadata={
                    **prompt_metadata,
                    "quality_score": str(quality_score),
                    "latency_ms": str(latency_ms),
                },
            )

        return AgentResult(
            answer=response.text,
            latency_ms=latency_ms,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            cost_usd=cost_usd,
            quality_score=quality_score,
        )

    def _run_with_legacy_trace_adapter(
        self,
        *,
        langfuse_client,
        trace_metadata: dict[str, str],
        trace_tags: list[str],
        user_id: str,
        feature: str,
        session_id: str,
        message: str,
        started: float,
    ) -> AgentResult:
        """Keep the old mock-client contract testable; production uses the v4 branch."""
        docs = retrieve(message)
        prompt = resolve_prompt(
            langfuse_client,
            feature=feature,
            docs=docs,
            message=message,
            enabled=tracing_enabled(),
        )
        response = self.llm.generate(prompt.text)
        quality_score = self._heuristic_quality(message, response.text, docs)
        latency_ms = int((time.perf_counter() - started) * 1000)
        cost_usd = self._estimate_cost(response.usage.input_tokens, response.usage.output_tokens)
        prompt_metadata = self._prompt_metadata(prompt, len(docs), summarize_text(message))

        langfuse_client.update_current_trace(
            user_id=hash_user_id(user_id),
            session_id=session_id,
            tags=trace_tags,
            metadata={
                "prompt_name": prompt.name,
                "prompt_label": prompt.label,
                "prompt_version": prompt.version,
                "prompt_source": prompt.source,
            },
        )
        langfuse_client.update_current_generation(
            model=self.model,
            metadata=prompt_metadata,
            usage_details={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
            },
            cost_details={"total": cost_usd},
            prompt=prompt.managed_prompt,
        )
        return AgentResult(
            answer=response.text,
            latency_ms=latency_ms,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            cost_usd=cost_usd,
            quality_score=quality_score,
        )

    @staticmethod
    def _prompt_metadata(prompt, doc_count: int, safe_message: str) -> dict[str, str]:
        return {
            "doc_count": str(doc_count),
            "query_preview": safe_message,
            "prompt_name": prompt.name,
            "prompt_label": prompt.label,
            "prompt_version": prompt.version,
            "prompt_source": prompt.source,
            "prompt_fetch_error": prompt.fetch_error or "none",
        }

    def _estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        input_cost = (tokens_in / 1_000_000) * 3
        output_cost = (tokens_out / 1_000_000) * 15
        return round(input_cost + output_cost, 6)

    def _heuristic_quality(self, question: str, answer: str, docs: list[str]) -> float:
        score = 0.5
        if docs:
            score += 0.2
        if len(answer) > 40:
            score += 0.1
        if question.lower().split()[0:1] and any(token in answer.lower() for token in question.lower().split()[:3]):
            score += 0.1
        if "[REDACTED" in answer:
            score -= 0.2
        return round(max(0.0, min(1.0, score)), 2)
