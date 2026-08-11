# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: API P95 latency vượt SLO
- Severity: critical
- SLI/SLO liên quan: `latency_p95_ms` — P95 không vượt 3000 ms trong 99.5% thời gian của cửa sổ 28 ngày.
- Điều kiện và thời gian duy trì: P95 latency > 3000 ms trong 5 phút liên tiếp.
- Ảnh hưởng tới người dùng: Người dùng nhận phản hồi chậm hoặc hết thời gian chờ.
- Ba bước kiểm tra đầu tiên: (1) xác nhận P95 và traffic trên dashboard trong cùng time range; (2) mở trace chậm để tìm span có thời gian bất thường; (3) tìm JSON log cùng `correlation_id` để xác nhận feature và lỗi liên quan.
- Mitigation tạm thời: Tắt hoặc giảm tải feature bị ảnh hưởng, sau đó rollback cấu hình/prompt gần nhất nếu trace cho thấy thay đổi đó liên quan.
- Owner: Dashboard, SLO & Alert

## Alert 2

- Tên: Tỷ lệ lỗi request vượt SLO
- Severity: critical
- SLI/SLO liên quan: `error_rate_pct` — không vượt 2% trong 99% thời gian của cửa sổ 28 ngày.
- Điều kiện và thời gian duy trì: Error rate > 2% trong 5 phút liên tiếp.
- Ảnh hưởng tới người dùng: Một phần request thất bại và không nhận được câu trả lời.
- Ba bước kiểm tra đầu tiên: (1) xem error-rate panel và breakdown `error_type`; (2) mở trace của một request lỗi; (3) tra log `request_failed` cùng `correlation_id`.
- Mitigation tạm thời: Tạm ngắt feature gây lỗi hoặc chuyển sang fallback an toàn; theo dõi error rate giảm trước khi khôi phục.
- Owner: Dashboard, SLO & Alert

## Alert 3

- Tên: Chi phí request vượt ngân sách ngày
- Severity: warning
- SLI/SLO liên quan: `daily_cost_usd` — tổng chi phí ngày không vượt 2.5 USD.
- Điều kiện và thời gian duy trì: Daily cost > 2.5 USD trong 15 phút liên tiếp.
- Ảnh hưởng tới người dùng: Ngân sách vận hành có nguy cơ vượt kế hoạch; chưa nhất thiết ảnh hưởng trực tiếp đến phản hồi.
- Ba bước kiểm tra đầu tiên: (1) xác nhận tổng cost và cost/phút trên dashboard; (2) kiểm tra tokens input/output của các request mới; (3) mở trace có cost/token cao để xác định feature hoặc model liên quan.
- Mitigation tạm thời: Giảm giới hạn token, chuyển sang model/response ngắn hơn hoặc tạm giới hạn feature phát sinh chi phí cao.
- Owner: Dashboard, SLO & Alert
