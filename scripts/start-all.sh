#!/usr/bin/env bash
set -euo pipefail

# start-all.sh — convenience wrapper to build images, create kind cluster, load images, deploy, and port-forward
# Usage: ./scripts/start-all.sh

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

echo "1/5: Build images"
make build-images

echo "2/5: Create kind cluster (idempotent)"
if kind get clusters | grep -q rightsizer-kind; then
  echo "kind cluster 'rightsizer-kind' already exists"
else
  make kind-create
fi

echo "3/5: Load images into kind"
make load-images-verify

echo "4/5: Apply k8s manifests"
kubectl apply -k k8s/

echo "5/5: Port-forward Prometheus and nginx (in background)"
# Start port-forwards in background and print PIDs
kubectl port-forward svc/prometheus 9090:9090 >/dev/null 2>&1 &
PF_PROM_PID=$!
kubectl port-forward svc/rightsizer-nginx 8080:80 >/dev/null 2>&1 &
PF_NGINX_PID=$!

echo "Prometheus port-forward PID=$PF_PROM_PID (http://localhost:9090)"
echo "NGINX port-forward PID=$PF_NGINX_PID (http://localhost:8080)"

echo "Done. Use Ctrl-C to stop this script; port-forwards will continue in background."

echo "To tear down: ./scripts/stop-all.sh or follow README teardown steps."
