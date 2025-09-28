# Rightsizer Local Test Lab

This workspace scaffolds a lightweight local environment to develop and test a Rightsizer Collector using:

- kind (single-node) Kubernetes cluster
- Prometheus (single pod, short retention)
- DCGM-mock server that exposes Prometheus-style GPU metrics at `/metrics`
- Rightsizer collector (Job/CronJob) that queries Prometheus and writes an HTML report to `/reports/latest`
- An optional NGINX deployment to serve the reports from the PVC


Quick steps (macOS / zsh):

1. Build images locally (or change IMAGE_PREFIX in `Makefile`):

```bash
cd new-rightsizer-local
make build-images
```

2. Create a kind single-node cluster:

```bash
make kind-create
```

3. Load built images into kind (run after cluster is ready):

```bash
make load-images
```

Tip: to avoid intermittent ImagePullBackOff when re-running the pipeline, use the new verification target which loads images and checks they exist inside the kind node:

```bash
make load-images-verify
```

`make load-images-verify` will run the same loads as `make load-images` and then confirm the images are present inside containerd on the kind node. If verification fails it will print helpful remediation steps.

4. Apply Kubernetes manifests (this will create StorageClass/PV/PVC, Prometheus, dcgm-mock, collector CronJob, and nginx):

```bash
kubectl apply -k k8s/
```

5. Verify Prometheus and dcgm-mock are running:

```bash
kubectl get pods -l app=prometheus
kubectl get pods -l app=dcgm-mock
kubectl port-forward svc/prometheus 9090:9090 &
```

Open http://localhost:9090 and use the expression `DCGM_FI_DEV_GPU_UTIL` to inspect metrics.

6. Rotate fixtures on dcgm-mock (optional)

You can change the fixture the mock serves by setting the `DCGM_FIXTURE` env var on the Deployment, or by curling the `/metrics?f=...` path directly from inside the cluster. Examples: `idle`, `low`, `bursty`, `mem`.

7. Trigger the collector once (or wait for CronJob):

```bash
kubectl create job --from=cronjob/rightsizer-cron rightsizer-manual-$(date +%s)
kubectl logs -f job/rightsizer-run-once
```

8. Serve reports with nginx and view them locally:

```bash
kubectl port-forward svc/rightsizer-nginx 8080:80
# open http://localhost:8080/
```

Smoke validation
----------------

After deploying, you can run the included smoke Job which:
- pulls the first lines of `/metrics` from `dcgm-mock`
- queries Prometheus for `DCGM_FI_DEV_GPU_UTIL`
- writes the results to the reports PVC under `/reports/smoke`

Run it with:

```bash
kubectl create job --from=job/rightsizer-smoke-check rightsizer-smoke-$(date +%s)
kubectl logs -f job/rightsizer-smoke-check
```

Then view the files via nginx (after port-forward) at `/smoke/`.

Verification & expected metrics names:

- GPU utilization: `DCGM_FI_DEV_GPU_UTIL{gpu="<id>"}`
- FB memory used: `DCGM_FI_DEV_FB_USED{gpu="<id>"}`
- FB memory total: `DCGM_FI_DEV_FB_TOTAL{gpu="<id>"}`

If you want to test deterministic conditions, edit the files under `dcgm-mock/fixtures/` then rebuild and reload the image or point Prometheus directly to the mock's pod IP (for fast iteration).

Fixture switching helper:

```bash
./scripts/switch-fixture.sh low
```



Notes:
- The mock server includes fixtures for idle, low, bursty and memory-heavy workloads under `dcgm-mock/fixtures/`.
- For persistence we use a hostPath-backed PersistentVolume and a PVC mounted at `/reports` for the collector and nginx.
- This repo intentionally keeps things simple (single-pod Prometheus, static PV) to be lightweight for local development.

See `Makefile` for convenience targets.
