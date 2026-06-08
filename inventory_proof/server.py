from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import urlparse

from .alerts import build_alerts
from .forecast import build_reorder_plan
from .ops_brief import operational_alerts


class DashboardHandler(BaseHTTPRequestHandler):
    db_path = Path("inventory.sqlite")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/plan":
            self._json([plan.to_dict() for plan in build_reorder_plan(self.db_path)])
        elif parsed.path == "/api/alerts":
            self._json(build_alerts(self.db_path))
        elif parsed.path == "/api/ops-alerts":
            self._json(operational_alerts(self.db_path))
        elif parsed.path in {"/", "/dashboard"}:
            self._html(render_dashboard())
        else:
            self.send_error(404, "Not found")

    def log_message(self, format: str, *args) -> None:
        return

    def _json(self, payload: object) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, body: str) -> None:
        encoded = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def run_dashboard(db_path: str | Path, host: str = "127.0.0.1", port: int = 8787) -> None:
    DashboardHandler.db_path = Path(db_path)
    server = ThreadingHTTPServer((host, port), DashboardHandler)
    print(f"Inventory dashboard: http://{host}:{port}")
    server.serve_forever()


def render_dashboard() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Inventory Proof Dashboard</title>
  <style>
    :root { color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    body { margin: 0; background: #f6f7f9; color: #17202a; }
    header { background: #ffffff; border-bottom: 1px solid #d9dee5; padding: 20px 28px; }
    h1 { font-size: 24px; margin: 0 0 6px; letter-spacing: 0; }
    main { max-width: 1180px; margin: 0 auto; padding: 24px; }
    .metrics { display: grid; grid-template-columns: repeat(4, minmax(140px, 1fr)); gap: 12px; margin-bottom: 18px; }
    .metric, .panel { background: #fff; border: 1px solid #d9dee5; border-radius: 8px; padding: 16px; }
    .metric b { display: block; font-size: 26px; margin-top: 6px; }
    table { width: 100%; border-collapse: collapse; background: #fff; border: 1px solid #d9dee5; }
    th, td { padding: 11px 12px; border-bottom: 1px solid #e7ebf0; text-align: left; font-size: 14px; }
    th { background: #eef2f6; font-size: 12px; text-transform: uppercase; color: #46515f; }
    .status { font-weight: 700; }
    .ORDER_NOW { color: #b42318; }
    .ORDER_SOON { color: #b54708; }
    .OK { color: #087443; }
    .WATCH { color: #175cd3; }
    .alerts { display: grid; gap: 10px; margin: 18px 0; }
    .alert { border-left: 4px solid #175cd3; background: #fff; border-radius: 8px; padding: 12px 14px; }
    .alert.critical { border-left-color: #b42318; }
    .alert.warning { border-left-color: #b54708; }
    @media (max-width: 760px) {
      main { padding: 14px; }
      .metrics { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
      table { display: block; overflow-x: auto; white-space: nowrap; }
    }
  </style>
</head>
<body>
  <header>
    <h1>Inventory Proof Dashboard</h1>
    <div>Ledger-backed stock, reorder planning, and action alerts.</div>
  </header>
  <main>
    <section class="metrics">
      <div class="metric">SKUs<b id="m-skus">0</b></div>
      <div class="metric">Order Now<b id="m-now">0</b></div>
      <div class="metric">Order Soon<b id="m-soon">0</b></div>
      <div class="metric">Watch<b id="m-watch">0</b></div>
    </section>
    <section id="alerts" class="alerts"></section>
    <section class="panel">
      <table>
        <thead>
          <tr><th>SKU</th><th>Name</th><th>Stock</th><th>Daily Use</th><th>Demand</th><th>Stockout</th><th>Reorder By</th><th>Suggested Order</th><th>Status</th></tr>
        </thead>
        <tbody id="rows"></tbody>
      </table>
    </section>
  </main>
  <script>
    async function load() {
      const [plan, alerts, opsAlerts] = await Promise.all([
        fetch('/api/plan').then(r => r.json()),
        fetch('/api/alerts').then(r => r.json()),
        fetch('/api/ops-alerts').then(r => r.json())
      ]);
      document.getElementById('m-skus').textContent = plan.length;
      document.getElementById('m-now').textContent = plan.filter(p => p.status === 'ORDER_NOW').length;
      document.getElementById('m-soon').textContent = plan.filter(p => p.status === 'ORDER_SOON').length;
      document.getElementById('m-watch').textContent = plan.filter(p => p.status === 'WATCH').length;
      const allAlerts = alerts.concat(opsAlerts);
      document.getElementById('alerts').innerHTML = allAlerts.map(a => `<div class="alert ${a.severity}"><strong>${a.severity.toUpperCase()}</strong> ${a.message}</div>`).join('');
      document.getElementById('rows').innerHTML = plan.map(p => `<tr>
        <td>${p.sku}</td><td>${p.name}</td><td>${p.stock_on_hand} ${p.unit}</td><td>${p.daily_usage}</td>
        <td>${p.upcoming_demand}</td><td>${p.projected_stockout_date || '-'}</td><td>${p.reorder_by_date || '-'}</td>
        <td>${p.reorder_quantity} ${p.unit}</td><td class="status ${p.status}">${p.status}</td>
      </tr>`).join('');
    }
    load();
    setInterval(load, 30000);
  </script>
</body>
</html>"""
