# Phân công nhóm — Day 13 Observability Lab

Nhóm 3 người, vai trò cố định:

- **Người 1** — Logging & PII
- **Người 2** — Tracing & Prompt Version
- **Người 3** — Dashboard, SLO & Alert **+** Incident, Report & Demo

Đã kiểm tra code thực tế trong repo để biết ai còn việc thật (`TODO`) và ai chỉ cần cấu hình/verify:

- **Logging & PII (Người 1)**: có 6 khối `TODO` thật cần code trong `app/middleware.py`, `app/main.py`, `app/logging_config.py`, `app/pii.py`. **[Đã hoàn thành — xem mục "Trạng thái" dưới đây]**
- **Tracing & Prompt Version (Người 2)**: `app/tracing.py`, `app/prompt_management.py`, `app/agent.py` **đã code sẵn đầy đủ** (không có TODO) — việc chính là cấu hình Langfuse (`.env`), tạo prompt `day13-chat` với các label trên Langfuse UI, và thu evidence.
- **Dashboard/SLO/Alert (Người 3, phần 1)**: `config/dashboard.yaml` và `scripts/validate_dashboard.py` đã hoàn chỉnh; còn `config/alert_rules.yaml` có 3 alert rỗng (`TODO_alert_1/2/3` — thiếu `name/severity/condition/owner`) và `config/slo.yaml` có 1 target cần thay (`latency_p95_ms.target`, dòng "Replace with your group's target").
- **Incident/Report/Demo (Người 3, phần 2)**: `app/incidents.py`, `app/challenge.py`, `scripts/inject_incident.py`, `scripts/load_test.py` đã hoàn chỉnh. `config/challenge.json` **đã được release cho cohort K3** (`challenge_id: day13-k3-observability-v1`, incident `rag_slow`, feature `refund`) — có thể chạy CP3 ngay, không cần chờ thêm. **Không tự sửa file này** (theo `RULES.md`).

## Bảng phân công theo Checkpoint

| Checkpoint | Người 1 — Logging & PII | Người 2 — Tracing & Prompt Version | Người 3 — Dashboard/SLO/Alert + Incident/Report |
|---|---|---|---|
| **CP0** (0:00–0:30)<br>Setup | Chạy theo `SETUP.md`: tạo venv, `pip install`, copy `.env`. Chạy `uvicorn` + `python scripts/load_test.py` để tạo `data/logs.jsonl` baseline, lưu kết quả `validate_logs.py` (baseline thấp là bình thường). | Lấy Langfuse key (project chung/cloud) từ Lab Coach, điền `LANGFUSE_PUBLIC_KEY/SECRET_KEY/HOST` vào `.env` chung của nhóm, xác nhận `/health` trả `tracing_enabled: true`. | Đọc trước `config/dashboard.yaml`, `config/slo.yaml`, `config/alert_rules.yaml`, `config/challenge.json` để biết contract; xác nhận `config/challenge.json` đã release cho K3. |
| **CP1** (0:30–1:30)<br>Logging & PII | **Việc code chính:**<br>1. `app/middleware.py`: clear contextvars, sinh/đọc `x-request-id` (`req-<8hex>`), `bind_contextvars(correlation_id=...)`, set response headers.<br>2. `app/main.py` (dòng ~47): `bind_contextvars(user_id_hash=hash_user_id(...), session_id=..., feature=..., model=..., env=...)` trước log `request_received`.<br>3. `app/logging_config.py`: bật `scrub_event` processor **trước** `JsonlFileProcessor()`.<br>4. `app/pii.py`: (tùy chọn) thêm pattern PII bổ sung.<br>Chạy `python scripts/validate_logs.py` đến khi ≥80/100. Lưu ảnh kết quả + log mẫu có/không PII vào `submission/evidence/`. | Trong lúc chờ Người 1 xong logging, tạo prompt `day13-chat` trên Langfuse UI: version 1 (label `baseline` + `production`), giữ 3 biến `{{feature}} {{docs}} {{message}}`. Soạn version 2 (label `candidate`, đổi nhỏ về format/độ dài). | Viết nội dung thật cho `config/alert_rules.yaml` (3 alert: name/severity/condition/owner, dùng threshold từ `dashboard.yaml`/`slo.yaml`) và chỉnh `latency_p95_ms.target` trong `config/slo.yaml`. Không cần chờ Người 1/2. |
| **CP2** (1:30–2:30)<br>Traces & Dashboard | Hỗ trợ: sau khi log đạt ≥80, chạy lại `load_test.py` nhiều lần để có ≥10 request đa dạng cho traces/dashboard dùng chung. Đối chiếu `data/logs.jsonl` không còn PII thô. | Chạy app với `LANGFUSE_PROMPT_LABEL=baseline` rồi `candidate`, mở ≥10 traces trên Langfuse, xác nhận metadata `prompt_name/prompt_label/prompt_version/prompt_source`. Đổi label `production` sang v2, chạy lại, rồi rollback về v1 — chụp ảnh trước/sau. Ghi 2 trace ID vào ghi chú chung. | Dùng `data/logs.jsonl` (đã sạch từ Người 1) build 6 panel (Latency/Traffic/Errors/Cost/Tokens/Quality) đúng mapping trong `docs/DASHBOARD_SETUP.md`. Chạy `python scripts/validate_dashboard.py` đến khi `6/6 panel`. Chụp ảnh dashboard có time range/đơn vị/threshold. |
| **CP3** (2:30–3:30)<br>Challenge chính thức | Đứng cạnh khi điều tra: dùng correlation ID để tra log tương ứng span/trace bất thường mà Người 3 tìm thấy. | Hỗ trợ mở trace của các request trong lúc incident để xem span nào phình to (RAG span nếu `rag_slow`). | **Chủ trì CP3:** chạy `python scripts/inject_incident.py` (không cần `--scenario`, sẽ tự đọc `config/challenge.json`) rồi `python scripts/load_test.py --challenge --concurrency 5`. Đọc metrics (`/metrics` hoặc dashboard) để xác định triệu chứng → mở trace lệch → tra log cùng correlation_id → viết root cause, fix, preventive measure. |
| **Hoàn tất** (3:30–4:00)<br>Report & Demo | Điền phần 3 (`Logging và tracing`) của `submission/REPORT.md`: evidence correlation ID, PII redaction. | Điền phần 4 (`Prompt versioning`): prompt name, version/label, trace ID, evidence rollback. | Điền phần 2, 5, 6 (`Kết quả kỹ thuật`, `Dashboard/SLO/alerts`, `Điều tra challenge`) + phần 1 (thông tin nhóm) và phần 7 (đóng góp cá nhân — ghép commit của cả 3). Chạy `python -m pytest -q` và `git status --short` trước khi push. |

## Điều phối chung (áp dụng cho cả 3 người)

- Dùng **1 file `.env` dùng chung** một cặp Langfuse key cho cả nhóm để traces của cả 3 người nằm trên cùng project — tránh mỗi người tạo project riêng.
- Mỗi người tự commit theo phần việc của mình (để `RUBRIC.md` phần B2 "commit khớp report cá nhân" có evidence rõ).
- Trước khi nộp: không commit `.env`, `.venv/`, log còn PII — kiểm bằng `git status --short` và review lại `data/logs.jsonl` mẫu.
- Nếu Người 1 xong CP1 sớm, có thể tạm rảnh tay hỗ trợ Người 3 viết `alert_rules.yaml`/`slo.yaml` (không có TODO code, chỉ là YAML) để rút ngắn thời gian tổng.

## Kiểm tra hoàn thành (chạy cuối buổi, cả nhóm)

```bash
python scripts/validate_logs.py       # ≥80/100 — Người 1 chịu trách nhiệm
python scripts/validate_dashboard.py  # 6/6 panel — Người 3 chịu trách nhiệm
python -m pytest -q                   # public tests — cả nhóm
git status --short                    # không lộ secret/PII
```

## Trạng thái

- [x] **CP1 — Logging & PII (Người 1)**: hoàn thành. `python scripts/validate_logs.py` → **100/100**, `python -m pytest -q` → 22/22 pass. Đã sửa `app/middleware.py`, `app/main.py`, `app/logging_config.py`, `app/pii.py`.
- [ ] **CP1 — Tracing & Prompt Version (Người 2)**: chưa bắt đầu.
- [x] **CP1 — Dashboard/SLO/Alert (Người 3)**: hoàn thành. Đã hoàn thiện SLO, 3 alert và runbook.
- [x] **CP2 — Dashboard (Người 3)**: hoàn thành. Dashboard runtime đọc `data/logs.jsonl`, đủ 6 panel; validator đạt 6/6; evidence ở `submission/evidence/dashboard-cp2.png`.
- [ ] **CP2 — Tracing (Người 2)**: chưa bắt đầu.
- [x] **CP3 — Incident (Người 3)**: đã chạy challenge `rag_slow`, thu metrics/log/dashboard evidence và cập nhật report. Trace/span evidence chờ Người 2 cấu hình Langfuse.
- [ ] **Report & Demo**: chưa hoàn tất.
