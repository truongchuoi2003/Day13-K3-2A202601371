# Evidence CP3 — rag_slow

- Challenge ID: `day13-k3-observability-v1`
- Incident: `rag_slow`
- Feature bị ảnh hưởng: `refund`
- Ngưỡng challenge: 2000 ms

## Metrics

| Thời điểm | Traffic | P95 latency | Error rate | Total cost |
|---|---:|---:|---:|---:|
| Baseline | 20 | 152 ms | 0% | 0.0422 USD |
| Sau khi bật `rag_slow` và chạy 5 query challenge | 25 | 2651 ms | 0% | 0.0521 USD |

P95 tăng 2499 ms và vượt ngưỡng challenge 2000 ms. Ảnh dashboard: `dashboard-cp3-rag-slow.png`.

## Log evidence

Một response của challenge:

```json
{"ts":"2026-08-11T04:44:32.267229Z","event":"response_sent","correlation_id":"req-714b71a1","session_id":"k3-challenge-s01","feature":"refund","latency_ms":2651,"tokens_in":29,"tokens_out":154,"cost_usd":0.002397,"quality_score":0.9}
```

Bốn request refund khác có latency lần lượt 2650, 2650, 2651 và 2650 ms, cùng xác nhận triệu chứng không phải một outlier đơn lẻ.

## Trace evidence

Không có trace ID trong lần chạy này vì `/health` trả `tracing_enabled: false`: biến `LANGFUSE_PUBLIC_KEY` và `LANGFUSE_SECRET_KEY` chưa được cấu hình. Không tạo hay ghi giả trace ID. Người 2 cần cấu hình Langfuse, chạy lại challenge và bổ sung trace/span thật.
