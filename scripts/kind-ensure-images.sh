#!/usr/bin/env bash
# Ensure images are loaded into a kind cluster and verify they are present inside the node.
# Usage: kind-ensure-images.sh <cluster-name> <image1> [<image2> ...]
set -euo pipefail
cluster_name=${1:-}
if [ -z "$cluster_name" ]; then
  echo "usage: $0 <cluster-name> <image1> [image2 ...]"
  exit 2
fi
shift
images=("$@")
node_container="kind-control-plane"
# Determine the actual container name for the control-plane node
actual_node_container=$(docker ps --format '{{.Names}}' | grep "${cluster_name}-control-plane" || true)
if [ -n "$actual_node_container" ]; then
  node_container=$actual_node_container
fi
echo "Loading images into kind cluster '${cluster_name}' (node container: ${node_container})"
# Load images (kind load already does this if called separately)
for img in "${images[@]}"; do
  echo "-> Loading ${img} into kind..."
  kind load docker-image "${img}" --name "${cluster_name}"
done
# Verify images exist inside containerd on the node
echo "Verifying images are present inside the kind node..."
# Try ctr first (containerd); use the k8s.io namespace
missing=()
for img in "${images[@]}"; do
  short="${img##*/}"
  # List images via containerd's ctr
  if docker exec "${node_container}" ctr -n k8s.io images ls | grep -E "${short}" >/dev/null 2>&1; then
    echo "  OK: ${img} present (ctr)"
  else
    # fallback to crictl if available
    if docker exec "${node_container}" sh -c "command -v crictl >/dev/null 2>&1"; then
      if docker exec "${node_container}" crictl images | grep -E "${short}" >/dev/null 2>&1; then
        echo "  OK: ${img} present (crictl)"
      else
        echo "  MISSING: ${img}"
        missing+=("${img}")
      fi
    else
      echo "  MISSING: ${img} (no crictl and not found via ctr)"
      missing+=("${img}")
    fi
  fi
done
if [ ${#missing[@]} -ne 0 ]; then
  echo "ERROR: Some images are missing inside kind node: ${missing[*]}"
  echo "You can try running: kind load docker-image <image> --name ${cluster_name}"
  exit 3
fi
echo "All images are present inside the kind node."
exit 0
