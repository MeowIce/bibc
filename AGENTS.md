# AGENTS.md - Bối cảnh Dự án & Quy định Vận hành Co-Pilot


## 1. Tổng quan Dự án & Luồng Hoạt động

- **Tên dự án**: BanInBlacklistedChannels (BIBC) v2.0
- **Tác giả**: MeowIce
- **Mục đích**: Bot Discord chuyên dụng đóng vai trò bẫy lọc spam (honeypot). Tự động phát hiện tin nhắn gửi vào kênh chỉ định được cấu hình persistent per-guild trong SQLite, xử lý người dùng vi phạm theo chính sách và xuất báo cáo giám sát.
- **Cấu trúc tệp tin & Kiến trúc**:
  - `bot.py`: Lớp `BibcBot` khởi chạy chính, quản lý vòng đời ứng dụng, khởi tạo database và đồng bộ command tree.
  - `config.py`: Tải cấu hình an toàn từ biến môi trường qua `python-dotenv` (`DISCORD_TOKEN`, `DATABASE_PATH`).
  - `database.py`: Quản lý kết nối SQLite và schema bảng `guild_configs`, `ban_records`.
  - `messageWatcher.py`: Pipeline lọc và điều phối sự kiện tin nhắn với cache chống lặp bounded.
  - `cogs/`: Slash command cogs gồm `cogs/config.py` (`/config`) và `cogs/status.py` (`/status`).
  - `models/`: Định nghĩa các cấu trúc dữ liệu (`GuildConfig`, `BanRecord`).
  - `repositories/`: Tầng truy xuất cơ sở dữ liệu (`GuildConfigRepository`, `BanRepository`).
  - `services/`: Tầng xử lý nghiệp vụ (`GuildConfigService`, `BanService`, `ReportService`, `StatisticsService`).
  - `utils/`: Các hàm tiện ích định dạng log và tính toán mốc thời gian UTC (`logging.py`, `time.py`).
  - `docs/`: Chứa tài liệu hướng dẫn triển khai (`production.md`) và đặc tả thiết kế refactor.
  - `tests/`: Bộ kiểm thử tự động toàn diện (unit tests, integration tests, lifecycle tests).
  - `requirements.txt`: Danh sách thư viện phụ thuộc (`discord.py`, `py-cord`, `python-dotenv`, `pytest`, `pytest-asyncio`).
- **Cơ chế vận hành chính**:
  - **Giám sát tin nhắn (`MessageWatcher`)**: Lọc bỏ bot, DM, guild chưa cấu hình hoặc kênh không khớp watch channel.
  - **Chế độ `enforced`**: Ban thành viên vi phạm (`delete_message_seconds=300`, lý do cấu hình sẵn), lưu bản ghi `banned` vào SQLite.
  - **Chế độ `permissive`**: Lưu bản ghi `detected` vào SQLite, không ban thành viên.
  - **Báo cáo sự kiện (`ReportService`)**: Gửi thông báo chi tiết dạng Embed tới kênh báo cáo của guild (hoạt động độc lập, không ảnh hưởng kết quả ban).
- **Hệ thống lệnh Slash Commands**:
  - `/config watchchannel <channel>`: Cấu hình kênh bẫy spam cho server (yêu cầu quyền Administrator).
  - `/config reportchannel <channel>`: Cấu hình kênh nhận log Embed sự kiện cho server (yêu cầu quyền Administrator).
  - `/config policy <enforced|permissive>`: Thiết lập chính sách thực thi cho server (yêu cầu quyền Administrator).
  - `/status`: Hiển thị thông tin bot, uptime, chính sách server hiện tại và thống kê số lượng đã xử lý (Tổng / Tháng / Tuần).

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
