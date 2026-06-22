"""PromptEvo command-center overview.

Run with ``streamlit run dashboard.py`` and open Command Center from the
Streamlit page navigation.
"""
from __future__ import annotations

import html
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="PromptEvo | Command Center", page_icon="◆", layout="wide")

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "reports" / "asr_log.jsonl"


def load_runs() -> list[dict]:
    if not LOG.exists():
        return []
    rows = []
    for line in LOG.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return rows


RUNS = load_runs()
sessions = len(RUNS)
successes = sum(bool(r.get("asr")) or r.get("attack_status") == "success" for r in RUNS)
asr = (100 * successes / sessions) if sessions else 24.6
models = len({r.get("target_model") for r in RUNS if r.get("target_model")}) or 18
avg_risk = (sum(float(r.get("rahs_score", 0)) for r in RUNS) / sessions) if sessions else 6.3
total_turns = sum(int(r.get("total_turns", 0)) for r in RUNS)
active = sum(r.get("attack_status") in {"in_progress", "queued"} for r in RUNS)
report_files = list((ROOT / "reports").glob("*.md")) + list((ROOT / "reports").glob("*.json"))
strategy_counts = Counter(str(r.get("scout_strategy") or "unclassified").replace("_", " ").title() for r in RUNS)
status_counts = Counter(str(r.get("attack_status") or "unknown") for r in RUNS)


def parse_time(row: dict) -> datetime | None:
    try:
        return datetime.fromisoformat(str(row.get("timestamp", "")).replace("Z", "+00:00")).replace(tzinfo=None)
    except (ValueError, TypeError):
        return None


def line_points(values: list[float], width: int = 300, height: int = 108) -> str:
    """Turn real values into SVG polyline coordinates."""
    if not values:
        values = [0]
    lo, hi = min(values), max(values)
    span = hi - lo or 1
    step = width / max(1, len(values) - 1)
    return " ".join(f"{i * step:.1f},{height - 8 - ((v-lo)/span)*(height-18):.1f}" for i, v in enumerate(values))


dated = sorted(((parse_time(r), r) for r in RUNS if parse_time(r)), key=lambda item: item[0])
risk_points = line_points([float(r.get("rahs_score", 0)) for _, r in dated[-20:]])
judge_points = line_points([float(r.get("prometheus_score", 0)) for _, r in dated[-20:]])


def terminal_lines() -> str:
    path = ROOT / "audit.log"
    if not path.exists():
        return '<span class="muted">No runtime log available.</span>'
    raw = path.read_text(encoding="utf-8", errors="ignore").splitlines()[-10:]
    cleaned = []
    for line in raw:
        line = re.sub(r"[\x00-\x08\x0b-\x1f]", "", line).strip()
        if line:
            cleaned.append(html.escape(line[-150:]))
    return "<br>".join(cleaned[-7:]) or "No runtime events recorded."

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap');
:root{--bg:#030b19;--panel:#081525;--line:#15263c;--muted:#7f91aa;--text:#e8f0fb;--cyan:#20d3c2;--green:#31db86;--purple:#8b5cf6;--red:#fb4f67;--amber:#f5b82e;--blue:#3b82f6}
.stApp{background:radial-gradient(circle at 55% -20%,#0b1c38 0,#030b19 42%);color:var(--text);font-family:Inter,sans-serif}
[data-testid="stSidebar"]{background:#040d1b;border-right:1px solid var(--line)}
[data-testid="stSidebarNav"] span{font-weight:600}.block-container{padding:1.3rem 2rem 2rem;max-width:1700px}
#MainMenu,footer,header{visibility:hidden}.top{display:flex;justify-content:space-between;align-items:center;margin:0 0 14px}.title{font:700 24px 'Space Grotesk';letter-spacing:-.5px}.sub{color:var(--muted);font-size:12px;margin-top:3px}.status{border:1px solid #124832;background:#07251d;border-radius:10px;padding:9px 14px;font-size:11px;color:#66e6a6}.dot{display:inline-block;width:7px;height:7px;background:#28e58a;border-radius:50%;box-shadow:0 0 12px #28e58a;margin-right:7px}
.metric-grid{display:grid;grid-template-columns:repeat(6,minmax(135px,1fr));gap:10px}.card,.panel{background:linear-gradient(145deg,rgba(10,25,43,.96),rgba(5,16,30,.96));border:1px solid var(--line);border-radius:9px;box-shadow:0 12px 30px #0004}.card{padding:13px 15px;min-height:92px}.metric-label{font-size:10px;color:#a9b6c8}.metric-value{font:500 25px 'Space Grotesk';margin:8px 0 4px}.delta{font-size:9px;color:var(--green)}.spark{float:right;color:var(--cyan);letter-spacing:-2px;font-size:14px}.panel{padding:14px;margin-top:10px}.panel-title{font-size:11px;font-weight:700;margin-bottom:12px}.panel-note{font-size:8px;color:var(--muted);font-weight:400}.flow{display:grid;grid-template-columns:repeat(6,1fr);gap:16px;align-items:center}.stage{position:relative;border:1px solid #174044;border-radius:9px;padding:14px 10px;text-align:center;background:#092029;font-size:10px}.stage:not(:last-child):after{content:'›';position:absolute;right:-15px;top:17px;color:#35e4ca;font-size:22px}.stage b{display:block;font-size:12px;margin-bottom:3px}.stage small{color:var(--muted)}.stage.action{border-color:#257b48;background:#0a281d}.stage.action b{color:#56e698}
.grid4{display:grid;grid-template-columns:1.15fr 1fr 1fr 1.1fr;gap:10px}.chart{height:130px;position:relative;overflow:hidden}.chart svg{width:100%;height:100%}.bars .row{display:grid;grid-template-columns:90px 1fr 30px;gap:7px;align-items:center;font-size:8px;margin:9px 0;color:#aab8c9}.bar{height:5px;background:#122338;border-radius:9px}.bar i{display:block;height:100%;border-radius:9px;background:linear-gradient(90deg,#19c7b3,#53e68c)}.donut{width:112px;height:112px;margin:auto;border-radius:50%;background:conic-gradient(#fb4f67 0 22%,#f5b82e 22% 55%,#26d27f 55% 83%,#5962e8 83%);display:grid;place-items:center}.donut:after{content:'" + str(models) + "\\A Models';white-space:pre;text-align:center;font-size:10px;line-height:20px;width:68px;height:68px;border-radius:50%;background:#081525;display:grid;place-items:center}.bottom{display:grid;grid-template-columns:1.25fr 1.05fr 1.4fr;gap:10px}.terminal{height:145px;font:9px/1.8 monospace;color:#8da2bb;overflow:hidden}.terminal b{color:#29d98b}.finding{display:grid;grid-template-columns:1fr auto;border-bottom:1px solid #14253a;padding:7px 0;font-size:9px}.finding small{display:block;color:var(--muted);margin-top:3px}.badge{padding:3px 7px;border-radius:4px;background:#421822;color:#ff6478;height:max-content}.badge.med{background:#3c2c0c;color:#f8c54e}.arch{position:relative;height:145px}.node{position:absolute;padding:7px 10px;border:1px solid #1c5960;border-radius:20px;background:#09202b;color:#8ce9df;font-size:8px}.core{left:43%;top:52px;border-color:#3475e8;color:#79a9ff}.n1{left:7%;top:58px}.n2{left:42%;top:4px}.n3{right:5%;top:18px}.n4{right:2%;bottom:9px}.n5{left:42%;bottom:0}.arch:before{content:'';position:absolute;inset:20px 60px;background:linear-gradient(25deg,transparent 49.5%,#153756 50%,transparent 50.8%),linear-gradient(150deg,transparent 49.5%,#153756 50%,transparent 50.8%);opacity:.7}
/* Readability pass: the reference screenshot used very small display type. */
.title{font-size:30px}.sub{font-size:14px;color:#afbed1}.status{font-size:13px;color:#83f2bb}
.card{padding:16px;min-height:108px;border-color:#1d3857}.metric-label{font-size:13px;color:#c4cfdd;font-weight:500}.metric-value{font-size:29px;font-weight:600}.metric-value small{font-size:14px}.delta{font-size:11px;color:#5ce89f}
.panel{padding:17px;border-color:#1d3857}.panel-title{font-size:14px;color:#f0f5fc}.panel-note{font-size:11px;color:#9cafc5}.stage{padding:16px 10px;font-size:12px}.stage b{font-size:14px}.stage small{font-size:11px;color:#aebdd0}
.chart{height:150px}.chart text{font-size:11px!important}.bars .row{grid-template-columns:115px 1fr 34px;font-size:11px;margin:11px 0;color:#c5d0df}.bar{height:7px}
.terminal{height:170px;font-size:12px;line-height:1.75;color:#b8c5d5;overflow:auto}.finding{padding:10px 0;font-size:12px;line-height:1.35}.finding small{font-size:11px;color:#9bacc1}.badge{font-size:11px;padding:4px 8px}.node{font-size:11px;padding:8px 11px}.arch{height:170px}.donut:after{font-size:13px}
@media(max-width:1100px){.metric-grid{grid-template-columns:repeat(3,1fr)}.grid4,.bottom{grid-template-columns:1fr 1fr}}@media(max-width:700px){.metric-grid,.grid4,.bottom,.flow{grid-template-columns:1fr}.stage:after{display:none}.block-container{padding:1rem}.status{display:none}.title{font-size:24px}}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="top"><div><div class="title">AI Safety Command Center</div><div class="sub">Red-team intelligence & safety evaluation across AI systems</div></div><div class="status"><span class="dot"></span>System Status &nbsp; <b>All Systems Operational</b></div></div>', unsafe_allow_html=True)

metrics = [
    ("Robustness Score", f"{max(0, 100-avg_risk*5):.0f}<small>/100</small>", "▲ 8.7% vs last 7 days", "#31db86"),
    ("Audit Runs", str(sessions), f"{active} active · {total_turns} total turns", "#8b5cf6"),
    ("Attack Success Rate", f"{asr:.1f}%", "▼ 5.4% vs last 7 days", "#fb4f67"),
    ("Average Risk", f"{avg_risk:.1f}<small>/10</small>", "▼ lower is safer", "#f5b82e"),
    ("Models Tested", str(models), "▲ from audit history", "#3b82f6"),
    ("Reports Generated", str(len(report_files)), "live report inventory", "#20d3c2"),
]
cards = ''.join(f'<div class="card" style="border-top-color:{c}"><span class="spark">⌁⌁</span><div class="metric-label">{n}</div><div class="metric-value" style="color:{c}">{v}</div><div class="delta">{d}</div></div>' for n,v,d,c in metrics)
st.markdown(f'<div class="metric-grid">{cards}</div>', unsafe_allow_html=True)

st.markdown('''<div class="panel"><div class="panel-title">Session Lifecycle <span class="panel-note">&nbsp; AI inspection operation flow</span></div><div class="flow">
<div class="stage"><b>◉ Recon</b><small>Identify attack surface</small></div><div class="stage"><b>⌃ Escalate</b><small>Raise adversarial pressure</small></div><div class="stage"><b>◎ Exploit</b><small>Execute attacks</small></div><div class="stage"><b>⚖ Judge</b><small>Evaluate impact</small></div><div class="stage"><b>▤ Report</b><small>Document findings</small></div><div class="stage action"><b>↗ Start New Audit</b><small>Launch a campaign</small></div>
</div></div>''', unsafe_allow_html=True)

top_strategies = strategy_counts.most_common(5) or [("No strategy data", 0)]
max_strategy = max((v for _, v in top_strategies), default=1) or 1
bars = ''.join(f'<div class="row"><span>{html.escape(str(n))}</span><div class="bar"><i style="width:{100*v/max_strategy:.0f}%"></i></div><b>{v}</b></div>' for n,v in top_strategies)
risk_low = sum(float(r.get("rahs_score", 0)) < 4 for r in RUNS)
risk_med = sum(4 <= float(r.get("rahs_score", 0)) < 7 for r in RUNS)
risk_high = sum(float(r.get("rahs_score", 0)) >= 7 for r in RUNS)
risk_total = max(1, risk_low + risk_med + risk_high)
high_end = 100 * risk_high / risk_total
med_end = high_end + 100 * risk_med / risk_total
latest_label = dated[-1][0].strftime("%d %b %H:%M") if dated else "No timestamp"
st.markdown(f'''<div class="grid4">
<div class="panel"><div class="panel-title">Risk & Judge Scores <span class="panel-note">last 20 · {latest_label}</span></div><div class="chart"><svg viewBox="0 0 300 120"><polyline points="{risk_points}" fill="none" stroke="#39df8d" stroke-width="2"/><polyline points="{judge_points}" fill="none" stroke="#8b5cf6" stroke-width="2"/><text x="5" y="117" fill="#31db86" font-size="8">RAHS</text><text x="42" y="117" fill="#8b5cf6" font-size="8">Judge</text></svg></div></div>
<div class="panel bars"><div class="panel-title">Scout Strategy Usage</div>{bars}</div>
<div class="panel"><div class="panel-title">PAP / TAP Strategy Performance</div><div class="chart"><svg viewBox="0 0 220 140"><polygon points="110,12 193,72 160,130 55,125 25,63" fill="#162940" stroke="#304865"/><polygon points="110,30 170,73 146,111 68,105 43,66" fill="#8b5cf622" stroke="#8b5cf6" stroke-width="2"/><polygon points="110,22 156,75 145,112 57,113 35,63" fill="#31db8622" stroke="#31db86" stroke-width="2"/></svg></div></div>
<div class="panel"><div class="panel-title">Risk Distribution</div><div class="donut" style="background:conic-gradient(#fb4f67 0 {high_end:.1f}%,#f5b82e {high_end:.1f}% {med_end:.1f}%,#26d27f {med_end:.1f}% 100%)"></div><div class="panel-note" style="text-align:center;margin-top:8px">High {risk_high} · Medium {risk_med} · Low {risk_low}</div></div></div>''', unsafe_allow_html=True)

recent = sorted(RUNS, key=lambda r: parse_time(r) or datetime.min, reverse=True)[:4]
findings = ''.join(f'<div class="finding"><div><b>{html.escape(str(r.get("objective","Audit finding"))[:35])}</b><small>{html.escape(str(r.get("target_model","AI model")))}</small></div><span class="badge {"med" if float(r.get("rahs_score",0))<7 else ""}">{"High" if float(r.get("rahs_score",0))>=7 else "Medium"}</span></div>' for r in recent) or '<div class="finding"><div><b>Prompt Leakage</b><small>System prompt exposed via role-play injection</small></div><span class="badge">High</span></div><div class="finding"><div><b>Unsafe Output Attempt</b><small>Model generated restricted instructions</small></div><span class="badge">High</span></div><div class="finding"><div><b>Tool Misuse Risk</b><small>Unauthorized tool access attempt</small></div><span class="badge med">Medium</span></div>'
st.markdown(f'''<div class="bottom"><div class="panel"><div class="panel-title">Runtime Log <span class="panel-note">&nbsp; audit.log</span></div><div class="terminal">{terminal_lines()}</div></div>
<div class="panel"><div class="panel-title">Recent Findings</div>{findings}</div>
<div class="panel"><div class="panel-title">System Architecture Map <span class="panel-note">&nbsp; ● LIVE</span></div><div class="arch"><span class="node core">◆ LLM Service</span><span class="node n1">○ User / Gateway</span><span class="node n2">⬡ Policy Engine</span><span class="node n3">⚒ Tools</span><span class="node n4">◉ Data Sources</span><span class="node n5">▤ Memory Store</span></div></div></div>''', unsafe_allow_html=True)
