#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <fixture>  # fixture: idle|low|bursty|mem"
  exit 2
fi
FIX=$1
kubectl -n default set env deployment/dcgm-mock DCGM_FIXTURE=$FIX
echo "Patched dcgm-mock to serve fixture: $FIX"
