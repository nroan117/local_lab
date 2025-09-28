Viewing the Rightsizer HTML report

- Ensure the collector has generated a report in the PVC (`/reports/latest/index.html`).
- Use the helper script to fetch and open the report locally:

```bash
chmod +x scripts/fetch-report.sh
./scripts/fetch-report.sh
```

- Or port-forward the nginx service and open in your browser:

```bash
kubectl port-forward svc/rightsizer-nginx 8080:80 &
open http://localhost:8080/latest/
```

Notes:
- The report now renders a table and an embedded Chart.js bar chart.
- For time-series plots we can extend the collector to query `query_range` and plot lines instead of bars.
