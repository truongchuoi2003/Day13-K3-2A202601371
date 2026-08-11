# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100 (0 lỗi required field, 0 lỗi enrichment, 10 correlation ID duy nhất, 0 PII leak) — xem `submission/evidence/validate_logs_result.png`.
- Tổng số traces: _(Người 2 điền)_
- Số PII leak còn lại: 0 — email, số điện thoại VN và số thẻ tín dụng test đều được redact trước khi ghi log (xem `submission/evidence/pii_redaction_proof.txt`).
- Link/đường dẫn dashboard: _(Người 3 điền)_

## 3. Logging và tracing

- Evidence correlation ID: `submission/evidence/correlation_id_sample.json` — hai log `request_received` và `response_sent` của cùng một request đều mang `correlation_id="req-0a135911"`, chứng minh `CorrelationIdMiddleware` sinh ID và giữ nguyên xuyên suốt vòng đời request qua `structlog` contextvars.
- Evidence PII redaction: `submission/evidence/pii_redaction_proof.txt` — request test gửi email `test@example.com`, SĐT `0912345678`, số thẻ `1234 5678 9012 3456`; log ghi lại `payload.message_preview` đã thay bằng `[REDACTED_EMAIL]`, `[REDACTED_PHONE_VN]`, `[REDACTED_CREDIT_CARD]`, không còn dữ liệu gốc nào lộ ra trong `data/logs.jsonl`.
- Evidence trace waterfall: _(Người 2 điền — phần Tracing & Prompt Version)_
- Giải thích một span đáng chú ý: _(Người 2 điền)_

## 4. Prompt versioning

- Prompt name:
- Version/label baseline:
- Version/label candidate:
- Trace ID của mỗi version:
- Bằng chứng đổi label hoặc rollback:

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`:
- Evidence dashboard:
- SLO đã chọn và lý do:
- Alert rules và runbook:

## 6. Điều tra challenge

- Challenge ID:
- Triệu chứng từ metrics:
- Trace ID liên quan:
- Log line/correlation ID liên quan:
- Root cause:
- Fix action:
- Preventive measure:

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Người 1 (Logging & PII) | Correlation ID middleware, enrich log context (`user_id_hash`, `session_id`, `feature`, `model`, `env`), bật PII scrubbing processor, thêm pattern PII | `60c47db` + commit evidence này _(điền SHA sau khi `git commit`)_ | Thứ tự processor trong `structlog` quyết định dữ liệu có được scrub trước khi ghi file hay không; dùng `contextvars` để lan truyền context xuyên middleware → handler → log mà không cần truyền tham số thủ công |
| Người 2 (Tracing & Prompt Version) | _(điền)_ | _(điền)_ | _(điền)_ |
| Người 3 (Dashboard/SLO/Alert + Incident/Report) | _(điền)_ | _(điền)_ | _(điền)_ |
