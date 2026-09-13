#!/bin/bash
# run_rl_repeats.sh — стабильные N повторов RL (go2_policy.py).
# Перед каждым запуском чистит lock-файлы Kit (причина зависаний старта),
# при неудачной инициализации повторяет попытку.
set -u
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$HOME/isaacsim-venv/bin/python"
KIT="$HOME/isaacsim-venv/lib/python3.12/site-packages/isaacsim/kit"
N="${1:-3}"
RUN_SEC="${2:-15}"
VX="${3:-0.3}"

echo "$VX 0 0" > /tmp/rl_cmd.txt
echo "=== RL повторы: N=$N, ${RUN_SEC}s, vx=$VX ==="

for i in $(seq 1 "$N"); do
  for attempt in 1 2; do
    # сброс lock-файлов Kit (залипают после прерываний)
    rm -rf "$KIT/cache/DerivedDataCache/app_instance_lock0" 2>/dev/null
    rm -f "$KIT/cache/DerivedDataCache"/*.lock "$KIT/cache/ov/"*.lock 2>/dev/null
    cat /tmp/rl_cmd.txt | GO2_TELEMETRY_TAG=rl_r$i timeout 90 \
      "$PY" -u "$REPO/src/isaac/go2_policy.py" --headless --duration "$RUN_SEC" \
      > "/tmp/rl_r$i.log" 2>&1
    rc=$?
    if grep -aq "policy initialized" "/tmp/rl_r$i.log" 2>/dev/null; then
      echo "  RL повтор $i: OK (попытка $attempt, rc=$rc)"
      break
    fi
    echo "  RL повтор $i: попытка $attempt неудачна (rc=$rc), повтор"
  done
done

echo "=== готово ==="
ls -t "$REPO"/logs/isaac/telemetry_rl_r*_*.csv 2>/dev/null | head -n "$N"
