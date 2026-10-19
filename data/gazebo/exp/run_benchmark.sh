#!/usr/bin/env bash
# Полный прогон базовой сцены: сбор, съёмка, бенчмарк, телеметрия, EDA.
# Варианты света и видео-облёт запускаются отдельно (variants.py + capture_views.py).
set -euo pipefail

cd "$(dirname "$0")/../../.."
ROOT="$(pwd)"
PY="$ROOT/.venv-lyrical/bin/python"

if [ ! -x "$PY" ]; then
  echo "Нет $PY. Создай venv и поставь requirements-benchmark.txt" >&2
  exit 1
fi

echo "== 1/11 сцена =="
"$PY" data/gazebo/exp/build_scene.py

echo "== 2/11 контейнер =="
docker compose up -d simulator
docker compose exec -T simulator bash -lc \
  'pkill -x ruby || true; source /opt/ros/jazzy/setup.bash; \
   nohup gz sim -s -r /root/ws/data/exp/world.sdf > /tmp/gz.log 2>&1 &'
sleep 15

echo "== 3/11 съёмка 48 ракурсов =="
"$PY" data/gazebo/exp/capture_views.py

echo "== 4/11 остановка Gazebo (чистый замер T) =="
docker compose exec -T simulator bash -lc 'pkill -x ruby || true'

echo "== 5/11 бенчмарк =="
"$PY" data/gazebo/exp/benchmark.py

echo "== 6/11 телеметрия =="
"$PY" data/gazebo/exp/telemetry.py

echo "== 7/11 confusion и листы =="
"$PY" data/gazebo/exp/analyze.py

echo "== 8/11 F1-свип =="
"$PY" data/gazebo/exp/sweep.py

echo "== 9/11 RSS =="
"$PY" data/gazebo/exp/rss.py

echo "== 10/11 GT, метрики, runtime =="
"$PY" data/gazebo/exp/gt_tools.py
"$PY" data/gazebo/exp/metrics.py
"$PY" data/gazebo/exp/runtime.py

echo "== 11/11 EDA и агрегат =="
"$PY" data/gazebo/exp/eda.py
"$PY" data/gazebo/exp/aggregate.py

echo "Готово: data/gazebo/exp/eda/REPORT.md, benchmark_results.csv, metrics.csv"
