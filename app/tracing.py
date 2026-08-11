from __future__ import annotations

import os
from typing import Any

# Langfuse v4 uses LANGFUSE_BASE_URL. Keep the lab's existing LANGFUSE_HOST
# configuration working while the shared environment is migrated.
if not os.getenv("LANGFUSE_BASE_URL") and os.getenv("LANGFUSE_HOST"):
    os.environ["LANGFUSE_BASE_URL"] = os.environ["LANGFUSE_HOST"]

try:
    from langfuse import get_client, observe, propagate_attributes

    LANGFUSE_SDK_AVAILABLE = True
except ImportError:  # pragma: no cover - chỉ dùng khi chưa cài requirements
    LANGFUSE_SDK_AVAILABLE = False

    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            return func

        return decorator

    class _NoopAttributes:
        def __enter__(self):
            return self

        def __exit__(self, *args: Any) -> None:
            return None

    def propagate_attributes(**kwargs: Any) -> _NoopAttributes:
        return _NoopAttributes()

    class _DummyClient:
        def update_current_trace(self, **kwargs: Any) -> None:
            return None

        def update_current_generation(self, **kwargs: Any) -> None:
            return None

        def flush(self) -> None:
            return None

    def get_client():
        return _DummyClient()


def get_langfuse_client():
    return get_client()


def tracing_enabled() -> bool:
    return LANGFUSE_SDK_AVAILABLE and bool(
        os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")
    )


def flush_traces() -> None:
    """Flush buffered spans during a graceful application shutdown."""
    if tracing_enabled():
        get_langfuse_client().flush()
