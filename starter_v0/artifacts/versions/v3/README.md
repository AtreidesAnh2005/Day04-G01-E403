# Artifact v3

## Hypothesis

V2 achieved full accuracy on the fixed base evaluation, but the agent did not
yet have a declared routing policy for the new `source_compare` tool.

Adding a narrow tool declaration and a minimal routing rule should extend the
agent's source-comparison capability without causing regression on the base
suite.

## Changed artifacts

- `artifacts/system_prompt.md`
- `artifacts/tools.yaml`
- `tools/source_compare/`
- `tools/__init__.py`

## Main changes

- Added the `source_compare` tool to the agent registry.
- Added deterministic source-comparison implementation and tests.
- Added tool declaration with supported criteria:
  - `coverage`
  - `agreement`
  - `conflicts`
- Restricted the tool to source items already collected.
- Preserved literal user search keywords.
- Preserved confirmation-first behavior for side-effecting actions.

## Run information

- Provider: `openai`
- Suite: `base`
- Run file: `runs/v3_B_base_openai_20260729T114119891490.json`
- Passed cases: 20/20
- Case accuracy: 1.00
- Tool routing accuracy: 1.00
- Argument accuracy: 1.00
- Multiturn accuracy: 1.00
- Provider error cases: 0

## Regression result

V3 preserved the complete v2 base score while adding the new
`source_compare` capability.
