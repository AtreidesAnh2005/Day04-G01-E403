# Artifact v1

## Hypothesis

The v0 system prompt encouraged the agent to guess missing information,
always call a tool, select only one tool, and cross confirmation boundaries.

A clearer decision policy should improve:

- out-of-scope no-tool behavior;
- missing-information handling;
- confirmation boundaries;
- multi-tool routing.

## Run information

- Provider: `openai`
- Suite: `base`
- Run file: `runs/v1_B_base_openai_20260729T103835297905.json`
- Artifact version: `v1+p87d2e5cc289d+t011c271ef0bb`

## Metrics

| Metric | v0 | v1 |
|---|---:|---:|
| Passed cases | 14 | 17 |
| Case accuracy | 0.70 | 0.85 |
| Tool routing accuracy | 0.75 | 1.00 |
| Argument accuracy | 0.70 | 0.85 |
| Multiturn accuracy | 1.00 | 1.00 |
| Provider error cases | 0 | 0 |

## Fixed cases

- `R08_out_of_scope`
- `R13_parallel_web_and_tweets`
- `R14_out_of_scope_coding`

## Remaining failures

- `R10_missing_handle` — wrong argument value
- `R11_missing_url` — wrong argument value
- `R12_confirm_before_send` — wrong argument value

## Conclusion

The v1 hypothesis was partially supported.

Tool selection and routing improved significantly, but the clarification and
confirmation tool argument contract still needs refinement.
