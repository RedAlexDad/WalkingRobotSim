#!/usr/bin/env bash
# Run the cafe RViz demo headlessly and capture a 1920x1080 screenshot.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# RViz may need a session bus; re-exec under dbus-run-session once.
if [ -z "${DBUS_SESSION_BUS_ADDRESS:-}" ]; then
  exec dbus-run-session -- "$0" "$@"
fi

set +u
source /opt/ros/lyrical/setup.bash
set -u
export DISPLAY=:99
export QT_QPA_PLATFORM=xcb
export LIBGL_ALWAYS_SOFTWARE=1
export XDG_RUNTIME_DIR=/tmp/opencode/xdg-rviz
mkdir -p "$XDG_RUNTIME_DIR" "$DIR/screenshots"
chmod 700 "$XDG_RUNTIME_DIR"

Xvfb :99 -screen 0 1920x1080x24 +extension GLX +render -noreset >"$DIR/xvfb.log" 2>&1 &
XVFB_PID=$!
sleep 1

python3 "$DIR/cafe_demo.py" >"$DIR/demo.log" 2>&1 &
PUB_PID=$!
sleep 1

rviz2 --fullscreen -d "$DIR/rviz/cafe_supervisory.rviz" >"$DIR/rviz.log" 2>&1 &
RVIZ_PID=$!

cleanup() {
  kill "$RVIZ_PID" "$PUB_PID" "$XVFB_PID" 2>/dev/null || true
}
trap cleanup EXIT

sleep 15
ffmpeg -y -loglevel error -f x11grab -draw_mouse 0 -video_size 1920x1080 -i :99.0 -frames:v 1 "$DIR/screenshots/cafe_supervisory.png"

echo "screenshot: $DIR/screenshots/cafe_supervisory.png"
