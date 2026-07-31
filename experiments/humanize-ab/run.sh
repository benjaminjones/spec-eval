#!/usr/bin/env bash
# A/B the humanize question against spec-eval's own graders, on one small spec.
#
#   REPS=3 MODEL=anthropic:claude-opus-4-8 experiments/humanize-ab/run.sh
#
# Swaps each variant into spec_eval/runlog.md, scores it with `sufficiency` and `audit`, and restores the
# original on every exit path (including Ctrl-C). Writes only under experiments/humanize-ab/.results — the
# repo's real spec-reports/ is never touched.
set -uo pipefail

cd "$(dirname "$0")/../.." || exit 1

REPS="${REPS:-3}"
MODEL="${MODEL:-anthropic:claude-opus-4-8}"
PY="${PY:-.venv/bin/python}"
SPEC="spec_eval/runlog.md"
EXP="experiments/humanize-ab"
RESULTS="$EXP/.results"
VARIANTS=(baseline frozen naive)

[ -x "$PY" ] || { echo "no interpreter at $PY (set PY=...)"; exit 1; }
if [ -z "${ANTHROPIC_API_KEY:-}${OPENAI_API_KEY:-}${GOOGLE_API_KEY:-}" ] && [ ! -f .env ]; then
  echo "No provider key in the environment and no .env file."
  echo "Set one (export ANTHROPIC_API_KEY=...) or pass --env; the graders need a model."
  exit 1
fi

# The A/B is only interpretable while the variants differ from the baseline in shape alone.
"$PY" "$EXP/scripts/verify_facts.py" || { echo "fact guard failed — not spending model calls"; exit 1; }

BACKUP="$(mktemp)"
cp "$SPEC" "$BACKUP"
restore() {
  cp "$BACKUP" "$SPEC" && rm -f "$BACKUP"
  echo ""
  echo "restored $SPEC from backup"
}
trap restore EXIT INT TERM

mkdir -p "$RESULTS"
CSV="$RESULTS/results.csv"
echo "variant,rep,sufficiency,gaps_major,gaps_minor,drift_high,drift_medium,drift_low" > "$CSV"

for variant in "${VARIANTS[@]}"; do
  for rep in $(seq 1 "$REPS"); do
    out="$RESULTS/$variant-$rep"
    mkdir -p "$out"
    cp "$EXP/runlog.$variant.md.variant" "$SPEC"
    echo ""
    echo "=== $variant rep $rep/$REPS ==============================================="
    "$PY" -m spec_eval sufficiency "spec_eval/runlog.py" --model "$MODEL" --out "$out" || true
    "$PY" -m spec_eval audit       "spec_eval/runlog.py" --model "$MODEL" --out "$out" || true
    "$PY" "$EXP/scripts/collect.py" "$out" "$variant" "$rep" >> "$CSV"
  done
done

echo ""
echo "=== summary ==============================================================="
"$PY" "$EXP/scripts/collect.py" --summarize "$CSV"
echo ""
echo "per-run artifacts: $RESULTS/<variant>-<rep>/  (sufficiency.json, findings.json, report.md)"
echo "csv:               $CSV"
