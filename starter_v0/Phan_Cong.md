# PHÂN CÔNG NHÓM 7 NGƯỜI — DAY 04 RESEARCH AGENT TOOL EVAL

## 1. Mục tiêu chung

Nhóm xây dựng một research agent chạy tool thật, lưu JSON logs, cải tiến prompt và tool declarations qua các phiên bản `v0 → v3`, bổ sung tool mới, xây đúng 10 group eval case, hoàn thiện UI và nộp đầy đủ evidence.

### Deliverables bắt buộc

- Provider preflight thành công.
- Core tools smoke-test thành công.
- Có run hợp lệ cho `v0`, `v1`, `v2`, `v3`.
- Mỗi version có hypothesis, hash, metric và run file.
- Có ít nhất 1 tool mới do nhóm tự viết.
- Có đúng 10 group eval case:
  - 5 single-turn;
  - 5 multi-turn.
- Có live transcript.
- Có UI hiển thị:
  - request;
  - final response;
  - tool name;
  - tool arguments;
  - tool result/error;
  - từng round;
  - artifact version.
- Có `REPORT.md`.
- Có link demo hoặc fallback transcript/run.
- Không lộ `.env`, API key hoặc token.

---

# 2. Trạng thái hiện tại

Nhóm đã hoàn thành baseline `v0`.

## Run v0 chính thức

```text
runs/v0_B_base_openai_20260729T101359397246.json
```

## Kết quả v0

| Metric | Giá trị |
|---|---:|
| Total cases | 20 |
| Measured cases | 20 |
| Provider error cases | 0 |
| Passed cases | 14 |
| Case accuracy | 0.70 |
| Tool routing accuracy | 0.75 |
| Argument accuracy | 0.70 |
| Multiturn accuracy | 1.00 |

## Các case fail ở v0

- `R08_out_of_scope`
- `R10_missing_handle`
- `R11_missing_url`
- `R12_confirm_before_send`
- `R13_parallel_web_and_tweets`
- `R14_out_of_scope_coding`

---

# 3. Nguyên tắc phối hợp

## 3.1. Không sửa fixed eval

Không thay đổi nội dung logic của:

```text
data/eval_base.json
```

Không sửa:

- query;
- expected arguments;
- expected behavior.

Không rename tool trong giai đoạn này nếu không thật sự cần thiết.

## 3.2. v1–v3 phải chạy tuần tự

Một người duy nhất phụ trách toàn bộ chuỗi thí nghiệm `v1 → v2 → v3`.

Quy trình:

```text
Đọc run trước
→ xác định failure
→ viết hypothesis
→ sửa đúng artifact liên quan
→ chạy đúng một version
→ lưu snapshot
→ ghi metric và run path
→ review
→ mới chuyển sang version tiếp theo
```

Không được:

- sửa một lần rồi chạy cả v1, v2, v3;
- chạy các version với artifact giống nhau;
- đổi eval để tăng điểm;
- ghi metric chưa có run thật;
- để nhiều người cùng sửa `system_prompt.md` hoặc `tools.yaml`.

## 3.3. Provider dùng thống nhất

Toàn nhóm dùng:

```bash
--provider openai
```

## 3.4. Không lộ secrets

Không commit hoặc chụp màn hình:

```text
.env
OPENAI_API_KEY
TAVILY_API_KEY
FIRECRAWL_API_KEY
RAPIDAPI_KEY
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
.venv/
__pycache__/
```

---

# 4. Phân công 7 người

---

## NGƯỜI 1 — ALVIN/QUỐC KHÁNH  
## EXPERIMENT OWNER — PHỤ TRÁCH TOÀN BỘ v1, v2, v3

### Vai trò

Sở hữu toàn bộ quá trình tối ưu agent dựa trên evidence.

### File phụ trách chính

```text
artifacts/system_prompt.md
artifacts/tools.yaml
artifacts/versions/v1/
artifacts/versions/v2/
artifacts/versions/v3/
runs/v1_*.json
runs/v2_*.json
runs/v3_*.json
```

### Trách nhiệm

1. Đọc run JSON của version trước.
2. Phân loại lỗi:
   - `wrong_tool`;
   - `wrong_arg_value`;
   - `missing_info`;
   - `wrong_boundary`;
   - `unnecessary_tool`;
   - `out_of_scope`.
3. Viết đúng một hypothesis chính cho mỗi version.
4. Chỉ sửa:
   - `artifacts/system_prompt.md`;
   - và/hoặc `artifacts/tools.yaml`.
5. Chạy eval.
6. Lưu snapshot artifact.
7. Gửi run path và metric cho Người 2.
8. Không tự sửa `version_log.csv` nếu Người 2 đang sở hữu file đó.
9. Không sửa `data/eval_base.json`.

---

### Giai đoạn v1

#### Hypothesis v1 đề xuất

> Prompt v0 ép agent tự đoán dữ liệu thiếu, luôn dùng tool, chỉ chọn một tool và thực hiện action nhạy cảm mà không hỏi xác nhận.

#### Mục tiêu xử lý

- Out-of-scope request không gọi tool.
- Thiếu handle thì dùng `clarify`.
- Thiếu URL thì dùng `clarify`.
- Send/post/publish phải hỏi xác nhận.
- Multi-source request được phép gọi nhiều tool.
- Capability question không gọi tool.

#### Artifact ưu tiên sửa

```text
artifacts/system_prompt.md
```

#### Chạy v1

```bash
python run_eval.py \
  --provider openai \
  --version v1 \
  --suite base \
  --eval-cases data/eval_base.json
```

#### Lưu snapshot

```bash
mkdir -p artifacts/versions/v1
cp artifacts/system_prompt.md artifacts/versions/v1/system_prompt.md
cp artifacts/tools.yaml artifacts/versions/v1/tools.yaml
```

#### Kết quả cần gửi nhóm

- run path;
- artifact version;
- prompt hash;
- tools hash;
- case accuracy;
- tool routing accuracy;
- argument accuracy;
- multiturn accuracy;
- failed cases;
- hypothesis đã dùng.

---

### Giai đoạn v2

Chỉ bắt đầu sau khi đã đọc đầy đủ run v1.

#### Mục tiêu v2

Tập trung vào lỗi còn lại trong tool routing hoặc arguments.

#### Artifact ưu tiên sửa

```text
artifacts/tools.yaml
```

#### Nội dung có thể cần làm rõ

- `timeline` chỉ dùng cho account cụ thể.
- `social_search` dùng cho keyword/topic.
- `lookup` dùng cho web/news.
- `fetch` chỉ dùng với URL thật.
- `format` chỉ dùng khi đã có items.
- `clarify` dùng khi thiếu required arguments.
- `send` có confirmation boundary.
- Mapping:
  - hôm nay → `day`;
  - tuần này → `week`;
  - tháng này → `month`;
  - mới nhất → `Latest`;
  - phổ biến nhất → `Top`.

#### Chạy v2

```bash
python run_eval.py \
  --provider openai \
  --version v2 \
  --suite base \
  --eval-cases data/eval_base.json
```

#### Lưu snapshot

```bash
mkdir -p artifacts/versions/v2
cp artifacts/system_prompt.md artifacts/versions/v2/system_prompt.md
cp artifacts/tools.yaml artifacts/versions/v2/tools.yaml
```

---

### Giai đoạn v3

Chỉ bắt đầu sau khi đã đọc run v2 và nhận feedback từ nhóm.

#### Mục tiêu v3

Sửa hypothesis cuối cùng dựa trên lỗi thật, có thể gồm:

- multi-tool routing;
- correction trong multi-turn;
- confirmation boundary;
- unnecessary tool;
- tích hợp tool mới;
- cải thiện group eval readiness.

#### Chạy v3

```bash
python run_eval.py \
  --provider openai \
  --version v3 \
  --suite base \
  --eval-cases data/eval_base.json
```

#### Lưu snapshot

```bash
mkdir -p artifacts/versions/v3
cp artifacts/system_prompt.md artifacts/versions/v3/system_prompt.md
cp artifacts/tools.yaml artifacts/versions/v3/tools.yaml
```

### Definition of Done của Người 1

- Có run hợp lệ cho v1, v2, v3.
- `provider_error_cases = 0`.
- Mỗi version có hypothesis riêng.
- Mỗi version có artifact/hash khác nhau khi có thay đổi.
- Có snapshot đầy đủ.
- Không sửa fixed eval.
- Không bịa metric.

---

## NGƯỜI 2 — EVAL ANALYST, VERSION LOG VÀ REPORT OWNER

### Vai trò

Reviewer độc lập cho toàn bộ v0–v3.

### File phụ trách

```text
artifacts/version_log.csv
analysis/base_runs.csv
artifacts/REPORT.md
```

### Trách nhiệm

1. Đọc run JSON của v0–v3.
2. Kiểm tra:
   - `provider_error_cases = 0`;
   - `measured_cases = total_cases`;
   - tool results không có lỗi API nghiêm trọng.
3. Parse runs:

```bash
python scripts/parse_runs.py \
  runs/ \
  --output analysis/base_runs.csv
```

4. Cập nhật `version_log.csv` sau mỗi version.
5. Ghi:
   - reason;
   - hypothesis;
   - artifact version;
   - prompt hash;
   - tools hash;
   - metric before;
   - metric after;
   - run file.
6. Viết bảng v0–v3 trong `REPORT.md`.
7. Kiểm tra metric trong report có truy ngược được về run JSON.
8. Viết failure analysis và reflection.
9. Phản hồi cho Người 1 trước khi chạy version tiếp theo.

### Definition of Done

- Version log đủ v0–v3.
- Không có số liệu tự bịa.
- Có bảng before/after rõ ràng.
- Mỗi hypothesis truy ngược được về failure cụ thể.
- `REPORT.md` có phần A và B.

---

## NGƯỜI 3 — NEW TOOL ENGINEER

### Vai trò

Xây ít nhất một tool mới do nhóm tự viết.

### Tool đề xuất

```text
source_compare
```

### File phụ trách

```text
tools/source_compare/
tools/__init__.py
```

### Cấu trúc

```text
tools/source_compare/
├── __init__.py
├── tool.py
└── TOOL.md
```

### Contract đề xuất

```python
def compare_sources(
    items: list[dict],
    criterion: str = "coverage",
    max_items: int = 5,
) -> dict:
    ...
```

### Yêu cầu

- Không cần API key.
- Deterministic.
- Không có side effect.
- Có type hints.
- Validate input.
- Không crash khi input rỗng.
- Không dùng bare `except`.
- Không claim factual verification.
- Cảnh báo khi ít hơn 2 source hợp lệ.
- Output contract nhất quán.

### Output đề xuất

```json
{
  "items": [],
  "comparison": {
    "agreements": [],
    "unique_claims": [],
    "potential_conflicts": [],
    "missing_metadata": []
  },
  "warnings": [],
  "error": null,
  "message": "Compared 2 sources"
}
```

### Lưu ý phối hợp

Người 3 không tự sửa `artifacts/tools.yaml` khi Người 1 đang chạy v1–v3.

Phần declaration của tool mới sẽ được:

- Người 3 chuẩn bị nội dung;
- Người 1 hoặc Người 7 merge vào `tools.yaml` ở thời điểm phù hợp.

### Quicktest

```bash
python - <<'PY'
from tools import TOOL_FUNCTIONS as T

result = T["source_compare"](
    items=[
        {
            "title": "Source A",
            "url": "https://example.com/a",
            "source": "A",
            "summary": "AI adoption increased in 2026."
        },
        {
            "title": "Source B",
            "url": "https://example.com/b",
            "source": "B",
            "summary": "AI adoption increased, especially in education."
        }
    ]
)

print({
    "error": result.get("error"),
    "result_type": type(result).__name__,
    "message": result.get("message"),
})
PY
```

### Definition of Done

- Có `TOOL.md`.
- Có implementation.
- Có registry.
- Có declaration cuối cùng.
- Quicktest pass.
- Có evidence trong report.
- Có ít nhất một group eval case dùng tool mới.

---

## NGƯỜI 4 — GROUP EVAL ENGINEER

### Vai trò

Thiết kế đúng 10 eval case do nhóm tự viết.

### File phụ trách

```text
data/eval_group.json
```

### Yêu cầu

- Chính xác 5 single-turn.
- Chính xác 5 multi-turn.
- Mỗi case có:
  - `id`;
  - `phase: "B"`;
  - `failure_type`;
  - `expect`;
  - `metadata.what_it_tests`.
- Multi-turn phải kết thúc bằng user turn.
- Không copy nguyên sample.
- Không sửa expectation để chiều output sai.

### Case đề xuất

#### Single-turn

1. Web news → `lookup`.
2. URL cụ thể → `fetch`.
3. Account cụ thể → `timeline`.
4. Social keyword → `social_search`.
5. Hai source items → `source_compare`.

#### Multi-turn

1. Thiếu handle → clarify → user bổ sung.
2. Thiếu URL → clarify → user bổ sung.
3. User sửa limit.
4. User hủy request → `no_tool`.
5. Send action → confirmation boundary.

### Validation

```bash
python - <<'PY'
import json
from pathlib import Path

data = json.loads(
    Path("data/eval_group.json").read_text(encoding="utf-8")
)

cases = data["cases"]
single = [case for case in cases if "query" in case]
multi = [case for case in cases if "turns" in case]

assert len(cases) == 10
assert len(single) == 5
assert len(multi) == 5

for case in multi:
    assert case["turns"][-1]["role"] == "user"

print({
    "total": len(cases),
    "single": len(single),
    "multi": len(multi),
})
PY
```

### Chạy group eval

Chỉ chạy sau khi v3 hoàn thành:

```bash
python run_eval.py \
  --provider openai \
  --version v3 \
  --suite group \
  --eval-cases data/eval_group.json
```

### Definition of Done

- Đúng 10 case.
- Đúng tỷ lệ 5/5.
- Có group run JSON.
- Có summary và failed cases.
- Có ít nhất một case test tool mới.

---

## NGƯỜI 5 — LIVE CHAT, TRANSCRIPT VÀ DEMO SCENARIO OWNER

### Vai trò

Chuẩn bị evidence multi-turn và rehearsal demo.

### File phụ trách

```text
transcripts/
docs/demo_scenarios.md
```

### Nhiệm vụ

1. Chuẩn bị 3–5 scenario demo.
2. Chạy live chat trên v3:

```bash
python chat.py \
  --provider openai \
  --version v3
```

3. Scenario bắt buộc:

#### Scenario 1 — Research bình thường

Ví dụ:

```text
Tìm tin AI agent evaluation trong tuần này.
```

#### Scenario 2 — Thiếu thông tin

Ví dụ:

```text
Lấy các bài đăng gần đây của người này.
```

Agent phải clarify, sau đó user bổ sung handle.

#### Scenario 3 — Action nhạy cảm

Ví dụ:

```text
Gửi bản tổng hợp này giúp tôi.
```

Agent phải yêu cầu xác nhận.

#### Scenario 4 — Multi-tool

Ví dụ:

```text
Tìm cả tin web và bài đăng social về AI agent evaluation.
```

#### Scenario 5 — Tool mới

So sánh hai source đã có.

4. Kiểm tra transcript JSON có:
   - artifact version;
   - user turn;
   - assistant response;
   - tool calls;
   - tool results;
   - status.
5. Chuẩn bị fallback transcript nếu mạng lỗi.
6. Phối hợp Người 6 và 7 để đưa scenario vào UI.

### Definition of Done

- Có ít nhất 3 transcript.
- Có đủ normal, clarify và confirmation.
- Có 3–5 scenario rehearse.
- Không gửi Telegram thật.
- Không lộ secrets.

---

## NGƯỜI 6 — FASTAPI BACKEND ENGINEER

### Vai trò

Xây backend cho frontend React TypeScript.

### Quy tắc bắt buộc

Phải tái sử dụng:

```python
chat.py::run_model_tool_loop
```

Không viết agent loop thứ hai.

### File phụ trách

```text
backend/
requirements.txt
```

### Cấu trúc

```text
backend/
├── __init__.py
├── main.py
├── schemas.py
└── services/
    ├── __init__.py
    └── agent_service.py
```

### Endpoint tối thiểu

```text
GET  /api/health
GET  /api/artifacts
POST /api/chat
GET  /api/transcripts/{transcript_id}
```

### Response `/api/chat`

```json
{
  "status": "answered",
  "assistant_text": "...",
  "artifact_version": "v3+...",
  "prompt_hash": "...",
  "tools_hash": "...",
  "rounds": [],
  "tool_events": [],
  "transcript_id": "..."
}
```

### Dependency

```text
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
```

### Chạy local

```bash
uvicorn backend.main:app --reload --port 8000
```

### Yêu cầu

- Load đúng artifact version.
- Trả rounds và tool events.
- Lưu transcript.
- Không trả key.
- Không trả raw stack trace.
- Có CORS local.
- Có Pydantic schemas.
- Có health endpoint.

### Definition of Done

- `/api/health` trả 200.
- `/api/chat` chạy được agent.
- Có transcript.
- Có artifact version.
- Frontend gọi được backend.
- Không lộ secrets.

---

## NGƯỜI 7 — REACT TYPESCRIPT FRONTEND, INTEGRATION VÀ DEPLOY

### Vai trò

Xây giao diện chính và tích hợp toàn bộ hệ thống.

### File phụ trách

```text
frontend/
artifacts/tools.yaml    # chỉ merge theo thống nhất với Người 1 và 3
deployment configs
```

### Stack

```text
React
TypeScript
Vite
```

### Cấu trúc

```text
frontend/
├── src/
│   ├── App.tsx
│   ├── api/
│   │   └── client.ts
│   ├── components/
│   │   ├── ChatPanel.tsx
│   │   ├── ToolTrace.tsx
│   │   ├── VersionSelector.tsx
│   │   ├── ArtifactBadge.tsx
│   │   ├── ScenarioPanel.tsx
│   │   └── TranscriptPanel.tsx
│   └── types/
│       └── agent.ts
├── package.json
└── vite.config.ts
```

### UI bắt buộc

- Request.
- Final response.
- Tool trace theo round.
- Tool name.
- Tool arguments.
- Tool result/error.
- Artifact version.
- Prompt hash.
- Tools hash.
- Version selector.
- Transcript ID.
- Loading state.
- Error state.
- Clear chat.
- Responsive layout.

### Nhiệm vụ integration

1. Kết nối FastAPI backend.
2. Hiển thị v0–v3.
3. Hiển thị 3–5 scenario mẫu.
4. Tích hợp tool mới sau khi Người 3 hoàn thành.
5. Phối hợp Người 1 khi cần cập nhật declaration trong `tools.yaml`.
6. Deploy hoặc mở tunnel.
7. Test bằng browser/device khác.
8. Lưu link demo vào report.

### Chạy frontend

```bash
cd frontend
npm install
npm run dev
```

### Definition of Done

- UI gọi backend thật.
- Trace hiển thị đầy đủ.
- Không có API key phía frontend.
- Có responsive layout.
- Có link demo.
- Có fallback khi backend/network lỗi.

---

# 5. Trình tự làm việc toàn nhóm

## Giai đoạn 1 — Khóa v0 và khởi động song song

### Người 1

- Khóa artifact v0.
- Bắt đầu hypothesis v1.

### Người 2

- Parse v0.
- Ghi dòng v0 vào version log.
- Chuẩn bị report skeleton.

### Người 3

- Scaffold tool mới.
- Viết `TOOL.md`.
- Viết implementation.

### Người 4

- Draft 10 group eval cases.
- Chưa chạy group eval.

### Người 5

- Viết demo scenarios.
- Chuẩn bị transcript checklist.

### Người 6

- Scaffold FastAPI.
- Tạo `/api/health`.

### Người 7

- Scaffold React TSX.
- Dùng mock data để dựng ToolTrace.

---

## Giai đoạn 2 — Chạy v1

### Người 1

- Chạy v1.
- Gửi run path, metric và failed cases.

### Người 2

- Review run v1.
- Cập nhật version log.
- Phản hồi failure còn lại.

### Người 3

- Hoàn thiện tool mới và quicktest.

### Người 4

- Hoàn thiện schema 10 case.

### Người 5

- Chuẩn bị scenario tương ứng lỗi v1.

### Người 6

- Hoàn thiện `/api/chat`.

### Người 7

- Kết nối backend bằng response thật.

---

## Giai đoạn 3 — Chạy v2

### Người 1

- Dựa trên run v1 để đặt hypothesis v2.
- Chạy v2.
- Gửi evidence.

### Người 2

- Review v2.
- Cập nhật version log và bảng metric.

### Người 3

- Mở PR tool mới.
- Phối hợp declaration với Người 1 và 7.

### Người 4

- Validate 10 cases.
- Chờ v3.

### Người 5

- Chuẩn bị live-chat commands.

### Người 6 và 7

- Hoàn thiện end-to-end UI.

---

## Giai đoạn 4 — Chạy v3 và group eval

### Người 1

- Đặt hypothesis v3.
- Chạy v3.
- Khóa artifact cuối.

### Người 2

- Review v3.
- Hoàn thiện bảng v0–v3.

### Người 3

- Xác nhận tool mới đã đăng ký và khai báo.

### Người 4

- Chạy group eval trên v3.

### Người 5

- Chạy live chat và lưu transcript.

### Người 6

- Kiểm tra backend với artifact v3.

### Người 7

- Kiểm tra UI với artifact v3 và tool mới.

---

## Giai đoạn 5 — Report, deploy và nộp

### Người 1

- Kiểm tra final artifact.
- Hỗ trợ sửa routing cuối nếu cần nhưng không phá v3 đã report.

### Người 2

- Hoàn thành `REPORT.md`.

### Người 3

- Viết evidence tool mới.

### Người 4

- Viết group eval summary.

### Người 5

- Rehearse demo và chuẩn bị fallback.

### Người 6

- Deploy backend hoặc mở tunnel.

### Người 7

- Deploy frontend.
- Test từ thiết bị khác.
- Gửi demo URL.

---

# 6. File ownership

| File/Folder | Người sở hữu |
|---|---|
| `artifacts/system_prompt.md` | Người 1 |
| `artifacts/tools.yaml` | Người 1; Người 7 hỗ trợ merge |
| `artifacts/versions/v1-v3/` | Người 1 |
| `runs/v1-v3*.json` | Người 1 |
| `artifacts/version_log.csv` | Người 2 |
| `analysis/` | Người 2 |
| `artifacts/REPORT.md` | Người 2 |
| `tools/source_compare/` | Người 3 |
| `tools/__init__.py` | Người 3 |
| `data/eval_group.json` | Người 4 |
| `transcripts/` | Người 5 |
| `docs/demo_scenarios.md` | Người 5 |
| `backend/` | Người 6 |
| `frontend/` | Người 7 |
| deploy config | Người 6 và 7 |

---

# 7. Branch convention

```text
main
experiment/v1-v3-agent-optimization
docs/eval-report
feature/source-compare-tool
eval/group-cases
demo/live-transcripts
feature/fastapi-backend
feature/react-ui
```

## Người 1 dùng branch

```bash
git switch main
git pull origin main
git switch -c experiment/v1-v3-agent-optimization
```

Mỗi version phải có commit riêng:

```bash
git commit -m "experiment: improve clarification and boundaries in v1"
git commit -m "experiment: refine tool declarations in v2"
git commit -m "experiment: finalize agent routing in v3"
```

---

# 8. Quy tắc merge

Thứ tự merge khuyến nghị:

```text
1. baseline v0
2. v1
3. v2
4. tool mới
5. backend
6. frontend
7. group eval cases
8. v3
9. transcripts
10. report
11. deployment evidence
```

Lưu ý:

- Tool mới có thể được code song song nhưng declaration nên merge ở thời điểm Người 1 xác nhận.
- Group eval chỉ chạy chính thức sau v3.
- Backend và frontend không được viết agent loop riêng.
- Người 2 phải review run trước khi Người 1 chuyển version tiếp theo.

---

# 9. Final validation

Người 2 và Người 7 phối hợp chạy:

```bash
python -m compileall .
git diff --check
git status --short
```

Kiểm tra group eval:

```bash
python - <<'PY'
import json
from pathlib import Path

data = json.loads(
    Path("data/eval_group.json").read_text(encoding="utf-8")
)
cases = data["cases"]

assert len(cases) == 10
assert sum("query" in case for case in cases) == 5
assert sum("turns" in case for case in cases) == 5

for case in cases:
    if "turns" in case:
        assert case["turns"][-1]["role"] == "user"

print("Group eval schema: PASS")
PY
```

Kiểm tra secrets:

```bash
git ls-files | grep -E '(^|/)\.env$|\.venv|__pycache__'
```

Kết quả phải rỗng.

---

# 10. Checklist cuối

```text
[ ] v0 base run
[ ] v1 base run
[ ] v2 base run
[ ] v3 base run
[ ] v3 group run
[ ] 10 group eval cases
[ ] 5 single-turn
[ ] 5 multi-turn
[ ] tool mới
[ ] TOOL.md
[ ] quicktest evidence
[ ] FastAPI backend
[ ] React TypeScript frontend
[ ] tool trace
[ ] artifact version
[ ] transcript JSON
[ ] version_log.csv
[ ] REPORT.md
[ ] demo URL
[ ] fallback run/transcript
[ ] repo đã push
[ ] không lộ secrets
