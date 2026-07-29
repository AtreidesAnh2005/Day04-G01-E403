# Artifact v2

## Hypothesis

V1 selected the correct tools, but clarification calls sometimes omitted
`response_type`, and side-effecting requests did not prioritize confirmation.

Making `response_type` required and clarifying the confirmation boundary in
tool declarations should improve argument accuracy without reducing routing
accuracy.

## Changed artifact

- `artifacts/tools.yaml`

## Main changes

- Required `response_type` in `clarify`.
- Defined `response_type="text"` for missing handles and URLs.
- Defined `response_type="yes_no"` for confirmation before side effects.
- Prioritized confirmation for send, post, publish, and delivery requests.
- Clarified that the initial action request is not explicit confirmation.

## Run information

- Provider: `openai`
- Suite: `base`
- Run file: `runs/v2_B_base_openai_20260729T111951627516.json`
- Artifact version: `v2+p87d2e5cc289d+te1ced7e1ed77`

## Metrics

| Metric | v1 | v2 |
|---|---:|---:|
| Passed cases | 17 | 20 |
| Case accuracy | 0.85 | 1.00 |
| Tool routing accuracy | 1.00 | 1.00 |
| Argument accuracy | 0.85 | 1.00 |
| Multiturn accuracy | 1.00 | 1.00 |
| Provider error cases | 0 | 0 |

## Fixed cases

- `R10_missing_handle`
- `R11_missing_url`
- `R12_confirm_before_send`

## Remaining failures

None.
