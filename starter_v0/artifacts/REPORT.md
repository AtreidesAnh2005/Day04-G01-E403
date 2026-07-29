# Day 04 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. Xong trước 11:30 để làm tài liệu phụ trợ khi demo.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. Có thể hoàn thiện sau buổi debate để nộp bài.

## Team

- Team: Group 01 - E403
- Members: 7 thành viên (Người 1: Alvin/Quốc Khánh, Người 2: Eval Analyst & Report Owner, ...)
- Provider/model: OpenAI / gpt-4o-mini

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent tự động tìm kiếm thông tin trên mạng xã hội Twitter/X theo từ khóa hoặc theo tài khoản (`@handle`), tìm kiếm thông tin tin tức web qua Tavily, đọc chi tiết nội dung URL và tổng hợp thành digest thông tin có cấu trúc. Agent hỗ trợ hỏi lại người dùng khi thiếu thông tin bắt buộc và xin xác nhận trước khi thực hiện hành động gửi tin nhạy cảm.

**Link dùng thử (truy cập được trong showdown):**

> Streamlit UI chạy tại địa chỉ local bên dưới.
>
> URL: http://localhost:8501

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi lại người dùng khi thiếu thông tin (handle, URL) hoặc xin xác nhận trước hành động nhạy cảm | Không |
| timeline | Lấy các bài đăng gần đây của một tài khoản Twitter/X cụ thể theo screenname | Không |
| social_search | Tìm kiếm bài đăng trên mạng xã hội Twitter/X theo từ khóa hoặc chủ đề | Không |
| lookup | Tìm kiếm thông tin tổng hợp và tin tức trên Web qua Tavily | Không |
| fetch | Đọc và trích xuất nội dung chi tiết từ một đường dẫn URL | Không |
| format | Trình bày và tổng hợp các bài đăng/kết quả đã tìm được thành bản tin markdown digest | Không |
| source_compare | So sánh, đối chiếu nội dung giữa các nguồn tin (agreements, conflicts, unique claims) | Có (Tool mới của nhóm) |

## A3. Câu hỏi mẫu để thử

1. Tweet mới nhất của Sam Altman (@sama) là gì?
2. Tìm các bài đăng gần đây về chủ đề AI trên Twitter và tổng hợp giúp mình.
3. Tóm tắt nội dung bài viết tại URL https://example.com hộ mình.
4. Đăng bản tin này lên Telegram giúp mình.

## A4. Kịch bản demo đã rehearse

| Scenario | Tool trace cần thấy | Câu chuyện cải thiện version | Fallback run/transcript |
|---|---|---|---|
| S1: Tra cứu tin của tài khoản cụ thể | `timeline(screenname="sama", limit=1)` | v0 và v1 đều route đúng `timeline` cho handle chính xác. | `transcripts/scenario1_normal_research.transcript.json` |
| S2: Yêu cầu tóm tắt nhưng thiếu Handle | `clarify(question="...", response_type="text")` | v0 tự đoán hoặc gọi sai tool, v1 học cách gọi `clarify` để hỏi lại handle từ user. | `transcripts/scenario2_clarify_missing_handle.transcript.json` |
| S3: Yêu cầu đăng bài Telegram | `clarify(question="...", response_type="yes_no")` | v0 không hỏi xác nhận, v1 kích hoạt confirmation boundary yêu cầu user xác nhận yes/no. | `transcripts/scenario3_sensitive_confirmation.transcript.json` |
| S4: Tìm tin đa nguồn và tổng hợp | `social_search` $\rightarrow$ `lookup` $\rightarrow$ `format` | v0 chọn 1 tool duy nhất, v1 nâng cấp khả năng chọn chuỗi multi-tool tổng hợp. | `transcripts/scenario4_multitool_research.transcript.json` |

---

# PHẦN B — Chi tiết / Bằng chứng

> Điều kiện metric hợp lệ: `provider_error_cases` phải bằng `0`; `measured_cases` phải bằng `total_cases`; và bất kỳ `tool_results` nào có error đều phải được review thủ công vì routing PASS không chứng minh tool execution đã đúng.

## B1. Version evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Prompt/tool change | Hypothesis | Metric name | Before | After | Run File |
|---|---|---|---|---:|---:|---|
| v0 | baseline starter prompt | Baseline starter prompt causes missing arg guessing, wrong confirmation boundaries, and single-tool restriction. | case_accuracy | N/A | 0.70 | `runs/v0_B_base_openai_20260729T101359397246.json` |
| v1 | Sửa `system_prompt.md` | Bổ sung quy tắc ranh giới quyết định (Ask user khi thiếu handle/URL, Confirmation trước khi gửi, Multi-tool routing, Out-of-scope không gọi tool). | case_accuracy | 0.70 | 0.85 | `runs/v1_B_base_openai_20260729T103835297905.json` |
| v2 | (Đang chờ Người 1 chạy v2) | Tinh chỉnh `tools.yaml` để làm rõ schema các arguments đặc thù (`response_type`). | case_accuracy | 0.85 | TBD | TBD |
| v3 | (Đang chờ Người 1 chạy v3) | Tối ưu tổng thể chuỗi multi-tool và tích hợp tool mới. | case_accuracy | TBD | TBD | TBD |

## B2. Failure analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R08_out_of_scope | out_of_scope | Called tool in v0 | v0 agent tự ý gọi tool cho câu hỏi out-of-scope coding/capability. | Đã sửa trong v1 system prompt: Out-of-scope request không gọi tool (v1 PASS). |
| R10_missing_handle | missing_info | `clarify(question="...")` (v1) | Agent đã route đúng sang `clarify` nhưng thiếu tham số `response_type="text"`. | Cần làm rõ schema tham số `response_type` của `clarify` trong `tools.yaml` ở v2. |
| R11_missing_url | missing_info | `clarify(question="...")` (v1) | Agent đã route đúng `clarify` khi thiếu URL bài viết nhưng thiếu `response_type="text"`. | Củng cố thêm mô tả default args cho `clarify` trong `tools.yaml` ở v2. |
| R12_confirm_before_send | wrong_boundary | `clarify(question="...", response_type="text")` (v1) | Agent nhận diện cần hỏi lại nhưng hỏi xin nội dung tin thay vì xin xác nhận yes/no trước khi gửi. | Cần siết chặt định nghĩa confirmation boundary cho hành động nhạy cảm trong `tools.yaml` và prompt v2. |

## B3. Team eval cases

List the 10 cases added to `data/eval_group.json`:

- 5 single-turn
- 5 multi-turn

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| (Đang chờ Người 4/5 soạn 10 cases) |  |  |  |

## B4. Live chat evidence

Use `transcripts/*.transcript.json`.

| Scenario/Turn | Version | Tool Calls + Args | Transcript/Run | Outcome |
|---|---|---|---|---|
| Scenario 1 | v1 | `timeline(screenname="sama", limit=1)` | `transcripts/scenario1_normal_research.transcript.json` | PASS |
| Scenario 2 | v1 | `clarify(question="...", response_type="text")` | `transcripts/scenario2_clarify_missing_handle.transcript.json` | PASS |
| Scenario 3 | v1 | `clarify(question="...", response_type="text")` | `transcripts/scenario3_sensitive_confirmation.transcript.json` | PASS |
| Scenario 4 | v1 | Multi-tool: `social_search` + `lookup` | `transcripts/scenario4_multitool_research.transcript.json` | PASS |

## B5. Tool capability evidence

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Must-have: tool mới đầu tiên | `tools/source_compare/tool.py` | So sánh đối chiếu nội dung nhiều nguồn tin rõ ràng. | Validate input không rỗng. |

## B6. Reflection

- **Which fixes belonged in `system_prompt.md`?** Các quy tắc ranh giới quyết định chung: khi nào hỏi lại (`clarify`), khi nào xin xác nhận (`yes_no`), khi nào không dùng tool (out-of-scope).
- **Which fixes belonged in `tools.yaml`?** Khai báo chi tiết kiểu dữ liệu tham số (`response_type: text/yes_no`), giá trị mặc định (`limit`), mô tả rõ trường hợp sử dụng (use-case boundary).
- **Which failure needed manual review instead of automatic grading?** Các case câu trả lời `clarify` có nội dung câu hỏi sinh ra linh hoạt (`question` string tự nhiên).
- **What would you improve next?** Tinh chỉnh `tools.yaml` ở v2 để đạt 100% accuracy cho các tham số `response_type` của `clarify`.
