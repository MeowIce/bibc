# AGENTS.md - Bối cảnh Dự án & Quy định Vận hành Co-Pilot


## 1. Tổng quan Dự án & Luồng Hoạt động

- **Tên dự án**: BanInBlacklistedChannels (BIBC) v2.0
- **Tác giả**: MeowIce
- **Mục đích**: Bot Discord chuyên dụng đóng vai trò bẫy lọc spam (honeypot). Tự động phát hiện tin nhắn gửi vào các kênh chỉ định nằm trong danh sách đen (`ChID`), xử lý người dùng vi phạm và báo cáo về kênh giám sát (`reportChID`).
- **Cấu trúc tệp tin**:
  - `bot.py`: Mã nguồn chính chạy trên môi trường production. Sử dụng slash commands (`discord.app_commands`) và event `on_message` để phát hiện vi phạm, quản lý trạng thái thực thi per-guild.
  - `opensrc.py`: Phiên bản mã nguồn mở hóa của `bot.py`, ẩn token nhạy cảm và thay thế ID cấu hình bằng dữ liệu mẫu.
  - `testbot.py`: Bản thử nghiệm tiền thân dùng tiền tố lệnh `!` (`commands.Bot`) và cờ `isDebugMode` để kiểm tra logic ban và uptime.
  - `requirements.txt`: Danh sách thư viện phụ thuộc (`discord.py`, `py-cord`).
- **Cơ chế vận hành chính**:
  - **Giám sát tin nhắn (`on_message`)**: Khi phát hiện tin nhắn trong kênh thuộc danh sách đen `ChID`, kiểm tra chế độ chính sách của server.
  - **Chế độ `Enforced`**: Thực thi ban thành viên vi phạm (`delete_message_seconds=300`, lý do cấu hình sẵn), lưu thông tin vào danh sách `bannedUsers` trong bộ nhớ runtime.
  - **Chế độ `LogOnly`**: Chỉ ghi nhận log ra console, không thực hiện hành động cấm.
  - **Báo cáo sự kiện**: Gửi thông báo chi tiết dạng Embed tới các kênh cấu hình trong `reportChID`.
- **Hệ thống lệnh Slash Commands**:
  - `/epedit`: Bật/tắt chính sách thực thi giữa `LogOnly` và `Enforced` (yêu cầu quyền Administrator).
  - `/getpolicy`: Truy vấn chính sách hiện tại của guild.
  - `/getban`: Xem danh sách tài khoản đã bị bot xử lý trong phiên chạy.
  - `/info`: Hiển thị thông tin bot, thời gian hoạt động (uptime), chính sách hiện tại và số lượng tài khoản đã xử lý.

---

## 2. Quy chuẩn Lập trình Dự án

- **Quy tắc đặt tên**: Sử dụng duy nhất kiểu camelCase cho tất cả tên biến và tên hàm (ngoại trừ các hàm hook/event bắt buộc của framework như `on_ready`, `setup_hook`).
- **Ghi chú trong mã nguồn**: Tuyệt đối không để lại ghi chú (comment) bên trong khối mã nguồn. Tất cả mã nguồn phải hoàn toàn sạch ghi chú, trừ khi được yêu cầu rõ ràng.
- **Không sử dụng emoji**: Tuyệt đối không được sử dụng emoji trong mã nguồn hoặc log xuất bản, trừ khi được yêu cầu rõ ràng.
- **Triết lý thiết kế (Ponytail & Minimal)**:
  - Tận dụng tối đa thư viện chuẩn (stdlib) và tính năng có sẵn của nền tảng trước khi thêm code hoặc thư viện ngoài.
  - Không tạo abstraction dư thừa (interface 1 implementation, helper 1 lần dùng).
  - Khắc phục lỗi tại gốc rễ (root cause) thay vì vá triệu chứng bề mặt.
  - Diff ngắn nhất, hiệu quả nhất, đảm bảo tính đúng đắn trên edge cases.

---

## 3. Nguyên tắc và Ràng buộc Vận hành Co-Pilot

- **Ngôn ngữ phản hồi**: Phản hồi theo đúng ngôn ngữ của câu hỏi (Tiếng Anh hoặc Tiếng Việt).
- **Xử lý thông tin mơ hồ**: Nếu các yêu cầu hoặc thông số kỹ thuật chưa rõ ràng, phải yêu cầu làm rõ trước khi thực thi.
- **Phong cách thực thi**: Đưa ra nhiều góc nhìn hoặc giải pháp cho các vấn đề kỹ thuật phức tạp. Giữ kết quả trực tiếp, không chứa các thành phần giao tiếp thừa, dấu gạch ngang dài, biểu tượng cảm xúc hoặc lời chào kết thúc.
- **Phong cách giao tiếp (Caveman)**: Giữ văn phong súc tích, ngắn gọn, đi thẳng vào trọng tâm kỹ thuật.

---

## 4. Quy định Thông báo Webhook

- Mỗi khi hoàn thành xong bất kỳ tác vụ hoặc công việc nào, phải chủ động gọi script `c:\Users\MeowIce\Documents\MeowBots\Webhooks\Webhook_Gemini.py` để gửi thông báo Discord webhook cho người dùng.
- **LƯU Ý**: Script `Webhook_Gemini.py` đã tự động chèn `<@666824403216105483> Workspace [tên ws]` ở đầu tin nhắn. Khi truyền tham số nội dung vào script, **chỉ truyền phần [nội dung output tóm tắt công việc đã xong]**, KHÔNG truyền lặp lại tag user hay `Workspace ...`.
- Lệnh mẫu thực thi qua PowerShell (`powershell.exe`):
  `$OutputEncoding = [System.Text.Encoding]::UTF8; [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; $env:WORKSPACE_NAME="MACB"; C:\Python314\python.exe c:\Users\MeowIce\Documents\MeowBots\Webhooks\Webhook_Gemini.py "[nội dung output]"`
