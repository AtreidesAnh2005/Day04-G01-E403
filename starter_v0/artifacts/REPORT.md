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
| S2: Yêu cầu tóm tắt nhưng thiếu Handle | `clarify(question="...", response_type="text")` | v0 tự đoán, v1 gọi clarify thiếu arg, v2 hoàn thành hỏi lại chuẩn xác (100% PASS). | `transcripts/scenario2_clarify_missing_handle.transcript.json` |
| S3: Yêu cầu đăng bài Telegram | `clarify(question="...", response_type="yes_no")` | v0 không hỏi xác nhận, v1 hỏi xin nội dung, v2 kích hoạt xác nhận yes_no chuẩn xác (100% PASS). | `transcripts/scenario3_sensitive_confirmation.transcript.json` |
| S4: Tìm tin đa nguồn và tổng hợp | `social_search` $\rightarrow$ `lookup` $\rightarrow$ `format` | v0 chọn 1 tool duy nhất, v1 và v2 nâng cấp khả năng chọn chuỗi multi-tool tổng hợp. | `transcripts/scenario4_multitool_research.transcript.json` |

---

# PHẦN B — Chi tiết / Bằng chứng

> Điều kiện metric hợp lệ: `provider_error_cases` phải bằng `0`; `measured_cases` phải bằng `total_cases`; và bất kỳ `tool_results` nào có error đều phải được review thủ công vì routing PASS không chứng minh tool execution đã đúng.

## B1. Version evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Prompt/tool change | Hypothesis | Metric name | Before | After | Run File |
|---|---|---|---|---:|---:|---|
| v0 | baseline starter prompt | Baseline starter prompt causes missing arg guessing, wrong confirmation boundaries, and single-tool restriction. | case_accuracy | N/A | 0.70 | `runs/v0_B_base_openai_20260729T101359397246.json` |
| v1 | Sửa `system_prompt.md` | Bổ sung quy tắc ranh giới quyết định (Ask user khi thiếu handle/URL, Confirmation trước khi gửi, Multi-tool routing, Out-of-scope không gọi tool). | case_accuracy | 0.70 | 0.85 | `runs/v1_B_base_openai_20260729T103835297905.json` |
| v2 | Tinh chỉnh `tools.yaml` | Tinh chỉnh schema tham số `response_type` (text vs yes_no) và mô tả default args của `clarify` trong `tools.yaml`. | case_accuracy | 0.85 | **1.00** | `runs/v2_B_base_openai_20260729T111951627516.json` |
| v3 | (Đang chờ Người 1 chạy v3) | Tối ưu tổng thể chuỗi multi-tool và tích hợp tool mới. | case_accuracy | 1.00 | TBD | TBD |

## B2. Failure analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R08_out_of_scope | out_of_scope | Called tool in v0 | v0 agent tự ý gọi tool cho câu hỏi out-of-scope coding/capability. | Đã sửa trong v1 system prompt: Out-of-scope request không gọi tool (v1 & v2 PASS). |
| R10_missing_handle | missing_info | `clarify(question="...")` (v1) | Agent ở v1 đã route đúng sang `clarify` nhưng thiếu tham số `response_type="text"`. | Đã sửa triệt để trong v2 tools.yaml: Bổ sung enum và default schema (v2 PASS 100%). |
| R11_missing_url | missing_info | `clarify(question="...")` (v1) | Agent ở v1 đã route đúng `clarify` khi thiếu URL bài viết nhưng thiếu `response_type="text"`. | Đã sửa triệt để trong v2 tools.yaml: Làm rõ mô tả tham số (v2 PASS 100%). |
| R12_confirm_before_send | wrong_boundary | `clarify(question="...", response_type="text")` (v1) | Agent ở v1 hỏi xin nội dung tin thay vì xin xác nhận yes/no trước khi gửi. | Đã sửa triệt để trong v2 tools.yaml: Ranh giới confirmation boundary ép kiểu yes_no (v2 PASS 100%). |

> 📌 **Ghi chú v2:** Ở phiên bản `v2`, toàn bộ 20/20 test cases đều **PASS 100%**, không còn case nào bị failure!

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
| Scenario 1 | v2 | `timeline(screenname="sama", limit=1)` | `transcripts/scenario1_normal_research.transcript.json` | PASS |
| Scenario 2 | v2 | `clarify(question="...", response_type="text")` | `transcripts/scenario2_clarify_missing_handle.transcript.json` | PASS |
| Scenario 3 | v2 | `clarify(question="...", response_type="yes_no")` | `transcripts/scenario3_sensitive_confirmation.transcript.json` | PASS |
| Scenario 4 | v2 | Multi-tool: `social_search` + `lookup` | `transcripts/scenario4_multitool_research.transcript.json` | PASS |

## B5. Tool capability evidence

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Must-have: tool mới đầu tiên | `tools/source_compare/tool.py` | So sánh đối chiếu nội dung nhiều nguồn tin rõ ràng. | Validate input không rỗng. |

## B6. Reflection

- **Which fixes belonged in `system_prompt.md`?** Các quy tắc ranh giới quyết định chung: khi nào hỏi lại (`clarify`), khi nào xin xác nhận (`yes_no`), khi nào không dùng tool (out-of-scope).
- **Which fixes belonged in `tools.yaml`?** Khai báo chi tiết kiểu dữ liệu tham số (`response_type: text/yes_no`), giá trị mặc định (`limit`), mô tả rõ trường hợp sử dụng (use-case boundary).
- **Which failure needed manual review instead of automatic grading?** Các case câu trả lời `clarify` có nội dung câu hỏi sinh ra linh hoạt (`question` string tự nhiên).
- **What would you improve next?** Duy trì 100% accuracy và chuẩn bị đánh giá trên bộ 10 team eval cases (`eval_group.json`).
