#!/usr/bin/env bash
# Путь к DRM-узлу встроенной AMD (iGPU) — устойчиво к наличию/отсутствию eGPU
# и смене номеров cardN/renderDN. Аргумент: card | render (по умолчанию render).
#
# Пример: scripts/detect-gpu.sh render -> /dev/dri/renderD128
# Код возврата 1, если iGPU не найден (тогда проброс GPU пропускается).
set -euo pipefail

want="${1:-render}"

for link in /sys/class/drm/card*; do
    name="$(basename "$link")"
    case "$name" in *-*) continue ;; esac              # пропустить коннекторы cardN-XXX
    [ -r "$link/device/vendor" ] || continue
    [ "$(cat "$link/device/vendor")" = "0x1002" ] || continue   # 0x1002 = AMD

    if [ "$want" = "card" ]; then
        dev="/dev/dri/$name"
    else
        render="$(ls "$link/device/drm" 2>/dev/null | grep -m1 '^renderD' || true)"
        [ -n "$render" ] || continue
        dev="/dev/dri/$render"
    fi

    [ -e "$dev" ] || continue                          # файл устройства реально есть
    echo "$dev"
    exit 0
done

echo "встроенная AMD GPU не найдена" >&2
exit 1
