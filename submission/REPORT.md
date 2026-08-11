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
- Tổng số traces: ít nhất 10 — xem `submission/evidence/trace-list-10plus.png`.
- Số PII leak còn lại: 0 — email, số điện thoại VN và số thẻ tín dụng test đều được redact trước khi ghi log (xem `submission/evidence/pii_redaction_proof.txt`).
- Link/đường dẫn dashboard: `scripts/dashboard.py` — chạy `python scripts/dashboard.py`, sau đó mở `http://127.0.0.1:8501`.

## 3. Logging và tracing

- Evidence correlation ID: `submission/evidence/correlation_id_sample.json` — hai log `request_received` và `response_sent` của cùng một request đều mang `correlation_id="req-0a135911"`, chứng minh `CorrelationIdMiddleware` sinh ID và giữ nguyên xuyên suốt vòng đời request qua `structlog` contextvars.
- Evidence PII redaction: `submission/evidence/pii_redaction_proof.txt` — request test gửi email `test@example.com`, SĐT `0912345678`, số thẻ `1234 5678 9012 3456`; log ghi lại `payload.message_preview` đã thay bằng `[REDACTED_EMAIL]`, `[REDACTED_PHONE_VN]`, `[REDACTED_CREDIT_CARD]`, không còn dữ liệu gốc nào lộ ra trong `data/logs.jsonl`.
- Evidence trace waterfall: `submission/evidence/trace-waterfall-production-v1.png` — trace production version 1.
- Giải thích một span đáng chú ý: Waterfall thể hiện hierarchy agent → retriever → generation. Khi điều tra latency, so sánh thời lượng retrieval với generation để khoanh vùng bước gây chậm trước khi tra log cùng correlation ID.

## 4. Prompt versioning

- Prompt name: `day13-chat`
- Version/label baseline: version 1 — `baseline`
- Version/label candidate: version 2 — `candidate`
- Trace ID của mỗi version:
  - baseline v1: `64bf6bf32feae3b4154cf78cd09e31e4` (`req-8c81c61b`)
  - candidate v2: `6382009567025aef1fc2af0ba24858d9` (`req-c8df8bd0`)
  - production v2 trước rollback: `280a42d8fa2d996901758853d9f88435` (`req-5c061fad`)
  - production v1 sau rollback: `792a67173fd84ff3e643a1f6b684af8a` (`req-0eeab3db`)
- Bằng chứng đổi label hoặc rollback: Đã chuyển label `production` từ version 1 sang version 2, tạo trace xác nhận; sau đó rollback `production` về version 1 và trace `req-0eeab3db` xác nhận `prompt_name=day13-chat`, `prompt_label=production`, `prompt_version=1`. Evidence: `prompt-versions-rollback.png`, `trace-waterfall-production-v1.png`, `trace-metadata-production-v1.png`, `trace-list-10plus.png`.

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: HỢP LỆ: 6/6 panel có trong dashboard contract — xem `submission/evidence/validate_dashboard_result.txt`.
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
| Người 2 (Tracing & Prompt Version) | Cấu hình Langfuse v4.14.3; tạo prompt `day13-chat` v1/v2 với label baseline/candidate; instrument agent/retriever/generation; promote và rollback label `production`; lưu evidence. | `f0d8e16` | Metadata prompt liên kết trace với đúng version/label; hierarchy agent–retriever–generation hỗ trợ phân tích latency, token và cost theo từng bước. |
| Người 3 (Dashboard/SLO/Alert + Incident/Report) | Hoàn thiện SLO, 3 alert symptom-based và runbook; xây dashboard runtime 6 panel từ `data/logs.jsonl`; chạy validator, điều tra `rag_slow` và lưu evidence CP2/CP3. | `4668964` (dashboard); thay bằng SHA commit cuối sau khi commit các cập nhật CP3/report. | Đọc JSONL để tính percentile, traffic, error rate, cost, token và quality; thiết kế SLO/alert theo chỉ số người dùng quan sát được. |
