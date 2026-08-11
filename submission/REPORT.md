# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`:
- Tổng số traces:
- Số PII leak còn lại:
- Link/đường dẫn dashboard:

## 3. Logging và tracing

- Evidence correlation ID:
- Evidence PII redaction:
- Evidence trace waterfall:
- Giải thích một span đáng chú ý:

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
| ------------ | ----------- | --------- | ---------------- |
|              |             |           |                  |
