"""Dashboard runtime cho Day 13 Observability Lab.

Chạy ``python scripts/dashboard.py`` rồi mở http://127.0.0.1:8501.
Trang không dùng thư viện ngoài: trình duyệt đọc JSONL từ endpoint local, tự làm mới
mỗi 30 giây và hiển thị sáu panel theo config/dashboard.yaml.
"""

from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = REPO_ROOT / "data" / "logs.jsonl"


PAGE = r"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Day 13 AI Observability Dashboard</title>
  <style>
    :root { color-scheme: dark; --bg:#08111f; --card:#101d31; --muted:#9fb0c8; --text:#edf5ff; --ok:#55d6a6; --bad:#ff7272; --line:#233652; --blue:#70b8ff; --amber:#ffc65a; }
    * { box-sizing: border-box; } body { margin:0; background:var(--bg); color:var(--text); font-family:Inter,Segoe UI,Arial,sans-serif; }
    header { padding:28px max(24px,calc((100vw - 1280px)/2)); border-bottom:1px solid var(--line); display:flex; justify-content:space-between; gap:16px; align-items:end; }
    h1 { margin:0; font-size:25px; } .subtitle { color:var(--muted); margin-top:7px; } .meta { text-align:right; color:var(--muted); font-size:14px; line-height:1.65; }
    main { max-width:1280px; margin:auto; padding:24px; } .grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:18px; }
    .panel { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:18px; min-height:270px; }
    .panel-head { display:flex; justify-content:space-between; gap:12px; align-items:start; } h2 { font-size:16px; margin:0; } .unit { color:var(--muted); font-size:13px; margin-top:5px; }
    .threshold { white-space:nowrap; font-size:12px; font-weight:600; border:1px solid var(--line); border-radius:999px; padding:5px 8px; color:var(--ok); }
    .threshold.bad { color:var(--bad); border-color:var(--bad); } .metric { font-size:29px; font-weight:700; margin:18px 0 2px; } .detail { color:var(--muted); font-size:13px; }
    svg { width:100%; height:132px; margin-top:12px; overflow:visible; } .axis { stroke:#38506f; stroke-width:1; } .line { fill:none; stroke:var(--blue); stroke-width:3; stroke-linejoin:round; stroke-linecap:round; } .warn { stroke:var(--amber); stroke-dasharray:5 4; stroke-width:1.5; }
    .bars { display:flex; height:128px; gap:10px; align-items:end; padding-top:8px; border-bottom:1px solid #38506f; } .bar { background:linear-gradient(#70b8ff,#427db8); min-width:18px; flex:1; border-radius:4px 4px 0 0; position:relative; } .bar span { position:absolute; bottom:-20px; width:100%; color:var(--muted); font-size:10px; text-align:center; }
    .split { display:grid; grid-template-columns:1fr 1fr; gap:20px; } .legend { color:var(--muted); font-size:12px; margin-top:10px; } .dot { display:inline-block; width:9px; height:9px; border-radius:50%; margin:0 4px 0 10px; } .in { background:#70b8ff }.out {background:#55d6a6}
    .empty { color:var(--muted); padding-top:50px; text-align:center; } @media(max-width:720px) { header { display:block; } .meta{text-align:left;margin-top:12px}.grid{grid-template-columns:1fr}.split{grid-template-columns:1fr} }
  </style>
</head>
<body>
  <header><div><h1>Day 13 — AI Observability</h1><div class="subtitle">Nguồn dữ liệu: <code>data/logs.jsonl</code></div></div><div class="meta">Time range: <strong>60 phút</strong><br>Auto refresh: <strong>30 giây</strong><br><span id="updated">Đang tải…</span></div></header>
  <main><div id="dashboard" class="grid"></div></main>
<script>
const WINDOW_MS=60*60*1000;
const fmt=n=>new Intl.NumberFormat('en-US',{maximumFractionDigits:2}).format(n);
const percentile=(values,p)=>{if(!values.length)return 0;let v=[...values].sort((a,b)=>a-b);let i=Math.max(0,Math.min(v.length-1,Math.round(p/100*v.length+.5)-1));return v[i]};
const isRecent=(row, now)=>!row.ts||now-new Date(row.ts).getTime()<=WINDOW_MS;
const svgLine=(values, threshold)=>{ if(!values.length)return '<div class="empty">Chưa có dữ liệu trong 60 phút gần nhất</div>'; const max=Math.max(...values,threshold||0,1), w=500,h=120; const points=values.map((v,i)=>`${i*(w/Math.max(values.length-1,1))},${h-(v/max*h)}`).join(' '); const y=threshold==null?'':h-(threshold/max*h); return `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none"><line class="axis" x1="0" y1="${h}" x2="${w}" y2="${h}"/>${threshold==null?'':`<line class="warn" x1="0" y1="${y}" x2="${w}" y2="${y}"/>`}<polyline class="line" points="${points}"/></svg>`; };
const bars=(items, color='')=>{if(!items.length)return '<div class="empty">Chưa có dữ liệu</div>'; const max=Math.max(...items.map(x=>x.value),1); return `<div class="bars">${items.map(x=>`<div class="bar" style="height:${Math.max(3,x.value/max*100)}%;${color?`background:${color}`:''}"><span>${x.label}</span></div>`).join('')}</div>`};
const card=(title,unit,threshold,failed,metric,detail,chart)=>`<section class="panel"><div class="panel-head"><div><h2>${title}</h2><div class="unit">${unit}</div></div><span class="threshold ${failed?'bad':''}">${threshold}</span></div><div class="metric">${metric}</div><div class="detail">${detail}</div>${chart}</section>`;
function perMinute(rows, value){ const buckets={}; rows.forEach(r=>{const k=(r.ts||'').slice(0,16); buckets[k]=(buckets[k]||0)+value(r);}); return Object.entries(buckets).map(([label,value])=>({label:label.slice(11),value})); }
function render(rows){
  const now=Date.now(), recent=rows.filter(r=>isRecent(r,now)), received=recent.filter(r=>r.event==='request_received'), sent=recent.filter(r=>r.event==='response_sent'), failed=recent.filter(r=>r.event==='request_failed');
  const latency=sent.map(r=>Number(r.latency_ms)||0), costs=sent.map(r=>Number(r.cost_usd)||0), tokensIn=sent.map(r=>Number(r.tokens_in)||0), tokensOut=sent.map(r=>Number(r.tokens_out)||0), quality=sent.map(r=>Number(r.quality_score)||0);
  const p50=percentile(latency,50),p95=percentile(latency,95),p99=percentile(latency,99), errorRate=received.length?failed.length/received.length*100:0, totalCost=costs.reduce((a,b)=>a+b,0), qualityAvg=quality.length?quality.reduce((a,b)=>a+b,0)/quality.length:0;
  const traffic=perMinute(received,()=>1), costByMinute=perMinute(sent,r=>Number(r.cost_usd)||0);
  const errors={};failed.forEach(r=>errors[r.error_type||'Unknown']=(errors[r.error_type||'Unknown']||0)+1);
  document.querySelector('#dashboard').innerHTML = [
    card('Latency percentiles','ms','P95 ≤ 3000 ms',p95>3000,`${fmt(p95)} ms`,`P50 ${fmt(p50)} · P99 ${fmt(p99)}`,svgLine(latency,3000)),
    card('Request traffic','requests / minute','≥ 1 req/phút',traffic.length>0 && traffic[traffic.length-1].value<1,`${received.length} requests`,`${traffic.length?fmt(traffic[traffic.length-1].value):0} request/phút (mới nhất)`,bars(traffic)),
    card('Error rate and breakdown','percent','Error rate ≤ 2%',errorRate>2,`${fmt(errorRate)}%`,`${failed.length} failed / ${received.length} received`,bars(Object.entries(errors).map(([label,value])=>({label,value}),'linear-gradient(#ff9a9a,#b84b4b)'))),
    card('Cost over time','USD','Total ≤ $2.50',totalCost>2.5,`$${fmt(totalCost)}`,`Tổng trong 60 phút`,svgLine(costByMinute.map(x=>x.value),2.5)),
    card('Input and output tokens','tokens','Total ≤ 50,000',tokensIn.reduce((a,b)=>a+b,0)+tokensOut.reduce((a,b)=>a+b,0)>50000,`${fmt(tokensIn.reduce((a,b)=>a+b,0)+tokensOut.reduce((a,b)=>a+b,0))}`,`Input ${fmt(tokensIn.reduce((a,b)=>a+b,0))} · Output ${fmt(tokensOut.reduce((a,b)=>a+b,0))}`,`<div class="split"><div>${svgLine(tokensIn,null)}<div class="legend"><i class="dot in"></i>Input tokens</div></div><div>${svgLine(tokensOut,null)}<div class="legend"><i class="dot out"></i>Output tokens</div></div></div>`),
    card('Quality proxy','score 0–1','Mean ≥ 0.75',qualityAvg<0.75,fmt(qualityAvg),`${quality.length} response có quality score`,svgLine(quality,.75))
  ].join('');
  document.querySelector('#updated').textContent=`Cập nhật: ${new Date().toLocaleString('vi-VN')} · ${recent.length} log events`;
}
async function load(){try{const r=await fetch('/api/logs',{cache:'no-store'});render(await r.json())}catch(e){document.querySelector('#dashboard').innerHTML='<div class="empty">Không thể đọc data/logs.jsonl: '+e.message+'</div>'}}
load(); setInterval(load,30000);
</script></body></html>"""


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/", "/index.html"}:
            self._send(HTTPStatus.OK, "text/html; charset=utf-8", PAGE.encode("utf-8"))
        elif self.path == "/api/logs":
            records = []
            if LOG_PATH.exists():
                for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            self._send(HTTPStatus.OK, "application/json; charset=utf-8", json.dumps(records).encode())
        else:
            self._send(HTTPStatus.NOT_FOUND, "text/plain; charset=utf-8", b"Not found")

    def _send(self, status: HTTPStatus, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format: str, *_args: object) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Day 13 runtime dashboard")
    parser.add_argument("--port", type=int, default=8501)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), DashboardHandler)
    print(f"Dashboard: http://127.0.0.1:{args.port}")
    print("Nguồn dữ liệu: data/logs.jsonl | refresh: 30 giây | time range: 60 phút")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
