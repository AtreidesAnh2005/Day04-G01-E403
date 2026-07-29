# Product Requirements Document (PRD) — Research Agent Tool Eval

## 1. Problem Statement (Vấn đề & Mục tiêu)

### Vấn đề
Khi xây dựng các ứng dụng AI Agent (đặc biệt là Research Agent phục vụ tìm kiếm, cào dữ liệu và tổng hợp thông tin), thách thức lớn nhất không chỉ nằm ở việc LLM "trả lời hay", mà ở khả năng **định tuyến công cụ (Tool Routing)** và **truyền tham số (Argument Passing)** chính xác. 

Nếu không được thiết kế và kiểm thử bài bản, Agent sẽ gặp phải các lỗi nghiêm trọng:
- Gọi sai công cụ (wrong tool).
- Truyền sai tham số hoặc sai kiểu dữ liệu (wrong argument value).
- Gọi công cụ thừa không cần thiết (unnecessary tool).
- Bỏ qua bước hỏi lại khi thiếu thông tin quan trọng (missing information / clarify).
- Tự ý thực hiện các hành động nhạy cảm mà không có sự xác nhận của người dùng (wrong boundary).

### Mục tiêu dự án
Xây dựng một **Research Agent** chạy thực tế có khả năng:
1. Tự động nhận yêu cầu nghiên cứu từ người dùng, lập kế hoạch, chọn và thực thi các công cụ tra cứu thực tế (`lookup`, `fetch`, `timeline`, `social_search`...).
2. Vận hành một quy trình **đánh giá dựa trên bằng chứng dữ liệu (Evidence-Driven Evaluation)**: Đo lường độ chính xác thông qua bộ kiểm thử tự động, đọc nhật ký lỗi (`run JSON`), từ đó liên tục tối ưu hóa **System Prompt** và **Tool Declarations** qua các phiên bản (`v0` $\rightarrow$ `v1` $\rightarrow$ `v2` $\rightarrow$ `v3`).

---

## 2. Core Features (Tính năng MVP cốt lõi)

### 2.1. Research Agent Core Loop
- **Multi-turn Agent Loop:** Khả năng nhận request, suy luận, chọn tool, truyền arguments, nhận kết quả từ tool và đưa ra phản hồi tổng hợp hoặc tiếp tục gọi tool tiếp theo.
- **Interactive Disambiguation (`clarify`):** Tự động phát hiện khi yêu cầu của người dùng bị thiếu thông tin cốt lõi hoặc chứa hành động nhạy cảm để dừng lại hỏi/xác nhận với người dùng trước khi tiếp tục.

### 2.2. Toolset (Hệ thống Công cụ)
- **Built-in Core Tools:**
  - `lookup`: Tìm kiếm thông tin trên Web dựa trên từ khóa (tích hợp Tavily API).
  - `fetch`: Cào và trích xuất nội dung văn bản chi tiết từ một URL (tích hợp Firecrawl API).
  - `timeline`: Lấy các bài đăng gần nhất từ một tài khoản mạng xã hội Twitter (tích hợp RapidAPI).
  - `social_search`: Tìm kiếm bài đăng trên mạng xã hội Twitter theo từ khóa (tích hợp RapidAPI).
  - `clarify`: Đặt câu hỏi clarification hoặc xác nhận Yes/No với người dùng.
  - `format`: Định dạng danh sách kết quả nghiên cứu thành bản tóm tắt Markdown chuyên nghiệp.
- **Custom Team Tool (Bắt buộc):** Ít nhất **1 tool mới** do nhóm tự phát triển, có mã nguồn Python, tài liệu mô tả `TOOL.md` và được khai báo đầy đủ trong registry và schema YAML.

### 2.3. Automated Evaluation Pipeline (`run_eval.py`)
- **Fixed Base Suite (`eval_base.json`):** Bộ test case chuẩn để đo lường benchmark ban đầu (`v0`).
- **Group Eval Suite (`eval_group.json`):** Bộ 10 test case tự thiết kế của nhóm (5 single-turn + 5 multi-turn) phủ các dạng lỗi quan trọng.
- **Metric Tracking:** Tính toán tự động các chỉ số:
  - `case_accuracy` (Tỷ lệ pass tổng thể).
  - `tool_routing_accuracy` (Tỷ lệ chọn đúng tool).
  - `argument_accuracy` (Tỷ lệ truyền đúng tham số).
  - `multiturn_accuracy` (Tỷ lệ xử lý đúng luồng nhiều lượt).
- **Run Audit Logging:** Lưu toàn bộ nhật ký thực thi vào các file JSON chuẩn hóa trong `runs/` kèm hash chứng thực của Prompt và Tools.

### 2.4. Evidence-Driven Versioning System
- Lưu vết toàn bộ lịch sử cải tiến trong `artifacts/version_log.csv` từ `v0` đến `v3`.
- Mỗi phiên bản ghi rõ: Tác giả, file thay đổi (`system_prompt.md` hoặc `tools.yaml`), giả thuyết cải tiến (hypothesis), điểm số trước/sau và file log kiểm chứng.

### 2.5. User Interface (UI - Streamlit)
- **Giao diện tương tác người dùng (`app.py`):**
  - Màn hình trò chuyện trực quan (Chat Interface).
  - Hiển thị công khai **Tool Trace**: Tên tool được gọi, tham số đầu vào, trạng thái/vòng gọi, và kết quả/lỗi chi tiết của từng bước.
  - Hiển thị rõ **Version / Artifact Hash** đang chạy.
- **Public Deployment:** Tích hợp công cụ tạo đường dẫn public tạm thời (ví dụ: Cloudflare Tunnel) để các nhóm khác có thể truy cập và trải nghiệm trực tiếp từ xa.

---

## 3. Out of Scope (Phạm vi ngoài v1)

Các tính năng **KHÔNG** nằm trong phạm vi phiên bản v1 này:
1. **Multi-agent Orchestration phức tạp:** Không xây dựng hệ thống nhiều agent tự trao đổi với nhau theo dạng hội đồng (consensus/voting).
2. **Auto-execution đối với hành động phá hủy:** Không tự động gửi email/tin nhắn thật hoặc thay đổi dữ liệu mà không có xác nhận Yes/No rõ ràng.
3. **Cào dữ liệu ngầm tự động (Background Crawler):** Không xây dựng hệ thống cào web tự động liên tục theo thời gian định sẵn.

---

## 4. Main User Flow (Luồng người dùng chính)

### Luồng 1: Người dùng tương tác qua Web UI (`app.py`)
1. **Khởi động:** Người dùng truy cập URL ứng dụng (Localhost hoặc Tunnel URL).
2. **Nhập yêu cầu:** Người dùng gửi câu hỏi/yêu cầu nghiên cứu (ví dụ: *"Tìm 3 bài đăng mới nhất của sama trên Twitter và tóm tắt nội dung chính"*).
3. **Agent Suy luận & Gọi Tool:**
   - Agent phân tích yêu cầu dựa trên `system_prompt.md` và `tools.yaml`.
   - Giao diện UI hiển thị thẻ **Tool Execution Trace** (ví dụ: đang gọi tool `timeline` với `screenname='sama'`, `limit=3`).
4. **Xử lý thiếu thông tin / Xác nhận (nếu có):**
   - Nếu câu hỏi mơ hồ, Agent gọi tool `clarify` và giao diện đưa ra câu hỏi làm rõ cho người dùng.
5. **Tổng hợp & Trả lời:** Agent gọi tool `format` và trả lời đáp án hoàn chỉnh cho người dùng dưới dạng Markdown.

### Luồng 2: Quy trình Đánh giá & Tối ưu cho Lập trình viên (Developer Iteration Flow)
1. **Chạy Baseline (`v0`):** Chạy `python run_eval.py --provider openai --version v0 ...` thu được file `runs/v0_...json`.
2. **Phân tích lỗi:** Mở file log JSON, soi các case bị ngắt hoặc chọn sai tool (`observed_mismatch`).
3. **Đưa ra Giả thuyết & Chỉnh sửa:** Sửa file Prompt hoặc Schema mô tả Tool.
4. **Đánh giá lại (`v1`, `v2`, `v3`):** Chạy lại eval suite, ghi nhận điểm số vào `version_log.csv` và hoàn thiện Báo cáo `REPORT.md`.
