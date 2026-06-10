#!/usr/bin/env bash
# Run every wave smoke from the packaged engine. Verifies the whole programme
# locally (synthetic fixtures + transcribed static reference). Green here proves
# wiring/parity; the LIVE confirmations in ACTION_PLAN.md are the real gates.
set -e
cd "$(dirname "$0")"
export SCIP_INSIGHT_CUTOVER=shadow      # default-off; nothing renders live
export SCIP_PLACEMENT_RENDER=static     # default-off; legacy render

echo "== regenerate D-2 migration artifacts (optional; included pre-generated) =="
python build_d2_migration.py

for s in smoke_insight_shadow_parity smoke_insight_wave_b smoke_editorial_wave_c \
         smoke_placement_wave_d1 smoke_placement_wave_d2; do
  echo "== $s =="
  if python "$s.py" >/tmp/$s.log 2>&1; then echo "$s: PASS"; else echo "$s: FAIL"; tail -20 /tmp/$s.log; exit 1; fi
done
echo
echo "ALL WAVE SMOKES PASS (A, B, C, D-1, D-2)"
