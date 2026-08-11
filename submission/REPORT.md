# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: PRAI
- Repository URL: https://github.com/truongchuoi2003/Day13-K3-Observability.git
- Commit SHA cuối: `5693c77ebefdd8ace1b8d79cb35994febc8b36e1` _(cập nhật lại sau commit cuối trước khi push)_
- Thành viên và vai trò:
  - Quách Xuân Trường — Trưởng nhóm
  - Ngô Thị Hằng — Thành viên
  - Nguyễn Huy Hoàng — Thành viên
  - Phân công kỹ thuật: Người 1 — Logging & PII; Người 2 — Tracing & Prompt Version; Người 3 — Dashboard, SLO & Alert + Incident, Report & Demo. Cần đối chiếu tên với ba vai trò này trước khi nộp.

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100 (52 log records; 0 lỗi required field; 0 lỗi enrichment; 27 correlation ID duy nhất; 0 PII leak) — xem `submission/evidence/validate_logs_result.txt`.
- Tổng số traces: 0 — Langfuse chưa được cấu hình trong môi trường kiểm tra (`tracing_enabled: false`).
- Số PII leak còn lại: 0 — email, số điện thoại VN và số thẻ tín dụng test đều được redact trước khi ghi log (xem `submission/evidence/pii_redaction_proof.txt`).
- Link/đường dẫn dashboard: `scripts/dashboard.py` — chạy `python scripts/dashboard.py`, sau đó mở `http://127.0.0.1:8501`.

## 3. Logging và tracing

- Evidence correlation ID: `submission/evidence/correlation_id_sample.json` — hai log `request_received` và `response_sent` của cùng một request đều mang `correlation_id="req-0a135911"`, chứng minh `CorrelationIdMiddleware` sinh ID và giữ nguyên xuyên suốt vòng đời request qua `structlog` contextvars.
- Evidence PII redaction: `submission/evidence/pii_redaction_proof.txt` — request test gửi email `test@example.com`, SĐT `0912345678`, số thẻ `1234 5678 9012 3456`; log ghi lại `payload.message_preview` đã thay bằng `[REDACTED_EMAIL]`, `[REDACTED_PHONE_VN]`, `[REDACTED_CREDIT_CARD]`, không còn dữ liệu gốc nào lộ ra trong `data/logs.jsonl`.
- Evidence trace waterfall: Chưa có. Cần cấu hình `LANGFUSE_PUBLIC_KEY` và `LANGFUSE_SECRET_KEY`, tạo trace thật rồi lưu ảnh waterfall vào `submission/evidence/`.
- Giải thích một span đáng chú ý: Chưa có trace/span thật để phân tích. Trong incident `rag_slow`, span cần kiểm tra sau khi bật Langfuse là retrieval/RAG, vì metric và log cho thấy độ trễ tăng khoảng 2.5 giây.

## 4. Prompt versioning

- Prompt name: `day13-chat` (contract; chưa tạo managed prompt trên Langfuse).
- Version/label baseline: Chưa có — cần tạo version 1 với labels `baseline` và `production`.
- Version/label candidate: Chưa có — cần tạo version 2 với label `candidate`.
- Trace ID của mỗi version: Chưa có vì tracing chưa được bật.
- Bằng chứng đổi label hoặc rollback: Chưa có. Người 2 cần chuyển `production` sang version 2, chạy request, rollback về version 1 và lưu ảnh evidence.

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: HỢP LỆ: 6/6 panel có trong dashboard contract.
- Evidence dashboard: `submission/evidence/dashboard-cp2.png` — dashboard đọc trực tiếp `data/logs.jsonl`, có time range 60 phút, auto refresh 30 giây, đơn vị và threshold cho đủ 6 panel.
- SLO đã chọn và lý do: latency P95 ≤ 3000 ms (target 99.5% trong cửa sổ 28 ngày), error rate ≤ 2% (99%), daily cost ≤ 2.5 USD (100%), quality score average ≥ 0.75 (95%). Bốn SLO này lần lượt bảo vệ trải nghiệm phản hồi, độ tin cậy, ngân sách và quality proxy của hệ thống AI.
- Alert rules và runbook: `API P95 latency vượt SLO` (critical, P95 > 3000 ms trong 5 phút); `Tỷ lệ lỗi request vượt SLO` (critical, error rate > 2% trong 5 phút); `Chi phí request vượt ngân sách ngày` (warning, daily cost > 2.5 USD trong 15 phút). Cấu hình ở `config/alert_rules.yaml`, runbook tương ứng ở `docs/alerts.md`.

## 6. Điều tra challenge

- Challenge ID: `day13-k3-observability-v1` — incident `rag_slow`, feature bị ảnh hưởng `refund`, ngưỡng challenge 2000 ms.
- Triệu chứng từ metrics: trước incident, traffic 20 và P95 latency 152 ms. Sau khi bật incident và chạy 5 query challenge, traffic là 25, P95 là 2651 ms (tăng 2499 ms và vượt ngưỡng challenge 2000 ms), error rate vẫn 0%. Evidence: `submission/evidence/dashboard-cp3-rag-slow.png` và `submission/evidence/incident-cp3.md`.
- Trace ID liên quan: Chưa có trace ID thật vì `/health` xác nhận `tracing_enabled: false` (chưa cấu hình Langfuse key). Không dùng trace giả; Người 2 cần bật Langfuse và chạy lại challenge để bổ sung trace/span RAG.
- Log line/correlation ID liên quan: `req-714b71a1` / session `k3-challenge-s01` / feature `refund` có event `response_sent`, `latency_ms=2651`; xem `submission/evidence/incident-cp3.md`. Bốn request challenge còn lại cũng có latency 2650–2651 ms.
- Root cause: Incident `rag_slow` được bật; hàm `retrieve()` trong `app/mock_rag.py` chèn `time.sleep(2.5)` trước retrieval. Dấu hiệu này phù hợp với P95 2651 ms và năm log refund có latency khoảng 2650 ms.
- Fix action: Loại bỏ độ trễ nhân tạo; trong hệ thống thật, tối ưu/truy vết truy vấn retrieval, đặt timeout và fallback cho vector store trước khi trả lời người dùng.
- Preventive measure: Theo dõi latency span retrieval trên Langfuse khi đã bật tracing; thêm alert/symptom threshold 2000 ms cho feature `refund` hoặc điều chỉnh SLO/alert latency sau khi thống nhất với owner. Threshold dashboard hiện là 3000 ms nên không báo alert cho incident này dù challenge đã vượt 2000 ms.

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên                                      | Phần việc                                                                                                                                                        | Commit/PR                                                                  | Điều đã học                                                                                                                                                                                                                                |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Người 1 (Logging & PII) | Correlation ID middleware, enrich log context (`user_id_hash`, `session_id`, `feature`, `model`, `env`), bật PII scrubbing processor, thêm pattern PII và evidence CP1 | `60c47db`, `c2121c3` | Thứ tự processor trong `structlog` quyết định dữ liệu có được scrub trước khi ghi file hay không; `contextvars` lan truyền context xuyên middleware → handler → log mà không cần truyền tham số thủ công. |
| Người 2 (Tracing & Prompt Version) | Chưa hoàn thành: Langfuse chưa cấu hình, chưa có managed prompt v1/v2, trace, label switch hoặc rollback evidence. | Chưa có commit/evidence cho phần này. | Cần cấu hình Langfuse, sau đó kiểm tra metadata `prompt_name`, `prompt_label`, `prompt_version` trên trace thật. |
| Người 3 (Dashboard/SLO/Alert + Incident/Report) | Hoàn thiện SLO, 3 alert symptom-based và runbook; xây dashboard runtime 6 panel từ `data/logs.jsonl`; chạy validator, điều tra `rag_slow` và lưu evidence CP2/CP3. | `4668964` (dashboard); thay bằng SHA commit cuối sau khi commit các cập nhật CP3/report. | Đọc JSONL để tính percentile, traffic, error rate, cost, token và quality; thiết kế SLO/alert theo chỉ số người dùng quan sát được. |
