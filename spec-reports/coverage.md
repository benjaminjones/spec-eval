# Spec coverage — `spec-eval`
**100%** — 11/11 spec-worthy code files have a governing spec.

## Unmodeled markdown *(outside the same-stem pairing model — neither covered nor uncovered)*
The percentage above scores code files against a spec of the same name. These directories hold markdown that pairing cannot reach — a spec tree keyed by requirement id, or behavior written AS markdown. Read the percentage as scoped to same-stem pairs, not to the project.
- **skills/** — 3 markdown file(s): `skills/spec-authoring/templates/OVERVIEW-template.md`, `skills/spec-authoring/templates/SPEC-HEALTH-template.md`, `skills/spec-authoring/templates/spec-template.md`
- **spec-reports/** — 3 markdown file(s): `spec-reports/coverage.md`, `spec-reports/report.md`, `spec-reports/sufficiency.md`

## Excluded (impractical to spec — by class)
- **glue** (2): `spec_eval/__init__.py`, `spec_eval/__main__.py`
- **test** (29): `tests/acceptance/test_ac_commands.py`, `tests/acceptance/test_ac_diagram.py`, `tests/acceptance/test_ac_file_scope.py`, `tests/acceptance/test_ac_layouts.py`, `tests/acceptance/test_ac_orphans.py`, `tests/conftest.py`, `tests/contract/test_artifact_hygiene.py`, `tests/contract/test_audit_parse.py` …
- **tooling** (1): `.github/scripts/check_artifact_hygiene.py`