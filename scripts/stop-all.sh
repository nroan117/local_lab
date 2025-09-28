#!/usr/bin/env bash
set -euo pipefail

# stop-all.sh — stop port-forwards and optionally tear down the kind cluster and k8s resources
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

# Kill any kubectl port-forward processes started previously
echo "Stopping kubectl port-forward processes..."
pkill -f 'kubectl port-forward' || true

echo "Deleting k8s resources applied by this lab (kubectl delete -k k8s/)"
read -p "Delete cluster resources and kind cluster? [y/N]: " yn || true
if [[ "${yn:-n}" =~ ^[Yy]$ ]]; then
  kubectl delete -k k8s/ || true
  echo "Deleting kind cluster 'rightsizer-kind'..."
  kind delete cluster --name rightsizer-kind || true
  echo "Optionally remove local images?"
  read -p "Remove images? [y/N]: " rmi || true
  if [[ "${rmi:-n}" =~ ^[Yy]$ ]]; then
    docker rmi rightsizer-local/dcgm-mock:latest rightsizer-local/rightsizer-collector:latest rightsizer-local/rightsizer-nginx:latest || true
  fi
else
  echo "Left k8s resources and kind cluster running."
fi

echo "Done."
