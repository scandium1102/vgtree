# Runtime modes

Select the mode once per operation and report it in the result.

## ENGINE

Run `vgtree --version` without installing anything. Select ENGINE only when the command exists and reports a compatible `1.1.x` release. Use the CLI for schema validation, state mutations, coverage, receipt binding, and completion gates. A machine result may be reported as `PASS` only from the command output and matching readback.

Report:

- `runtime_mode=ENGINE`
- `engine_validation=PASS|FAIL|INCOMPATIBLE`
- the exact version and command result

## SKILL_ONLY

Select SKILL_ONLY when the CLI is absent or not compatible. Do not install VGTREE automatically. Use the packaged schemas, templates, and checklists for planning, a manual work record, receipt drafting, and read-only review.

SKILL_ONLY is an honest fallback, not a second engine:

- `runtime_mode=SKILL_ONLY`
- `engine_validation=NOT_RUN`
- overall status cannot exceed `REVIEW_REQUIRED`
- never claim that state, coverage, receipt, or completion gates passed
- preserve exact missing checks and the command that an ENGINE run should execute later

The shared resources are under `../../shared/` from each Skill directory.

