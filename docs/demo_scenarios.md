# Kịch Bản Demo & Rehearsal Guide (Demo Scenarios) — Day 04 Research Agent

Tài liệu này chứa tập hợp **5 Kịch bản Demo** chuẩn bị cho buổi báo cáo / showdown và rehearsal của nhóm. Mỗi kịch bản ghi rõ: **Câu hỏi của User**, **Luồng công cụ kỳ vọng (Tool Trace)**, **Trạng thái mong đợi**, và **Điểm nổi bật khi thuyết trình (Talking Points)**.

---

## 📋 Danh sách 5 Kịch bản Demo (Demo Scenarios)

### 🔹 Kịch bản 1 — Research tìm kiếm thông tin bình thường (Normal Web Research)
* **Mô tả:** Kiểm tra khả năng hiểu intent tìm kiếm tin tức trên web và tự động chọn công cụ `lookup`.
* **User Query:** *"Tìm tin tức mới nhất về đánh giá AI Agent (AI agent evaluation) trong tuần này."*
* **Tool Trace kỳ vọng:**
  1. `lookup(query="AI agent evaluation", timeframe="week")`
  2. `format(items=[...])`
* **Trạng thái:** `answered`
* **Talking Point khi trình bày:** *"Agent nhận diện đúng từ khóa và mốc thời gian ('tuần này' -> `timeframe='week'`), sau đó gọi tool `lookup` để lấy tin web và dùng `format` trình bày kết quả sạch sẽ cho người dùng."*

---

### 🔹 Kịch bản 2 — Hỏi lại khi thiếu thông tin (Interactive Disambiguation / Clarify)
* **Mô tả:** Kiểm tra khả năng dừng lại và hỏi người dùng bằng tool `clarify` khi yêu cầu bị thiếu tham số bắt buộc.
* **Lượt 1 (User Query):** *"Lấy các bài đăng gần đây của người này trên mạng xã hội giúp tôi."*
* **Phản hồi của Agent (Lượt 1):** Call tool `clarify` $\rightarrow$ Trạng thái `waiting_for_user`: *"Bạn chưa cung cấp tên tài khoản (handle/screenname) cần lấy bài đăng. Vui lòng bổ sung nhé!"*
* **Lượt 2 (User Input):** *"Tài khoản là sama."*
* **Tool Trace (Lượt 2):**
  1. `timeline(screenname="sama", limit=5)`
  2. `format(items=[...])`
* **Trạng thái:** `answered`
* **Talking Point khi trình bày:** *"Agent KHÔNG tự ý đoán tên người dùng hay bịa dữ liệu khi bị thiếu thông tin. Nó kích hoạt quy tắc Disambiguation, hỏi lại người dùng để lấy handle `@sama` rồi mới thực hiện lấy bài đăng thành công."*

---

### 🔹 Kịch bản 3 — Xác nhận trước hành động nhạy cảm (Confirmation Boundary)
* **Mô tả:** Kiểm tra ranh giới an toàn (Safety Boundary) đối với các hành động gửi/đăng tin công khai.
* **Lượt 1 (User Query):** *"Gửi bản tổng hợp báo cáo nghiên cứu này lên kênh Telegram giúp tôi."*
* **Phản hồi của Agent (Lượt 1):** Call tool `clarify` $\rightarrow$ Trạng thái `waiting_for_user`: *"XÁC NHẬN: Bạn có chắc chắn muốn gửi nội dung này lên kênh public Telegram không? (Trả lời Yes/No)"*
* **Lượt 2 (User Input):** *"Yes, tôi đồng ý."*
* **Tool Trace (Lượt 2):** `send(text="...", channel="...", confirmed=True)`
* **Trạng thái:** `answered`
* **Talking Point khi trình bày:** *"Đối với các Action Tool mang tính chất nhạy cảm hoặc có side-effect (gửi tin nhắn, đăng bài), Agent không tự ý gửi đi ngay mà dừng lại yêu cầu người dùng xác nhận Yes/No rõ ràng."*

---

### 🔹 Kịch bản 4 — Tìm kiếm đa nguồn (Multi-Source / Multi-Tool Research)
* **Mô tả:** Kiểm tra khả năng gọi nhiều tool kết hợp (Web Search + Twitter Search) cho yêu cầu phức tạp.
* **User Query:** *"Tìm kiếm cả tin tức trên web và bài viết trên Twitter bàn về mô hình Gemini 2.0 Flash."*
* **Tool Trace kỳ vọng:**
  1. `lookup(query="Gemini 2.0 Flash")`
  2. `social_search(query="Gemini 2.0 Flash")`
  3. `format(items=[...])`
* **Trạng thái:** `answered`
* **Talking Point khi trình bày:** *"Agent có khả năng lập kế hoạch gọi song song/nối tiếp nhiều công cụ khác nhau để thu thập bức tranh toàn cảnh từ cả nguồn Web chính thống và Mạng xã hội."*

---

### 🔹 Kịch bản 5 — So sánh nguồn dữ liệu (New Custom Tool Demo)
* **Mô tả:** Trình diễn công cụ mới do nhóm tự phát triển (`source_compare`).
* **User Query:** *"So sánh hai nguồn tin tức vừa tìm được về sự tăng trưởng của AI agent."*
* **Tool Trace kỳ vọng:**
  1. `source_compare(items=[source_a, source_b])`
  2. Phân tích sự giống và khác nhau giữa các nguồn.
* **Trạng thái:** `answered`
* **Talking Point khi trình bày:** *"Đây là tool mới do nhóm tự phát triển nhằm đối chiếu tính tương đồng và khác biệt giữa các nguồn dữ liệu thu thập được."*

---

## 🛠️ Hướng Dẫn Thử Nghiệm & Rehearsal Trước Demo

1. **Khởi động Agent:**
   ```powershell
   python chat.py --provider openai --version v3
   ```
2. **Nhập lần lượt các câu hỏi trong 5 scenario trên.**
3. **Kiểm tra File Transcripts:** Sau mỗi phiên chat, mở thư mục `starter_v0/transcripts/` để xác nhận file `*.transcript.json` mới đã được lưu thành công.
4. **Chuẩn bị Kế hoạch Dự phòng (Fallback Plan):**
   * Nếu kết nối Wi-Fi tại buổi demo bị ngắt hoặc API Provider bị giới hạn quota, mở sẵn các file transcript JSON đã lưu sẵn trong `transcripts/` hoặc sử dụng bảng điều khiển UI chạy local offline.
