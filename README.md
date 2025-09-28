# Rightsizer Local Test Lab

This workspace scaffolds a lightweight local environment to develop and test a Rightsizer Collector using:

- kind (single-node) Kubernetes cluster
- Prometheus (single pod, short retention)
- DCGM-mock server that exposes Prometheus-style GPU metrics at `/metrics`
- Rightsizer collector (Job/CronJob) that queries Prometheus and writes an HTML report to `/reports/latest`
- An optional NGINX deployment to serve the reports from the PVC
# Rightsizer Local Test Lab

A small local lab for developing and testing the Rightsizer collector with:

- kind (single-node Kubernetes)
- Prometheus (single pod)
- A dcgm-mock server that exposes Prometheus-format GPU metrics at `/metrics`
- A collector that queries Prometheus and writes an HTML report to `/reports/latest`
- An optional nginx to serve the reports from a PVC

This README gives minimal, copy-paste commands to get started, verify, run a smoke test, switch fixtures, and tear everything down.

## Prerequisites (macOS / zsh)

- Docker Desktop
- kind
- kubectl
- jq (optional, for prettier JSON): `brew install jq`

If you use Homebrew you can install: `brew install kind kubectl jq`.

## Quick start

1. Build local images

```bash
cd /path/to/local_lab
make build-images
```

2. Create (or reuse) a kind cluster

```bash
make kind-create
```

3. Load local images into kind

```bash
make load-images-verify
# or: make load-images
```

4. Deploy k8s manifests

```bash
kubectl apply -k k8s/
```

5. Port-forward services to view locally

```bash
# Prometheus UI
kubectl port-forward svc/prometheus 9090:9090 &
# NGINX (reports)
kubectl port-forward svc/rightsizer-nginx 8080:80 &
```

Open in your browser:

- Prometheus: http://localhost:9090
- Reports: http://localhost:8080/latest/ and http://localhost:8080/smoke/

Note: a request to `http://localhost:8080/` may return `403 Forbidden` because directory listing is disabled. Use the specific report paths above.

## Verify Prometheus and metrics

- Check Prometheus responds (GET, not HEAD):

```bash
curl -s http://localhost:9090 | sed -n '1,6p'
```

- Query a sample metric:

```bash
curl -s "http://localhost:9090/api/v1/query?query=DCGM_FI_DEV_GPU_UTIL" | jq .
```

## Run the collector or smoke test

- Trigger the collector once (runs the same logic as the CronJob):

```bash
kubectl create job --from=cronjob/rightsizer-cron rightsizer-manual-$(date +%s)
kubectl logs -f job/$(kubectl get jobs -o jsonpath='{.items[-1].metadata.name}')
```

- Run the smoke-check job (small validation):

```bash
kubectl create job --from=job/rightsizer-smoke-check rightsizer-smoke-$(date +%s)
kubectl logs -f job/$(kubectl get jobs -o jsonpath='{.items[-1].metadata.name}')
```

After the jobs complete, view smoke outputs at:

- http://localhost:8080/smoke/
- http://localhost:8080/smoke/status.txt

## Switch dcgm-mock fixture (quick iteration)

You can change which fixture `dcgm-mock` serves without rebuilding the image:

```bash
./scripts/switch-fixture.sh low
# or: ./scripts/switch-fixture.sh idle
```

This patches the `dcgm-mock` Deployment's `DCGM_FIXTURE` env var.

## Teardown (clean local environment)

1) Stop port-forwards (on macOS / zsh):

```bash
ps aux | grep 'kubectl port-forward' | grep -v grep
# kill <PID>
# or
pkill -f 'kubectl port-forward'
```

2) Remove k8s resources applied by this lab:

```bash
kubectl delete -k k8s/
```

3) Optionally delete all jobs and pods (force):

```bash
kubectl delete job --all
kubectl delete pod --all --grace-period=0 --force || true
```

4) Delete the kind cluster:

```bash
kind delete cluster --name rightsizer-kind
```

5) Optionally remove local images:

```bash
docker rmi rightsizer-local/dcgm-mock:latest rightsizer-local/rightsizer-collector:latest rightsizer-local/rightsizer-nginx:latest || true
```

## Notes

- Reports are written to a hostPath PV mounted at `/reports` in the cluster and served by nginx; check `k8s/storage/pv-pvc.yaml` for details.
- If you encounter `ImagePullBackOff`, re-run `make load-images-verify` to ensure images are loaded into the kind node.
- For deterministic testing, edit files in `dcgm-mock/fixtures/` and rebuild/reload the `dcgm-mock` image.

## Troubleshooting

- If Prometheus `curl -I` returns `405 Method Not Allowed` use a GET instead.
- If nginx returns `403` for `/`, open `/latest/` or `/smoke/` directly.

---

That's it — the README is intentionally compact and action-oriented. If you'd like, I can add a one-line badge or a tiny diagram, or create a `scripts/start-all.sh` that runs the sequence automatically.
