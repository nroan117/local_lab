#!/usr/bin/env bash
# Fetch the latest rightsizer report locally using nginx port-forward
set -euo pipefail
PORT=8080
kubectl port-forward svc/rightsizer-nginx ${PORT}:80 >/dev/null 2>&1 &
PF_PID=$!
# Give port-forward a moment
sleep 1
trap 'kill ${PF_PID} >/dev/null 2>&1 || true' EXIT
curl -s "http://localhost:${PORT}/latest/" -o /tmp/rightsizer-latest.html
echo "Saved /tmp/rightsizer-latest.html"
# Attempt to open in macOS default browser if available
if command -v open >/dev/null 2>&1; then
  open /tmp/rightsizer-latest.html
else
  echo "Open /tmp/rightsizer-latest.html in your browser"
fi
