#!/usr/bin/env python3
import os
import requests
from datetime import datetime
import json
import time
import logging
import sys

PROM_URL = os.environ.get('PROMETHEUS_URL', 'http://prometheus:9090')
# Allow overriding report path for local testing
REPORT_PATH = os.environ.get('REPORT_PATH', '/reports/latest')


# Configure root logger to output to stdout (useful inside k8s and locally)
def configure_logging():
  root = logging.getLogger()
  if root.handlers:
    return
  handler = logging.StreamHandler(stream=sys.stdout)
  fmt = '%(asctime)s %(levelname)s %(name)s: %(message)s'
  handler.setFormatter(logging.Formatter(fmt))
  root.setLevel(logging.INFO)
  root.addHandler(handler)


LOGGER = logging.getLogger('collector')


def query(metric, timeout=10, retries=2, backoff=1.0):
  """Query Prometheus with a timeout and simple retry/backoff.

  Returns the parsed JSON on success or raises the last exception.
  """
  last_exc = None
  for attempt in range(1, retries + 1):
    try:
      r = requests.get(f"{PROM_URL}/api/v1/query", params={"query": metric}, timeout=timeout)
      r.raise_for_status()
      return r.json()
    except Exception as e:
      last_exc = e
      if attempt < retries:
        time.sleep(backoff * attempt)
        continue
      raise


def make_html(report_path, metrics_data):
  os.makedirs(report_path, exist_ok=True)
  now = datetime.utcnow().isoformat() + 'Z'

  # build rows and chart data with nicer labels
  rows = []
  chart_labels = []
  chart_values = []

  for m, res in metrics_data.items():
    if isinstance(res, dict) and res.get('status') == 'success':
      result = res.get('data', {}).get('result', [])
      if result:
        raw_val = result[0]['value'][1]
        try:
          val = float(raw_val)
        except Exception:
          # keep non-numeric values as-is so the report shows them
          val = raw_val
        metric_labels = result[0].get('metric', {})
        # friendly label: prefer gpu label if present
        friendly = metric_labels.get('gpu') or metric_labels.get('instance') or m
        rows.append((m, metric_labels, val, friendly))
        chart_labels.append(friendly)
        chart_values.append(val)
      else:
        rows.append((m, {}, 'no-data', m))
    else:
      rows.append((m, {}, res, m))

  def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

  html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Rightsizer Report</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; margin: 20px; color:#222 }}
  table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }}
  th, td {{ border: 1px solid #eee; padding: 10px; vertical-align: top; }}
  th {{ background: #fafafa; text-align: left; font-weight: 600; color:#333 }}
  pre {{ margin:0; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, 'Courier New', monospace; font-size: 12px; background:#fff }}
  .label-list {{ list-style:none; margin:0; padding:0 }}
  .label-list li {{ display:inline-block; background:#f1f5f9; margin:2px 4px; padding:4px 8px; border-radius:4px; font-size:12px }}
  </style>
</head>
<body>
  <h1>Rightsizer Report</h1>
  <p>Generated: {now}</p>

  <h2>Metrics</h2>
  <table>
  <thead><tr><th>Query</th><th>Labels</th><th style="width:120px">Value</th></tr></thead>
  <tbody>
"""

  for q, labels_dict, v, friendly in rows:
    if isinstance(v, float):
      value_str = f"{v:.3f}"
    else:
      value_str = esc(v)

    # render labels as pill list
    if isinstance(labels_dict, dict) and labels_dict:
      labels_html = '<ul class="label-list">' + ''.join(f"<li>{esc(k)}: {esc(v)}</li>" for k, v in labels_dict.items()) + '</ul>'
    else:
      labels_html = ''

    html += f"    <tr><td><pre>{esc(q)}</pre></td><td>{labels_html}</td><td>{value_str}</td></tr>\n"

  html += """
  </tbody>
  </table>

  <h2>Chart</h2>
  <canvas id="metricsChart" width="600" height="200"></canvas>
  <script>
  const ctx = document.getElementById('metricsChart').getContext('2d');
  const chart = new Chart(ctx, {
    type: 'bar',
    data: {
    labels: %s,
    datasets: [{
      label: 'Metric value',
      data: %s,
      backgroundColor: 'rgba(54, 162, 235, 0.8)',
      borderColor: 'rgba(54, 162, 235, 1)',
      borderWidth: 1
    }]
    },
    options: {
    responsive: true,
    maintainAspectRatio: false,
    scales: { y: { beginAtZero: true } }
    }
  });
  </script>

</body>
</html>""" % (json.dumps(chart_labels), json.dumps(chart_values))

  with open(os.path.join(report_path, 'index.html'), 'w') as f:
    f.write(html)
  LOGGER.info('Wrote report to %s', os.path.join(report_path, 'index.html'))


def build_report():
  metrics = ['avg_over_time(DCGM_FI_DEV_GPU_UTIL[5m])']
  results = {}
  for m in metrics:
    try:
      LOGGER.info('Querying Prometheus for: %s', m)
      res = query(m)
      results[m] = res
      LOGGER.debug('Result for %s: %s', m, json.dumps(res)[:200])
    except Exception as e:
      LOGGER.exception('Query failed for %s', m)
      results[m] = {'error': str(e)}
  return results


def main():
  configure_logging()
  LOGGER.info('Starting collector')
  report_path = REPORT_PATH
  metrics_data = build_report()
  make_html(report_path, metrics_data)
  LOGGER.info('Collector finished')


if __name__ == '__main__':
  main()

