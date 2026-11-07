import datetime as dt
import os
from html import escape
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

# -----------------------------------------------------------------------------
# Page configuration and theme
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Strait of Hormuz | Intelligence Dashboard",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CUSTOM_CSS = """
<style>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap");

:root {
    --bg: #0b0a0c;
    --bg-2: #100d10;
    --panel: #171317;
    --panel-2: #120f13;
    --text: #f6efe9;
    --muted: #ad9f98;
    --dim: #756966;
    --border: #35292e;
    --border-hi: #64454a;
    --copper: #e8a64a;
    --coral: #ff6b61;
    --green: #4ccb8a;
    --violet: #c58be8;
    --mono: "IBM Plex Mono", ui-monospace, monospace;
    --ui: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    --display: "Space Grotesk", "Inter", sans-serif;
}

html { scroll-behavior: smooth; }
body, [class*="css"], button, input, textarea, select { font-family: var(--ui) !important; }
[data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background: var(--bg) !important;
    color: var(--text) !important;
}
[data-testid="stHeader"] { background: transparent !important; height:0 !important; }
[data-testid="stToolbar"], [data-testid="stAppDeployButton"], .stDeployButton { display:none !important; }
[data-testid="stDecoration"], [data-testid="stStatusWidget"] { display:none !important; }
.block-container { max-width: 1400px; padding: 24px 42px 72px; }
[data-testid="stMarkdownContainer"] { line-height: 1.58; }

/* Clear, persistent website navigation */
.nav-shell {
    position: sticky; top: 0; z-index: 900;
    margin: -8px -8px 24px; padding: 10px 12px 11px;
    background: rgba(11,10,12,.94);
    border: 1px solid #3a2c31; border-radius: 14px;
    box-shadow: 0 14px 36px rgba(0,0,0,.30), inset 0 1px 0 rgba(255,255,255,.035);
    backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
}
.command-brand { align-items:center; display:flex; gap:9px; color:#fff4ed; font-family:var(--mono); font-size:.78rem; font-weight:600; letter-spacing:.09em; line-height:1.05; padding:5px 2px; }
.command-mark { color:var(--copper); font-size:1.35rem; }
.command-brand small { color:#a87c71; font-size:.52rem; letter-spacing:.16em; }
.command-meta { color:var(--green); font-family:var(--mono); font-size:.62rem; line-height:1.5; padding:4px 0; text-align:right; }
.command-meta small { color:#9b8982; font-size:.56rem; }
[data-testid="stSegmentedControl"] { width:100% !important; }
[data-testid="stSegmentedControl"] > div { width:100% !important; background:#151116 !important; border:1px solid #3a2d32 !important; border-radius:10px !important; padding:3px !important; gap:3px !important; }
[data-testid="stSegmentedControl"] button {
    background:transparent !important; border:1px solid transparent !important; border-radius:7px !important;
    color:#b6a8a1 !important; font-family:var(--ui) !important; font-size:.73rem !important; font-weight:700 !important;
    min-height:34px !important; padding:7px 11px !important; transition:all .2s ease !important;
}
[data-testid="stSegmentedControl"] button:hover { background:#24191e !important; border-color:#5e4147 !important; color:#fff5ef !important; transform:translateY(-1px); }
[data-testid="stSegmentedControl"] button[aria-pressed="true"] {
    background:linear-gradient(135deg,#49282f,#2b1a20) !important; border-color:#9a5d61 !important;
    box-shadow:inset 0 -2px 0 var(--copper), 0 5px 14px rgba(0,0,0,.18) !important; color:#fff7f0 !important;
}
[data-testid="stSegmentedControl"] button p { font-size:.73rem !important; margin:0 !important; white-space:nowrap !important; }

/* Header */
.topbar { align-items:center; border-bottom:1px solid #403136; display:flex; justify-content:space-between; margin:2px 0 24px; padding:0 0 16px; }
.header-title { color:#ffd8b5 !important; font-family:var(--display); font-size:1.72rem; font-weight:800; letter-spacing:-.04em; }
.header-sub { color:#b9a69d; font-size:.9rem; margin-left:10px; }
.header-meta { color:#9d8880; font-family:var(--mono); font-size:.65rem; line-height:1.5; text-align:right; }
.live-dot { animation:livePulse 1.7s ease-in-out infinite; background:var(--green); border-radius:50%; display:inline-block; height:7px; margin:0 6px 1px 12px; width:7px; }
.live-label { color:var(--green); font-family:var(--mono); font-size:.65rem; font-weight:700; letter-spacing:.1em; }

/* Shared content */
.page-hero { border-bottom:1px solid #3a2c31; margin:4px 0 28px; padding:8px 0 22px; }
.page-kicker, .menu-hint { color:#c08c78; font-family:var(--mono); font-size:.62rem; letter-spacing:.15em; text-transform:uppercase; }
.page-title { color:#fff1e7; font-family:var(--display); font-size:clamp(2rem,4vw,3.7rem); font-weight:800; letter-spacing:-.06em; line-height:.98; margin-top:10px; }
.page-description { color:#a69a92; font-size:.9rem; line-height:1.6; margin-top:10px; max-width:760px; }
.section-title { color:#bfa69d; font-family:var(--mono); font-size:.68rem; font-weight:600; letter-spacing:.13em; margin:34px 0 14px; text-transform:uppercase; }
.icon { display:inline-flex; vertical-align:-3px; margin-right:7px; } .icon svg { height:15px; width:15px; }
.panel, .actor-card, .article-card, .quote-card, .method-card, .feed-card, .counter-card, .control-card {
    background:linear-gradient(145deg,var(--panel),var(--panel-2)); border:1px solid var(--border); border-radius:12px;
    box-shadow:0 14px 32px rgba(0,0,0,.18), inset 0 1px 0 rgba(255,235,225,.025);
}
.panel { min-height:158px; padding:18px 20px; transition:transform .2s ease,border-color .2s ease,box-shadow .2s ease; }
.panel:hover, .actor-card:hover, .article-card:hover, .counter-card:hover { border-color:var(--border-hi); transform:translateY(-3px); box-shadow:0 18px 38px rgba(0,0,0,.25); }
.panel-title { color:#bfa69d; font-size:.66rem; font-weight:800; letter-spacing:.13em; line-height:1.2; margin-bottom:13px; text-transform:uppercase; }
.card-title { color:#f4eee7; font-family:var(--display); font-size:.9rem; font-weight:700; }
.big-number { color:#f4eee7; font-family:var(--mono); font-size:1.75rem; font-weight:600; letter-spacing:-.045em; line-height:1.08; }
.big-number.red,.counter-value.red { color:var(--coral); } .big-number.amber,.counter-value.amber { color:var(--copper); } .big-number.green,.counter-value.green { color:var(--green); } .big-number.blue { color:var(--violet); }
.sub-label { color:var(--muted); font-size:.72rem; line-height:1.45; }
.mono,.big-number,.header-meta,.menu-hint,.news-meta,.timeline-date,.badge,.counter-value,.counter-label,.counter-delta,.page-kicker { font-family:var(--mono) !important; }
.metric-row { align-items:flex-start; display:flex; flex-wrap:wrap; gap:24px; } .metric-row > div { min-width:76px; }
.status-center { align-items:center; display:flex; flex-direction:column; justify-content:center; min-height:108px; text-align:center; }
.badge { border:1px solid currentColor; border-radius:999px; display:inline-block; font-size:.57rem; font-weight:800; line-height:1; padding:4px 7px; white-space:nowrap; }
.badge-critical { background:#321a1c; color:var(--coral); } .badge-high { background:#302116; color:var(--copper); } .badge-moderate { background:#14291f; color:var(--green); } .badge-info { background:#281b31; color:var(--violet); }
.map-schematic { color:var(--muted); font-family:var(--mono); font-size:.66rem; line-height:2; padding:8px 0 2px; text-align:center; }
.map-line { color:#594247; }
.data-row,.route,.news-item { border-bottom:1px solid #2b2025; } .data-row { align-items:center; display:flex; justify-content:space-between; gap:16px; padding:8px 0; font-size:.73rem; }
.route { padding:10px 0; font-size:.76rem; }
.timeline-entry { border-left:3px solid #4b3840; margin:0 0 18px 5px; padding:4px 0 8px 16px; transition:border-color .2s ease,padding-left .2s ease; }
.timeline-entry:hover { border-left-color:var(--copper); padding-left:20px; } .timeline-entry.critical { border-left-color:var(--coral); } .timeline-entry.warning { border-left-color:var(--copper); }
.timeline-meta { align-items:center; display:flex; flex-wrap:wrap; gap:6px; margin-bottom:7px; } .timeline-date { color:#756966; font-size:.66rem; } .timeline-target { color:#e7eef8; font-size:.82rem; font-weight:800; line-height:1.3; margin-bottom:4px; }
.news-item { padding:16px 4px; transition:padding-left .18s ease; } .news-item:hover { padding-left:10px; } .news-item:last-child { border-bottom:0; } .news-title { color:#eaf2fc; font-size:.88rem; font-weight:800; line-height:1.36; } .news-meta { color:#756966; font-size:.61rem; margin-top:5px; }
.actor-card { min-height:200px; padding:18px; transition:transform .2s ease,border-color .2s ease; } .actor-index { color:var(--copper); font-family:var(--mono); font-size:.62rem; } .actor-name { color:#fff1e7; font-size:1rem; font-weight:800; margin-top:25px; } .actor-rule { background:#4b3439; height:1px; margin:12px 0; } .actor-link,.article-link { color:var(--copper); font-family:var(--mono); font-size:.61rem; letter-spacing:.05em; margin-top:17px; }
.article-card { overflow:hidden; transition:transform .2s ease,border-color .2s ease; } .article-art { align-items:flex-end; display:flex; height:138px; padding:14px; position:relative; }
.art-1 { background:radial-gradient(circle at 75% 25%,#d87848,transparent 22%),linear-gradient(135deg,#472426,#191219 65%); } .art-2 { background:radial-gradient(circle at 25% 22%,#d6a055,transparent 19%),linear-gradient(135deg,#38232c,#141016 65%); } .art-3 { background:radial-gradient(circle at 65% 35%,#a96d91,transparent 24%),linear-gradient(135deg,#2c2031,#141016 65%); } .article-content { padding:15px 16px 18px; } .article-title { color:#fff1e7; font-size:.93rem; font-weight:800; line-height:1.34; margin:9px 0 8px; }
.feed-card { padding:17px 20px; } .quote-card { min-height:310px; padding:21px; } .quote-mark { color:var(--copper); font-size:4.6rem; line-height:.8; margin-top:25px; } .quote-text { color:#f3ded1; font-size:1.28rem; font-weight:600; letter-spacing:-.025em; line-height:1.32; margin:6px 0 26px; }
.method-card { min-height:164px; padding:18px; } .status-line { border-bottom:1px solid #2b2025; color:#d9c9c1; display:flex; font-family:var(--mono); font-size:.64rem; gap:8px; padding:10px 0; } .status-line span:last-child { color:#806f6b; margin-left:auto; } .status-dot { background:var(--green); border-radius:50%; height:7px; margin-top:3px; width:7px; } .status-dot.amber { background:var(--copper); } .status-dot.red { background:var(--coral); }
.counter-card { min-height:104px; padding:15px 17px; transition:transform .2s ease,border-color .2s ease; } .counter-value { font-size:1.52rem; font-weight:600; line-height:1.1; } .counter-label { color:#bfa69d; font-size:.59rem; letter-spacing:.09em; margin-top:8px; } .counter-delta { color:#766a68; font-size:.6rem; margin-top:5px; }
.control-card { min-height:280px; padding:17px 18px; } .alert-strip { align-items:center; background:#241719; border:1px solid #84484a; border-radius:9px; color:#e7b1a7; display:flex; font-family:var(--mono); font-size:.64rem; gap:10px; margin:13px 0 3px; padding:11px 14px; } .alert-strip b { color:#ff8077; letter-spacing:.08em; } .alert-strip small { color:#b97f70; margin-left:auto; } .alert-pulse { background:var(--coral); border-radius:50%; box-shadow:0 0 0 5px rgba(255,107,97,.12); height:7px; width:7px; }
.market-shell { overflow:hidden; position:relative; } .market-kpis { display:flex; flex-wrap:wrap; gap:24px; margin:4px 0 12px; } .market-kpi-value { color:var(--copper); font-family:var(--mono); font-size:1.4rem; font-weight:600; } .market-kpi-label { color:#756966; font-family:var(--mono); font-size:.57rem; letter-spacing:.08em; text-transform:uppercase; }
.analysis-rail { background:linear-gradient(145deg,#1b1518,#120f13); border:1px solid #3b2b30; border-radius:12px; height:100%; overflow:hidden; } .analysis-art { align-items:flex-end; background:radial-gradient(circle at 72% 28%,rgba(220,105,60,.8),transparent 26%),linear-gradient(135deg,#3a2021 0%,#151219 56%,#241318 100%); display:flex; height:148px; padding:16px; position:relative; } .analysis-art::before { border:1px solid rgba(248,213,172,.35); border-radius:50%; content:""; height:92px; position:absolute; right:18px; top:20px; width:92px; } .analysis-art::after { background:linear-gradient(135deg,transparent 45%,rgba(231,166,74,.72) 46%,transparent 48%); content:""; inset:0; position:absolute; } .analysis-body { padding:15px 16px 17px; } .analysis-title { color:#fff2e8; font-size:.92rem; font-weight:800; line-height:1.3; margin:10px 0 7px; }
[data-testid="stExpander"] { background:#171419; border:1px solid #3a2b30; border-radius:10px; margin-bottom:11px; } [data-testid="stExpander"] summary { color:#fff1e7 !important; font-size:.86rem !important; font-weight:700 !important; padding:11px 8px !important; }
[data-testid="stProgressBar"] { background:#2a2024; } [data-testid="stProgressBar"] > div > div { background:linear-gradient(90deg,var(--coral),var(--copper)); }
.stButton > button { background:#2b1b20; border:1px solid #6a444b; color:#fff0e9; } .stButton > button:hover { background:#47252d; border-color:#d58b78; }
.footer { color:#675a58; font-family:var(--mono); font-size:.6rem; margin-top:34px; padding:30px 0 4px; text-align:center; letter-spacing:.04em; }

/* Scroll-to-reveal: modern browsers reveal cards as they enter the viewport. */
@keyframes revealUp { from { opacity:0; transform:translateY(28px) scale(.985); filter:blur(3px); } to { opacity:1; transform:none; filter:none; } }
.panel,.actor-card,.article-card,.quote-card,.method-card,.feed-card,.counter-card,.control-card,.timeline-entry,.analysis-rail { animation:revealUp .72s cubic-bezier(.2,.7,.2,1) both; animation-timeline:view(); animation-range:entry 0% cover 24%; }
@supports not (animation-timeline: view()) { .panel,.actor-card,.article-card,.quote-card,.method-card,.feed-card,.counter-card,.control-card,.timeline-entry,.analysis-rail { animation:revealUp .65s ease both; } }
@keyframes livePulse { 0%,100% { box-shadow:0 0 0 0 rgba(76,203,138,.55); } 50% { box-shadow:0 0 0 7px rgba(76,203,138,0); } }

/* Streamlit widget polish: consistent custom controls across every page */
[data-testid="stSegmentedControl"] { margin: 4px 0 18px !important; }
[data-testid="stSegmentedControl"] > div { min-height: 46px !important; }
[data-testid="stMultiSelect"] > div, [data-testid="stSelectbox"] > div,
[data-testid="stTextInput"] > div, [data-testid="stNumberInput"] > div,
[data-testid="stDateInput"] > div { background:#151116 !important; border-radius:10px !important; }
[data-testid="stMultiSelect"] [role="combobox"], [data-testid="stSelectbox"] [role="combobox"] { color:#f4eee7 !important; }
[data-testid="stMultiSelect"] [data-baseweb="select"], [data-testid="stSelectbox"] [data-baseweb="select"] { border-color:#49383f !important; }
[data-testid="stMultiSelect"] [data-baseweb="tag"] { background:#3a2429 !important; border:1px solid #765057 !important; color:#fff0e8 !important; border-radius:7px !important; }
[data-testid="stCheckbox"] > label, [data-testid="stToggle"] > label { color:#e9ddd7 !important; font-weight:650 !important; }
[data-testid="stCheckbox"] [role="checkbox"] { border:1px solid #765057 !important; background:#151116 !important; }
[data-testid="stToggle"] button { background:#2b2024 !important; border:1px solid #62454b !important; }
[data-testid="stToggle"] button[aria-checked="true"] { background:#9b554d !important; }
[data-testid="stExpander"] { background:linear-gradient(145deg,#181418,#120f13) !important; border:1px solid #49363c !important; border-radius:12px !important; overflow:hidden; }
[data-testid="stExpander"] summary { padding:15px 16px !important; min-height:48px; }
[data-testid="stExpander"] summary:hover { background:#20171b !important; }
[data-testid="stProgress"] { margin:12px 0 18px !important; }
[data-testid="stProgressBar"] { background:#2b2226 !important; border-radius:99px !important; overflow:hidden; height:7px !important; }
[data-testid="stProgressBar"] > div > div { background:linear-gradient(90deg,#ff6b61,#e8a64a) !important; border-radius:99px !important; }
.visual-hero { position:relative; overflow:hidden; min-height:340px; border:1px solid #49363c; border-radius:14px; background:#121014; box-shadow:0 18px 40px rgba(0,0,0,.28); }
.visual-hero img { width:100%; height:340px; object-fit:cover; display:block; filter:saturate(.95) contrast(1.03); }
.visual-hero::after { content:""; position:absolute; inset:0; background:linear-gradient(180deg,rgba(7,7,9,.02) 28%,rgba(7,7,9,.82) 100%); pointer-events:none; }
.visual-overlay { position:absolute; z-index:2; left:22px; right:22px; bottom:20px; }
.visual-title { color:#fff4ec; font-size:1.28rem; font-weight:800; letter-spacing:-.025em; margin-top:10px; }
.visual-caption { color:#d0c0ba; font-size:.76rem; line-height:1.5; margin-top:5px; max-width:720px; }
.page-hero { padding-top:14px; margin-top:4px; min-height:132px; }
.page-title { max-width:100%; overflow-wrap:anywhere; }
.header-title { display:inline-block; line-height:1.05; }
.header-sub { display:inline-block; line-height:1.3; vertical-align:middle; }
.topbar { min-height:62px; }
[data-testid="stPlotlyChart"] { border:1px solid #30252a; border-radius:12px; overflow:hidden; background:#171419; }

/* Bespoke masthead and navigation */
.site-brand { display:flex; align-items:center; gap:14px; padding:2px 0 18px; }
.site-mark { display:grid; place-items:center; width:42px; height:42px; border:1px solid #81584e; border-radius:50%; color:var(--copper); font-family:var(--mono); font-size:1rem; box-shadow:inset 0 0 0 5px rgba(232,166,74,.04); }
.site-name { color:#fff3e9; font-family:var(--display); font-size:1.05rem; font-weight:800; letter-spacing:.02em; line-height:1.08; }
.site-deck { color:#9f8e87; font-size:.68rem; margin-top:5px; letter-spacing:.04em; }
.site-status { color:#9c8a83; font-family:var(--mono); font-size:.58rem; line-height:1.55; text-align:right; padding-top:7px; }
.site-status b { color:var(--green); letter-spacing:.1em; }
[data-testid="stPopover"] { display:flex; justify-content:flex-end; padding-top:2px; }
[data-testid="stPopover"] > button { min-height:42px !important; padding:8px 13px !important; border-radius:999px !important; border:1px solid #574047 !important; background:#171216 !important; color:#fff1e7 !important; font-family:var(--mono) !important; font-size:.65rem !important; letter-spacing:.08em; }
[data-testid="stPopover"] > button:hover { border-color:var(--copper) !important; background:#24181d !important; }
[data-testid="stPopoverBody"] { background:#151115 !important; border:1px solid #4b383e !important; border-radius:14px !important; min-width:250px !important; padding:10px !important; }
[data-testid="stPopoverBody"] [role="radiogroup"] label { padding:8px 10px !important; border-radius:8px; }
[data-testid="stPopoverBody"] [role="radiogroup"] label:hover { background:#24191e; }
.editorial-rule { height:1px; background:linear-gradient(90deg,var(--copper),#51343c 28%,transparent); margin:-3px 0 28px; }
.panel, .actor-card, .article-card { position:relative; }
.panel::before, .actor-card::before { content:""; position:absolute; left:18px; top:-1px; width:42px; height:1px; background:var(--copper); opacity:.65; }
.actor-name, .article-title, .news-title, .visual-title, .quote-text { font-family:var(--display); }
.control-card { min-height:0; height:auto; overflow:visible; }
[data-testid="stMultiSelect"] { margin-bottom:10px; }
[data-testid="stVerticalBlock"] { min-width:0; }

@media (max-width: 1050px) {
    .block-container { padding:30px 22px 48px; }
    .nav-shell { margin:-6px -4px 20px; }
    [data-testid="stSegmentedControl"] > div { overflow-x:auto !important; justify-content:flex-start !important; }
    [data-testid="stSegmentedControl"] button { flex:0 0 auto !important; }
    .command-meta { display:none; }
}
@media (max-width: 720px) {
    .block-container { padding:24px 14px 38px; }
    [data-testid="stToolbar"] { display:none !important; }
    [data-testid="stHorizontalBlock"] { flex-wrap:wrap !important; gap:.8rem !important; }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { min-width:100% !important; flex:1 1 100% !important; width:100% !important; }
    .site-brand { padding-bottom:2px; }
    .site-status { text-align:left; padding:0 0 3px 56px; }
    [data-testid="stPopover"] { justify-content:flex-start; padding-left:56px; margin-bottom:16px; }
    .header-title { font-size:1.35rem; } .header-sub { display:block; margin:5px 0 0; } .page-title { font-size:2.25rem; overflow-wrap:normal; word-break:normal; }
    .page-hero { min-height:0; padding:8px 0 20px; }
    .panel { min-height:0; padding:16px; } .metric-row { gap:18px; }
    .visual-hero, .visual-hero img { min-height:280px; height:280px; }
    .alert-strip { align-items:flex-start; flex-wrap:wrap; }
    .alert-strip small { margin-left:0; width:100%; }
    .map-schematic { font-size:.58rem; overflow:hidden; }
}

/* Clarento editorial pass — deliberate rhythm, restrained surfaces */
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] { gap:0 !important; }
[data-testid="stHorizontalBlock"] { align-items:flex-start !important; gap:20px !important; margin:0 !important; }
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { min-width:0; }
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"] > [data-testid="stVerticalBlock"] { gap:0 !important; }
p, li, [data-testid="stMarkdownContainer"] { font-family:var(--ui) !important; font-weight:400; }
h1,h2,h3,.page-title,.visual-title,.article-title,.actor-name,.quote-text,.news-title,.card-title { font-family:var(--display) !important; font-weight:600 !important; }
.page-title { font-size:clamp(2.7rem,5vw,5rem); line-height:.96; letter-spacing:-.05em; max-width:900px; }
.page-description { color:#aaa096; font-size:.96rem; line-height:1.72; max-width:660px; }
.page-hero { min-height:0; margin:0 0 52px; padding:42px 0 40px; }
.page-kicker,.panel-title,.section-title { font-weight:500 !important; }
.section-title { border-top:1px solid var(--border); margin:76px 0 22px; padding-top:19px; }
.panel,.actor-card,.article-card,.quote-card,.method-card,.feed-card,.counter-card,.control-card,.analysis-rail {
    background:var(--panel); border:1px solid var(--border); border-radius:2px; box-shadow:none; height:auto; margin-bottom:20px;
}
.card-grid { display:grid; gap:20px; margin:0 0 20px; align-items:stretch; }
.card-grid.grid-2 { grid-template-columns:repeat(2,minmax(0,1fr)); }
.card-grid.grid-3 { grid-template-columns:repeat(3,minmax(0,1fr)); }
.card-grid.grid-traffic { grid-template-columns:minmax(220px,.85fr) minmax(400px,1.7fr) minmax(220px,.85fr); }
.card-grid > .panel,.card-grid > .actor-card,.card-grid > .article-card { height:100%; margin:0; }
.card-grid.grid-2 > .panel { min-height:210px; }
.card-grid.grid-3 > .panel { min-height:250px; }
.card-grid.grid-traffic > .panel { min-height:255px; }
.about-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:20px; align-items:stretch; }
.about-grid > * { min-height:230px; height:100%; margin:0 !important; }
.panel { min-height:0; padding:24px 25px 26px; }
.panel:hover,.actor-card:hover,.article-card:hover,.counter-card:hover { border-color:var(--border-hi); transform:none; box-shadow:none; }
.panel::before,.actor-card::before { display:none; }
.panel-title { color:#bdb1a7; font-size:.62rem; letter-spacing:.16em; margin-bottom:22px; }
.card-title { color:var(--text); font-size:1.18rem; line-height:1.28; letter-spacing:-.025em; }
.big-number { font-size:2rem; font-weight:500; }
.sub-label { font-size:.78rem; line-height:1.62; }
.actor-card { min-height:250px; padding:25px; }
.actor-name { font-size:1.6rem; margin-top:42px; }
.article-card { min-height:370px; }
.article-title { font-size:1.35rem; line-height:1.18; }
.feed-card,.quote-card,.method-card,.control-card { padding:25px; }
.counter-card { min-height:118px; padding:20px; }
.visual-hero { border-radius:2px; border-color:var(--border); box-shadow:none; margin-bottom:28px; }
.market-shell { padding-bottom:0; }
.market-kpis { background:var(--panel); border:1px solid var(--border); border-bottom:0; margin:0 !important; padding:22px 24px 18px; }
[data-testid="stPlotlyChart"] { border-color:var(--border); border-radius:2px; }
.analysis-rail { border-radius:2px; }
.analysis-art { background:linear-gradient(135deg,#352219,#1d1915 64%); }
.analysis-art::after { background:linear-gradient(135deg,transparent 48%,rgba(184,97,64,.72) 49%,transparent 50%); }
.metric-row { gap:34px; }
.data-row { padding:10px 0; }
.timeline-entry { margin-bottom:24px; }
.footer { border-top:1px solid var(--border); margin-top:90px; padding-top:28px; }

/* Header reads as a designed website navigation, not a Streamlit widget. */
.site-brand { min-width:0; padding:9px 0 20px; }
.site-brand > div:last-child { min-width:0; }
.site-mark { width:36px; height:36px; border:0; border-radius:0; border-right:1px solid var(--copper); box-shadow:none; justify-content:start; }
.site-name { font-family:var(--ui); font-size:.96rem; letter-spacing:-.02em; }
.site-deck { font-size:.64rem; max-width:420px; white-space:normal; overflow-wrap:break-word; }
.site-status { min-height:48px; padding:8px 0 14px; }
.editorial-rule { background:var(--border); margin:-10px 0 0; }
.site-nav {
    display:flex; align-items:center; justify-content:center; gap:2px; min-height:44px;
    overflow-x:auto; scrollbar-width:none; white-space:nowrap;
}
.site-nav::-webkit-scrollbar { display:none; }
.site-nav .nav-link {
    position:relative; display:inline-flex; align-items:center; min-height:40px; padding:8px 9px;
    color:#8f857c !important; font-family:var(--mono); font-size:.58rem; font-weight:500;
    letter-spacing:.035em; text-decoration:none !important; transition:color .18s ease;
}
.site-nav .nav-link:hover { color:#f4eee3 !important; }
.site-nav .nav-link.is-active { color:#f4eee3 !important; }
.site-nav .nav-link.is-active::after {
    content:""; position:absolute; left:9px; right:9px; bottom:3px; height:1px; background:var(--copper);
}

/* Native Streamlit buttons power navigation; presentation stays editorial. */
.stButton { margin:0 !important; }
.stButton > button {
    min-height:40px !important; padding:7px 5px !important; border:0 !important; border-radius:0 !important;
    background:transparent !important; box-shadow:none !important; color:#8f857c !important;
}
.stButton > button p { font-family:var(--mono) !important; font-size:.56rem !important; font-weight:500 !important; white-space:nowrap; }
.stButton > button:hover { color:#f4eee3 !important; background:#211c17 !important; transform:none !important; }
.stButton > button[kind="primary"] {
    color:#f4eee3 !important; background:transparent !important; box-shadow:inset 0 -1px 0 var(--copper) !important;
}
.stButton > button:focus { outline:1px solid var(--copper) !important; outline-offset:-2px; }

/* Native tabs provide client-side navigation: no rerun state can block a page. */
[data-testid="stTabs"] { margin-top:0; }
[data-baseweb="tab-list"] {
    gap:2px !important; min-height:54px; padding:5px 0 0 !important; overflow-x:auto;
    border-bottom:1px solid var(--border); scrollbar-width:none;
}
[data-baseweb="tab-list"]::-webkit-scrollbar { display:none; }
[data-baseweb="tab"] {
    flex:0 0 auto !important; min-width:auto !important; height:48px !important; padding:0 15px !important;
    color:#8f827d !important; background:transparent !important; border:0 !important;
}
[data-baseweb="tab"] p { font-family:var(--mono) !important; font-size:.62rem !important; font-weight:500 !important; letter-spacing:.045em; white-space:nowrap; }
[data-baseweb="tab"]:hover { color:var(--text) !important; background:#171317 !important; }
[data-baseweb="tab"][aria-selected="true"] { color:var(--text) !important; }
[data-baseweb="tab-highlight"] { background:var(--copper) !important; height:1px !important; }
[data-baseweb="tab-border"] { display:none !important; }
[data-testid="stTabContent"] { padding-top:0 !important; }

/* Functional inline navigation, styled as text rather than a dashboard control. */
[data-testid="stSegmentedControl"] { margin:0 !important; }
[data-testid="stSegmentedControl"] > div {
    width:100% !important; min-height:42px !important; display:flex !important; justify-content:center !important;
    gap:2px !important; padding:0 !important; overflow-x:auto !important;
    background:transparent !important; border:0 !important; border-radius:0 !important; scrollbar-width:none;
}
[data-testid="stSegmentedControl"] > div::-webkit-scrollbar { display:none; }
[data-testid="stSegmentedControl"] button {
    flex:0 0 auto !important; min-height:38px !important; padding:8px 9px !important;
    background:transparent !important; border:0 !important; border-radius:0 !important; box-shadow:none !important;
    color:#8f857c !important; transform:none !important;
}
[data-testid="stSegmentedControl"] button p { font-family:var(--mono) !important; font-size:.58rem !important; font-weight:500 !important; letter-spacing:.04em; }
[data-testid="stSegmentedControl"] button:hover { color:#f4eee3 !important; background:transparent !important; }
[data-testid="stSegmentedControl"] button[aria-pressed="true"] {
    color:#f4eee3 !important; background:transparent !important; border:0 !important;
    box-shadow:inset 0 -1px 0 var(--copper) !important;
}

/* Reliable page router: the radio owns state, CSS makes it read like bespoke nav. */
[data-testid="stRadio"] { width:100%; margin:0 !important; }
[data-testid="stRadio"] [role="radiogroup"] {
    display:flex !important; flex-wrap:nowrap !important; justify-content:center; gap:3px !important;
    width:100%; min-height:42px; overflow-x:auto; scrollbar-width:none;
}
[data-testid="stRadio"] [role="radiogroup"]::-webkit-scrollbar { display:none; }
[data-testid="stRadio"] label {
    flex:0 0 auto; position:relative; margin:0 !important; padding:10px 8px 11px !important;
    color:#8f857c !important; cursor:pointer; transition:color .18s ease;
}
[data-testid="stRadio"] label input { position:absolute !important; opacity:0 !important; pointer-events:none !important; }
[data-testid="stRadio"] label [data-testid="stMarkdownContainer"] { margin:0 !important; }
[data-testid="stRadio"] label p { font-family:var(--mono) !important; font-size:.58rem !important; font-weight:500 !important; letter-spacing:.035em; white-space:nowrap; }
[data-testid="stRadio"] label:hover { color:#f4eee3 !important; }
[data-testid="stRadio"] label:has(input:checked) { color:#f4eee3 !important; }
[data-testid="stRadio"] label:has(input:checked)::after {
    content:""; position:absolute; left:8px; right:8px; bottom:4px; height:1px; background:var(--copper);
}
[data-testid="stPopover"] { padding-top:4px; }
[data-testid="stPopover"] > button {
    position:relative; width:48px !important; min-width:48px !important; height:42px !important; padding:0 !important;
    border:0 !important; border-radius:0 !important; color:transparent !important;
    background:linear-gradient(#f4eee3,#f4eee3) 50% calc(50% - 7px)/25px 1px no-repeat,
               linear-gradient(#f4eee3,#f4eee3) 50% 50%/25px 1px no-repeat,
               linear-gradient(#f4eee3,#f4eee3) 50% calc(50% + 7px)/25px 1px no-repeat !important;
}
[data-testid="stPopover"] > button p,[data-testid="stPopover"] > button svg { opacity:0 !important; }
[data-testid="stPopover"] > button:hover { background-color:#28231e !important; }
[data-testid="stPopoverBody"] { background:#f4eee3 !important; border:0 !important; border-radius:2px !important; padding:14px !important; }
[data-testid="stPopoverBody"] [role="radiogroup"] label { color:#16130f !important; font-family:var(--ui) !important; border-bottom:1px solid #d8cfc1; border-radius:0; padding:11px 8px !important; }
[data-testid="stPopoverBody"] [role="radiogroup"] label:hover { background:#e8dfd1; }

@media (max-width:720px) {
    [data-testid="stHorizontalBlock"] { gap:14px !important; }
    .block-container { padding:18px 18px 44px; }
    .page-hero { margin-bottom:34px; padding:34px 0 30px; }
    .page-title { font-size:3.35rem; }
    .section-title { margin-top:54px; }
    .site-status { padding-left:0; }
    .site-deck { max-width:260px; font-size:.6rem; line-height:1.45; }
    [data-testid="stSegmentedControl"] > div { justify-content:flex-start !important; }
    [data-testid="stSegmentedControl"] button { padding:8px 10px !important; }
    [data-testid="stRadio"] [role="radiogroup"] { justify-content:flex-start; }
    .site-nav { justify-content:flex-start; }
    [data-testid="stColumn"] [data-testid="stHorizontalBlock"] { flex-wrap:nowrap !important; overflow-x:auto; gap:2px !important; }
    [data-testid="stColumn"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { min-width:76px !important; flex:0 0 76px !important; width:76px !important; }
    .panel,.actor-card,.feed-card,.quote-card,.method-card,.control-card { padding:21px; }
    .panel,.actor-card,.article-card,.quote-card,.method-card,.feed-card,.counter-card,.control-card,.analysis-rail { margin-bottom:14px; }
    .card-grid,.card-grid.grid-2,.card-grid.grid-3,.card-grid.grid-traffic { grid-template-columns:1fr; gap:14px; margin-bottom:14px; }
    .about-grid { grid-template-columns:1fr; gap:14px; }
    .about-grid > * { min-height:0; }
    .card-grid > .panel,.card-grid.grid-2 > .panel,.card-grid.grid-3 > .panel,.card-grid.grid-traffic > .panel { min-height:0; margin:0; }
}
@media (min-width:721px) and (max-width:1100px) {
    .card-grid.grid-3,.card-grid.grid-traffic { grid-template-columns:repeat(2,minmax(0,1fr)); }
    .card-grid.grid-traffic > .panel:nth-child(2) { grid-column:1 / -1; grid-row:1; }
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Frontend Flask API client helpers
# -----------------------------------------------------------------------------
FLASK_API_URL = os.getenv("FLASK_API_URL", "http://127.0.0.1:5000").rstrip("/")


@st.cache_data(ttl=20, show_spinner=False)
def get_vessel_status() -> Optional[Dict[str, Any]]:
    """Fetch live AISStream connection status with 20-second cache."""
    try:
        resp = requests.get(f"{FLASK_API_URL}/api/vessels/status", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


@st.cache_data(ttl=20, show_spinner=False)
def get_vessel_summary() -> Optional[Dict[str, Any]]:
    """Fetch active vessel metrics summary with 20-second cache."""
    try:
        resp = requests.get(f"{FLASK_API_URL}/api/vessels/summary", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


@st.cache_data(ttl=20, show_spinner=False)
def get_active_vessels() -> Optional[List[Dict[str, Any]]]:
    """Fetch active vessels list for map overlay with 20-second cache."""
    try:
        resp = requests.get(f"{FLASK_API_URL}/api/vessels", timeout=5)
        if resp.status_code == 200:
            return resp.json().get("vessels", [])
    except Exception:
        pass
    return None


@st.cache_data(ttl=300, show_spinner=False)
def get_brent_data() -> Optional[Dict[str, Any]]:
    """Fetch official U.S. EIA daily Brent spot price with 5-minute cache."""
    try:
        resp = requests.get(f"{FLASK_API_URL}/api/brent", timeout=8)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


# -----------------------------------------------------------------------------
# Data layer — static baselines & verified live feeds
# -----------------------------------------------------------------------------
PORT_IMAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hormuz_port.jpg")

CLOSED_SINCE = dt.datetime(2026, 2, 28, tzinfo=dt.timezone.utc)
NOW = dt.datetime.now(dt.timezone.utc)
delta = NOW - CLOSED_SINCE

# Static baseline estimates for metrics not supplied by live AIS stream
traffic_baseline = {
    "daily_throughput_dwt": "520.0K",
    "daily_throughput_pct_avg": "5% of 10.3M avg",
    "transits_24h": 1,
    "transits_normal": 60,
    "vessels_waiting": 441,
    "vessels_breakdown": {"Tankers": 185, "Bulk Carriers": 156, "Other": 100},
}
war_risk = {"level": "EXTREME", "premium": 8.5, "normal_rate": 0.15, "multiple": "56.7x normal"}
tanker_rate = {"value": 320, "unit": "WS", "change_pct": 540, "pre_crisis": 50}

trade_impact = {
    "oil_at_risk_pct": 21,
    "daily_cost_est": "$8.2B",
    "countries": [
        ("Japan", "CRITICAL", "90% dep."),
        ("South Korea", "CRITICAL", "80% dep."),
        ("China", "HIGH", "40% dep."),
        ("India", "HIGH", "60% dep."),
        ("European Union", "MODERATE", "20% dep."),
        ("Saudi Arabia & UAE", "HIGH", "100% dep."),
    ],
}
lng_impact = {
    "world_lng_at_risk_pct": 25,
    "daily_cost_est": "$2.1B",
    "top_importers": ["Japan", "South Korea", "China"],
    "note": "25% of global LNG trade disrupted. LNG carriers nearly halted; critical shortage for Japan and South Korea. Spot LNG prices elevated due to reduced supply and rerouting delays.",
}
supply_chain = {
    "shipping_rate_change": "+425%",
    "cpi_impact": "+3.8%",
    "spr_days": "70d",
    "bullets": [
        "VLCC tanker rates surged from ~$900k pre-crisis ($50 WS) to $4M+ for compliant tonnage (300+ WS) — 4-5x normal cost.",
        "Approximately 6,000 seafarers trapped in region; IMO evacuation efforts ongoing via safe routes.",
        "LNG spot prices elevated; Japan & South Korea facing $15-20/MMBtu vs $8-10 pre-crisis; winter demand fears.",
        "Global automotive, petrochemical, and manufacturing output declining due to diesel/jet fuel shortages and cost inflation; refinery throughput down 15-25%.",
    ],
}
alt_routes = [
    ("Cape of Good Hope", "+12D", "+$650K", "Moderate rerouting; higher costs and 10-15 day delays discourage adoption. ~8-10 VLCC-equivalent daily transits shifting to Cape route."),
    ("Saudi Arabia East-West Pipeline", "5 Mbpd", "Full", "Operating at 5 Mbpd capacity (full). Saudi crude from Eastern fields redirected westward to Red Sea export terminals."),
    ("UAE Habshan-Fujairah Pipeline", "1.5 Mbpd", "Full", "Operating at 1.5 Mbpd capacity (full). UAE crude rerouted to Fujairah for Red Sea/Suez export."),
]
vessel_incidents = {
    "iran": 61, "us_uk": 19, "held": 29, "sunk": 4, "seizures": 17, "attacks": 49, "disabled": 10, "sunk_total": 4,
    "log": [
        ("Sep 8, 2026", "United States", "DISABLED", "M/T Derya (Iran)", "Iranian crude oil tanker struck by US forces near Kharg Island, part of the five-tanker retaliatory strike following the IRGC's second attempted missile strike on a US Navy warship in two days."),
        ("Sep 8, 2026", "United States", "SUNK", "Riesco (Unknown)", "Iranian-linked crude oil tanker struck in the Gulf of Oman as part of the five-tanker US retaliatory strike package on September 8."),
        ("Sep 8, 2026", "United States", "DISABLED", "Three Additional Tankers (Gulf of Oman)", "Three further Iranian crude oil tankers struck by US forces in the Gulf of Oman on September 8, part of the same five-vessel retaliatory package."),
    ],
}
strike_exchange = {
    "iran_irgc": 34, "us_israel": 22, "total_strikes": "~774", "thresholds": 33, "airstrikes": 19, "missile": 17, "drone": 11, "naval": 9,
    "log": [
        ("Sep 9, 2026", "IRGC", "MISSILE", "Two US Navy destroyers (Iran)", "DISPUTED CLAIM. IRGC state-aligned media claims Iranian forces struck two US Navy destroyers with ballistic missiles, causing 'significant damage'; CENTCOM issues a flat public denial."),
        ("Sep 8, 2026", "IRGC", "MISSILE", "US Navy warship (unspecified) (Iran)", "IRGC forces attempt to strike a US Navy warship with ballistic missiles for the second time in two days. CENTCOM says the attempt failed."),
        ("Sep 8, 2026", "United States", "AIRSTRIKE", "Five Iranian crude oil tankers", "US forces destroy five Iranian crude oil tankers after the IRGC's second attempted missile strike on a US Navy warship in two days."),
    ],
}
news_items = [
    ("Saudi Arabia shuts key oil pipeline as Houthis seize strategic Red Sea island", "Saudi Arabia has shut down its major East-West oil pipeline after it was attacked by drones, as the widening Iran war opened another front.", "The Times Of India", "18 hours ago"),
    ("Oil above $100: Red Sea threat could add month to Asia shipments", "Red Sea tensions and Houthi advances threaten Bab al-Mandab, forcing oil tankers to reroute around Africa, lifting prices above $100.", "Gulf News", "18 hours ago"),
    ("Six months into the Iran war, no end is in sight", "The Gulf faces disruption, rising risks and no clear end in sight, as shifting battles reshape regional security and oil routes.", "Gulf News", "18 hours ago"),
    ("Hormuz choked, Red Sea threatened: How will oil get through?", "Hormuz, Red Sea squeeze: How will oil get through?", "Gulf News", "19 hours ago"),
]
peace_talks = {
    "status": "PROPOSED", "days_ago": 16, "headline": "Qatar-Iran Diplomacy Ongoing; Statement 'Not in Hurry' to Resume Negotiations",
    "body": "Qatar's PM/FM met Iranian leaders to discuss de-escalation and creating conditions for dialogue on Strait of Hormuz management. Iranian officials remain only meeting with mediators. Earlier ceasefire failed after both sides resumed attacks; Iran-US and Iran-Oman talks continue via intermediaries, but no breakthrough apparent.",
    "tags": ["Iran", "Qatar", "Pakistan", "United States", "Oman"],
}
analysis_items = [
    ("Eight Tankers in Seven Days: How the Blockade Became a Tanker War", "Analysis", "6 min read", "Ten Iranian tankers destroyed in a week, marking a shift from deterrence to attrition at sea."),
    ("The Ship That Sailed: How the Second MOU Collapsed", "Analysis", "7 min read", "A review of the operational and diplomatic constraints shaping commercial passage through Hormuz."),
    ("The Second MOU: Why This One Is Different", "Analysis", "11 min read", "Key scenarios for shipping access, insurance pricing, and regional de-escalation."),
]


# -----------------------------------------------------------------------------
# Presentation helpers
# -----------------------------------------------------------------------------
def icon(kind: str, color: str = "currentColor") -> str:
    paths = {
        "pulse": '<path d="M3 12h4l2-7 4 14 2-7h6"/>',
        "shield": '<path d="M12 3 19 6v5c0 4.4-3 8-7 10-4-2-7-5.6-7-10V6l7-3Z"/><path d="m9 12 2 2 4-4"/>',
        "ship": '<path d="M3 17h18M5 17l1 3h12l1-3M7 14V6h7l3 3v5M10 6V3h4"/>',
        "alert": '<path d="M12 3 2.5 20h19L12 3Z"/><path d="M12 9v5m0 3h.01"/>',
        "chart": '<path d="M4 19V5m0 14h16M7 15l3-4 3 2 4-6"/>',
        "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.2 2.5 3.3 5.5 3.3 9s-1.1 6.5-3.3 9c-2.2-2.5-3.3-5.5-3.3-9S9.8 5.5 12 3Z"/>',
    }
    return f'<span class="icon" style="color:{color}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{paths.get(kind, paths["pulse"])}</svg></span>'


def badge(label: str, level: str = "moderate") -> str:
    return f'<span class="badge badge-{level.lower()}">{escape(str(label))}</span>'


def panel(title: str, body: str, title_icon: str | None = None) -> str:
    icon_html = icon(title_icon) if title_icon else ""
    return f'<div class="panel"><div class="panel-title">{icon_html}{escape(title)}</div>{body}</div>'


def metric(value: str, label: str, tone: str = "") -> str:
    return f'<div><div class="big-number {tone}">{escape(str(value))}</div><div class="sub-label">{escape(label)}</div></div>'


def severity_for(kind: str) -> str:
    return "critical" if kind in {"SUNK", "MISSILE", "AIRSTRIKE"} else "warning"


def timeline_item(date: str, actor: str, kind: str, target: str, description: str) -> str:
    level = severity_for(kind)
    actor_level = "moderate" if actor in {"United States", "IRGC"} else "info"
    return f'''<div class="timeline-entry {level}">
        <div class="timeline-meta"><span class="timeline-date">{escape(date)}</span>{badge(actor, actor_level)}{badge(kind, "critical" if level == "critical" else "high")}</div>
        <div class="timeline-target">{escape(target)}</div>
        <div class="sub-label">{escape(description)}</div>
    </div>'''


def section_heading(label: str, kind: str = "pulse") -> None:
    st.markdown(f'<div class="panel-title section-title">{icon(kind)}{escape(label)}</div>', unsafe_allow_html=True)


def page_hero(kicker: str, title: str, description: str) -> None:
    st.markdown(f'<div class="page-hero"><div class="page-kicker">{escape(kicker)}</div><div class="page-title">{escape(title)}</div><div class="page-description">{escape(description)}</div></div>', unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Fetch dynamic backend data (cached)
# -----------------------------------------------------------------------------
vessel_status = get_vessel_status()
vessel_summary = get_vessel_summary()
active_vessels_list = get_active_vessels() or []
brent_data = get_brent_data()

ais_connected = bool(vessel_status and vessel_status.get("connected"))


# -----------------------------------------------------------------------------
# Masthead and compact site navigation
# -----------------------------------------------------------------------------
brand_col, status_col = st.columns([7.8, 2.2], gap="medium", vertical_alignment="center")

with brand_col:
    st.markdown('<div class="site-brand"><div class="site-mark">H/26</div><div><div class="site-name">STRAIT / SIGNAL</div><div class="site-deck">Independent maritime intelligence for the Hormuz corridor</div></div></div>', unsafe_allow_html=True)
with status_col:
    st.markdown(f'<div class="site-status"><b><span class="live-dot" style="margin-left:0"></span>LIVE MONITOR</b><br>UPDATED {NOW.strftime("%d %b · %H:%M UTC")}</div>', unsafe_allow_html=True)
st.markdown('<div class="editorial-rule"></div>', unsafe_allow_html=True)
tab_overview, tab_timeline, tab_actors, tab_blog, tab_news, tab_about, tab_faq = st.tabs(
    ["Overview", "Timeline", "Key Actors", "Blog", "News", "About", "FAQ"]
)


# -----------------------------------------------------------------------------
# Overview
# -----------------------------------------------------------------------------
with tab_overview:
        status_body = f'<div class="status-center">{badge("CLOSED", "critical")}<div class="sub-label" style="margin-top:10px">Since {CLOSED_SINCE.strftime("%B %d, %Y")} · {delta.days} days ago</div></div>'
        hours, minutes = delta.seconds // 3600, (delta.seconds % 3600) // 60
        duration_body = f'<div class="metric-row">{metric(str(delta.days), "DAYS", "red")}{metric(str(hours), "HOURS")}{metric(str(minutes), "MINUTES")}</div>'
        st.markdown(f'<div class="card-grid grid-2">{panel("STRAIT STATUS", status_body, "alert")}{panel("DURATION OF CLOSURE", duration_body, "pulse")}</div>', unsafe_allow_html=True)

        section_heading("Strait of Hormuz · Traffic Overview", "ship")
        if os.path.exists(PORT_IMAGE):
            img_left, img_right = st.columns([1.65, 1], gap="large")
            with img_left:
                st.markdown('<div class="visual-hero"><img src="data:image/jpeg;base64,' + __import__("base64").b64encode(open(PORT_IMAGE, "rb").read()).decode() + '"/><div class="visual-overlay"><span class="badge badge-high">PORT ACTIVITY</span><div class="visual-title">Trade infrastructure at the chokepoint</div><div class="visual-caption">Container traffic, heavy-lift cranes and market signals converge around the Strait.</div></div></div>', unsafe_allow_html=True)
            with img_right:
                st.markdown(panel("WHY THE CHOKEPOINT MATTERS", '<div class="card-title">A narrow maritime passage with outsized economic impact.</div><div class="sub-label" style="margin-top:9px">Use this visual anchor as the opening context for the traffic, insurance, energy and rerouting indicators below.</div><div class="badge badge-high" style="margin-top:14px">21 NM · NARROWEST POINT</div>', "globe"), unsafe_allow_html=True)

        map_body = '<div class="map-schematic"><div>IRAN <span class="map-line">──────────────</span></div><div>QESHM · HORMUZ · LARAK → GULF OF OMAN</div><div>UAE <span class="map-line">──────────────</span> OMAN</div><div class="sub-label">Narrowest point · 21 nautical miles</div></div>'
        transit_body = metric(f'{traffic_baseline["transits_24h"]} ships', "24H · " + f'{traffic_baseline["transits_24h"] / traffic_baseline["transits_normal"] * 100:.1f}% of normal', "red") + '<div style="height:16px"></div>' + metric(str(traffic_baseline["vessels_waiting"]), "VESSELS WAITING", "amber") + '<div class="sub-label" style="margin-top:6px;font-size:0.62rem;color:#756966">ESTIMATED SAMPLE BASELINE</div>'
        traffic_cards = panel("DAILY THROUGHPUT", metric(traffic_baseline["daily_throughput_dwt"], "DWT · " + traffic_baseline["daily_throughput_pct_avg"], "red") + '<div class="sub-label" style="margin-top:6px;font-size:0.62rem;color:#756966">ESTIMATED SAMPLE BASELINE</div>', "chart") + panel("SCHEMATIC ROUTE MAP", map_body, "globe") + panel("TRANSITS & QUEUE", transit_body, "ship")
        st.markdown(f'<div class="card-grid grid-traffic">{traffic_cards}</div>', unsafe_allow_html=True)

        # Dynamic CURRENT TRAFFIC from AISStream
        if ais_connected and vessel_summary:
            active_cnt = vessel_summary.get("active_vessels", 0)
            underway_cnt = vessel_summary.get("underway_vessels", 0)
            stationary_cnt = vessel_summary.get("stationary_vessels", 0)
            v_types = vessel_summary.get("vessel_types", {})
            types_str = " · ".join(f"{k}: {v}" for k, v in v_types.items())
            fetched_time = vessel_summary.get("fetched_at", "")[:19].replace("T", " ")

            current_body = (
                metric(f"{active_cnt} active", "CURRENT ACTIVE VESSELS", "green" if active_cnt > 0 else "amber")
                + f'<div class="sub-label" style="margin-top:8px">Underway: <b class="mono">{underway_cnt}</b> · Stationary: <b class="mono">{stationary_cnt}</b></div>'
                + f'<div class="sub-label" style="margin-top:4px">{escape(types_str)}</div>'
                + f'<div class="sub-label" style="margin-top:8px;color:#756966;font-size:0.64rem">Provider: <b>AISStream</b> · Updated: {escape(fetched_time)} UTC</div>'
            )
        else:
            current_body = (
                '<div class="status-center">'
                + badge("FEED UNAVAILABLE", "high")
                + '<div class="sub-label" style="margin-top:10px;color:#c08c78">Live vessel feed unavailable</div>'
                + '<div class="sub-label" style="margin-top:4px;font-size:0.62rem;color:#756966">Provider: AISStream · Missing API key or offline</div>'
                + '</div>'
            )

        # Retain waiting queue card with clear estimation label
        rows = "".join(f'<div class="data-row"><span>{escape(k)}</span><b class="mono">{v}</b></div>' for k, v in traffic_baseline["vessels_breakdown"].items())
        waiting_card_body = metric(str(traffic_baseline["vessels_waiting"]), "TOTAL QUEUE", "amber") + rows + '<div class="sub-label" style="margin-top:8px;font-size:0.62rem;color:#756966">SAMPLE QUEUE ESTIMATE</div>'
        risk_body = badge(war_risk["level"], "critical") + f'<div class="sub-label" style="margin-top:12px">War risk premium: <b class="mono">{war_risk["premium"]}%</b></div><div class="sub-label">Normal rate: {war_risk["normal_rate"]}%</div><div class="sub-label">Increase: <b>{war_risk["multiple"]}</b></div>'
        st.markdown(f'<div class="card-grid grid-3">{panel("CURRENT TRAFFIC", current_body, "ship")}{panel("VESSELS WAITING", waiting_card_body, "alert")}{panel("WAR RISK INSURANCE", risk_body, "shield")}</div>', unsafe_allow_html=True)

        rate_body = metric(f'{tanker_rate["value"]} {tanker_rate["unit"]}', "VLCC SPOT RATE", "red") + f'<div class="sub-label" style="margin-top:8px">+{tanker_rate["change_pct"]}% vs pre-crisis · Pre-crisis: {tanker_rate["pre_crisis"]} WS</div>'
        tags = " ".join(badge(t, "moderate") for t in peace_talks["tags"])
        diplomacy_body = f'{badge(peace_talks["status"], "high")} <span class="sub-label">{peace_talks["days_ago"]} days ago</span><div class="card-title" style="margin-top:12px">{escape(peace_talks["headline"])}</div><div class="sub-label" style="margin-top:8px">{escape(peace_talks["body"])}</div><div style="margin-top:12px">{tags}</div>'
        st.markdown(f'<div class="card-grid grid-2">{panel("TANKER SPOT RATE", rate_body, "chart")}{panel("PEACE TALKS & DIPLOMACY", diplomacy_body, "globe")}</div>', unsafe_allow_html=True)

        # Dynamic Brent Crude Spot Price from U.S. EIA API v2
        section_heading("Brent Crude · Historical", "chart")
        chart_col, analysis_col = st.columns([2.15, 1], gap="large")
        with chart_col:
            if brent_data and "history" in brent_data and len(brent_data["history"]) > 0:
                history_rows = brent_data["history"]
                b_dates = [r["date"] for r in history_rows]
                b_prices = [r["value"] for r in history_rows]
                latest_p = brent_data.get("latest", b_prices[-1])
                change_val = brent_data.get("change", 0.0)
                change_pct_val = brent_data.get("change_percent", 0.0)
                stale_note = " (stale)" if brent_data.get("stale") else ""
                fetched_label = brent_data.get("fetched_at", "")[:10]

                st.markdown(
                    f'<div class="market-kpis">'
                    f'<div><div class="market-kpi-value">${latest_p:.2f}</div><div class="market-kpi-label">UKOIL last{stale_note}</div></div>'
                    f'<div><div class="market-kpi-value" style="color:{"#4CCB8A" if change_val >= 0 else "#D87352"}">{change_val:+.2f} ({change_pct_val:+.1f}%)</div><div class="market-kpi-label">Latest daily move — U.S. EIA</div></div>'
                    f'<div><div class="market-kpi-value">{len(b_prices)}D</div><div class="market-kpi-label">EIA RBRTE Window ({fetched_label})</div></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                fig = go.Figure()
                moving_average = pd.Series(b_prices).rolling(7, min_periods=1).mean()
                fig.add_trace(go.Scatter(x=b_dates, y=b_prices, mode="lines", line=dict(color="#C58BE8", width=3), fill="tozeroy", fillcolor="rgba(197,139,232,.09)", name="Brent spot (EIA)", hovertemplate="$%{y:.2f}<extra>Brent</extra>"))
                fig.add_trace(go.Scatter(x=b_dates, y=moving_average, mode="lines", line=dict(color="#E8A64A", width=1.7, dash="dot"), name="7-day average", hovertemplate="$%{y:.2f}<extra>7D average</extra>"))
                fig.add_trace(go.Scatter(x=[b_dates[-1]], y=[latest_p], mode="markers", marker=dict(size=10, color="#FF6B61", line=dict(color="#FFF1E7", width=2)), name="Latest daily", hovertemplate="Latest · $%{y:.2f}<extra></extra>"))
                fig.add_hline(y=max(b_prices), line_width=1, line_dash="dot", line_color="rgba(255,107,97,.35)", annotation_text=f"HIGH  ${max(b_prices):.2f}", annotation_position="top left", annotation_font=dict(size=9, color="#BFA69D"))
                fig.add_hline(y=min(b_prices), line_width=1, line_dash="dot", line_color="rgba(76,203,138,.28)", annotation_text=f"LOW  ${min(b_prices):.2f}", annotation_position="bottom left", annotation_font=dict(size=9, color="#BFA69D"))
                fig.update_layout(paper_bgcolor="#171317", plot_bgcolor="#171317", height=410, margin=dict(l=18, r=18, t=52, b=24), font=dict(color="#D7C8C4", family="Inter, sans-serif"), hovermode="x unified", hoverlabel=dict(bgcolor="#100D10", bordercolor="#64454A", font=dict(color="#F6EFE9")), xaxis=dict(showgrid=False, tickfont=dict(size=10, color="#8E7F7A"), rangeslider=dict(visible=False), showspikes=True, spikecolor="#64454A", spikethickness=1), yaxis=dict(title="USD / BARREL", title_font=dict(size=10, color="#8E7F7A"), gridcolor="#35292E", zeroline=False, tickprefix="$", tickfont=dict(size=10, color="#8E7F7A"), fixedrange=False), legend=dict(orientation="h", y=1.13, x=0, font=dict(size=10)), showlegend=True)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "scrollZoom": False, "responsive": True})
            else:
                # Structured fallback when EIA data is temporarily unavailable
                st.markdown(
                    '<div class="panel" style="min-height:220px;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;">'
                    '<div class="card-title" style="color:var(--copper);font-size:1.05rem;">Brent price temporarily unavailable</div>'
                    '<div class="sub-label" style="margin-top:10px;color:#a69a92">Could not retrieve daily Europe Brent spot price from U.S. EIA API v2.</div>'
                    '<div class="sub-label" style="margin-top:6px;font-size:0.64rem;color:#756966">Please verify EIA_API_KEY configuration or backend connectivity.</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )

        with analysis_col:
            title, kind, read_time, summary = analysis_items[0]
            body = f"""<div class="analysis-rail"><div class="analysis-art"><span class="badge badge-high">FEATURED ANALYSIS</span></div><div class="analysis-body"><div class="news-meta">{escape(kind)} · {escape(read_time)}</div><div class="analysis-title">{escape(title)}</div><div class="sub-label">{escape(summary)} CENTCOM's new framing marks a shift from deterrence to attrition at sea.</div><div class="analysis-link">READ FULL ANALYSIS →</div></div></div>"""
            st.markdown(body, unsafe_allow_html=True)

        section_heading("Geopolitical Threat Surface", "globe")
        map_col, control_col = st.columns([2.35, 1], gap="large")
        with control_col:
            st.markdown('<div class="control-card"><div class="panel-title">RISK INDICATORS</div>', unsafe_allow_html=True)
            risk_layers = st.multiselect("Show layers", ["Conflict zones", "Mine risk", "Shipping disruption", "Infrastructure", "Live AIS Vessels"], default=["Conflict zones", "Mine risk", "Shipping disruption"], label_visibility="collapsed")
            alert_mode = st.toggle("High-priority alerts", value=True)
            show_labels = st.toggle("Show map labels", value=True)
            st.markdown('<div class="sub-label" style="margin-top:12px">Interactive simulation layer · refreshes with the live monitor</div></div>', unsafe_allow_html=True)
        with map_col:
            threat_points = []
            if "Conflict zones" in risk_layers:
                threat_points.append((56.5, 25.8, "CRITICAL", "Strait approaches", "Missile and naval activity"))
            if "Mine risk" in risk_layers:
                threat_points.append((56.1, 26.4, "HIGH", "Hormuz lanes", "Historic mine-laying corridor"))
            if "Shipping disruption" in risk_layers:
                threat_points.append((55.5, 26.1, "HIGH", "Queue zone", "441 vessels waiting (est)"))
            if "Infrastructure" in risk_layers:
                threat_points.append((51.5, 25.3, "MODERATE", "Qatar LNG", "Export dependency"))
            if threat_points:
                lat, lon, levels, names, notes = zip(*threat_points)
            else:
                lat, lon, levels, names, notes = [], [], [], [], []
            colors = {"CRITICAL": "#FF6B61", "HIGH": "#E8A64A", "MODERATE": "#4CCB8A"}
            fig_map = go.Figure(go.Scattergeo(lat=lat, lon=lon, mode="markers+text" if show_labels else "markers", text=names if show_labels else None, textposition="top center", customdata=notes, hovertemplate="<b>%{text}</b><br>%{customdata}<extra></extra>", marker=dict(size=14, color=[colors[x] for x in levels] if levels else [], line=dict(color="#FFF1E7", width=1), opacity=.9), name="Risk Layer"))

            # Optional live vessel overlay if selected
            if "Live AIS Vessels" in risk_layers and active_vessels_list:
                v_lats = [v["latitude"] for v in active_vessels_list if v.get("latitude") is not None]
                v_lons = [v["longitude"] for v in active_vessels_list if v.get("longitude") is not None]
                v_names = [v.get("name") or f"MMSI {v['mmsi']}" for v in active_vessels_list if v.get("latitude") is not None]
                v_notes = [f"Type: {v.get('ship_type', 'Other')} | SOG: {v.get('sog', 'N/A')} kn" for v in active_vessels_list if v.get("latitude") is not None]
                if v_lats:
                    fig_map.add_trace(go.Scattergeo(
                        lat=v_lats,
                        lon=v_lons,
                        mode="markers+text" if show_labels else "markers",
                        text=v_names if show_labels else None,
                        textposition="bottom center",
                        customdata=v_notes,
                        hovertemplate="<b>%{text}</b><br>%{customdata}<extra>AISStream</extra>",
                        marker=dict(size=9, color="#4CCB8A", symbol="triangle-up", line=dict(color="#FFFFFF", width=1)),
                        name="Active Vessels"
                    ))

            fig_map.update_geos(scope="world", projection_type="equirectangular", center=dict(lat=26, lon=55), lataxis_range=[20, 32], lonaxis_range=[45, 65], showland=True, landcolor="#1B171A", showocean=True, oceancolor="#0E1115", showcountries=True, countrycolor="#47383D", coastlinecolor="#6B4D4C", showlakes=False)
            fig_map.update_layout(paper_bgcolor="#171419", height=330, margin=dict(l=0, r=0, t=0, b=0), font=dict(color="#EBDDD6", family="IBM Plex Sans, sans-serif"), showlegend=False)
            st.plotly_chart(fig_map, use_container_width=True, config={"displayModeBar": False, "scrollZoom": True})

        section_heading("Live Shipping Transit Volume", "ship")
        count_col1, count_col2, count_col3, count_col4 = st.columns(4, gap="medium")

        # Live underway count from AISStream if available
        if ais_connected and vessel_summary:
            underway_val = str(vessel_summary.get("underway_vessels", 0))
            active_total = vessel_summary.get("active_vessels", 0)
            underway_delta = f"{active_total} observed (AISStream)"
            underway_tone = "green"
        else:
            underway_val = "N/A"
            underway_delta = "Feed unavailable"
            underway_tone = "amber"

        live_counts = [
            ("UNDERWAY", underway_val, underway_delta, underway_tone),
            ("24H TRANSITS", str(traffic_baseline["transits_24h"]), "-98.3% (sample)", "red"),
            ("WAITING", str(traffic_baseline["vessels_waiting"]), "+5 today (sample)", "amber"),
            ("THROUGHPUT", traffic_baseline["daily_throughput_dwt"], "5% baseline (sample)", "red")
        ]
        for col, (label, value, delta_text, tone) in zip([count_col1, count_col2, count_col3, count_col4], live_counts):
            with col:
                st.markdown(f'<div class="counter-card"><div class="counter-value {tone}">{escape(value)}</div><div class="counter-label">{escape(label)}</div><div class="counter-delta">{escape(delta_text)}</div></div>', unsafe_allow_html=True)
        if alert_mode:
            st.toast("High-priority maritime alert: transit volume remains below 5% of normal.", icon="⚠️")
            st.markdown('<div class="alert-strip"><span class="alert-pulse"></span><b>PRIORITY ALERT</b><span>Transit volume below baseline · Mine-risk layer active · Insurance premium elevated</span><small>LIVE FEED</small></div>', unsafe_allow_html=True)

        section_heading("Vessel Incidents · Maritime Tracker", "ship")
        vi = vessel_incidents
        total = vi["iran"] + vi["us_uk"]
        summary = f'<div class="metric-row">{metric(str(vi["iran"]), "IRAN", "red")}{metric(str(vi["us_uk"]), "US / UK", "blue")}{metric(str(vi["held"]), "HELD", "amber")}{metric(str(vi["sunk"]), "SUNK", "red")}</div><div class="sub-label" style="margin-top:12px">{vi["seizures"]} seizures · {vi["attacks"]} attacks · {vi["disabled"]} disabled · {vi["sunk_total"]} sunk</div>'
        st.markdown(panel("INCIDENT SUMMARY", summary, "alert"), unsafe_allow_html=True)
        st.progress(vi["iran"] / total)
        for date, actor, kind, target, desc in vi["log"]:
            st.markdown(timeline_item(date, actor, kind, target, desc), unsafe_allow_html=True)

        section_heading("Strike Exchange · Conflict Tracker", "shield")
        se = strike_exchange
        summary = f'<div class="metric-row">{metric(str(se["iran_irgc"]), "IRAN / IRGC", "red")}{metric(str(se["us_israel"]), "US / ISRAEL", "blue")}{metric(se["total_strikes"], "TOTAL STRIKES")}{metric(str(se["thresholds"]), "THRESHOLDS", "amber")}</div><div class="sub-label" style="margin-top:12px">{se["airstrikes"]} airstrikes · {se["missile"]} missile · {se["drone"]} drone · {se["naval"]} naval</div>'
        st.markdown(panel("EXCHANGE SUMMARY", summary, "shield"), unsafe_allow_html=True)
        st.progress(se["iran_irgc"] / (se["iran_irgc"] + se["us_israel"]))
        for date, actor, kind, target, desc in se["log"]:
            st.markdown(timeline_item(date, actor, kind, target, desc), unsafe_allow_html=True)

        g1, g2 = st.columns(2)
        with g1:
            rows = "".join(f'<div class="data-row"><span>{badge(level, "critical" if level == "CRITICAL" else "high" if level == "HIGH" else "moderate")} {escape(name)}</span><span class="mono">{escape(dep)}</span></div>' for name, level, dep in trade_impact["countries"])
            body = f'<div class="metric-row">{metric(str(trade_impact["oil_at_risk_pct"]) + "%", "WORLD OIL AT RISK", "red")}{metric(trade_impact["daily_cost_est"], "DAILY COST EST.", "amber")}</div><div style="margin-top:10px">{rows}</div>'
            st.markdown(panel("GLOBAL TRADE IMPACT", body, "globe"), unsafe_allow_html=True)
        with g2:
            importers = " ".join(badge(c, "critical") for c in lng_impact["top_importers"])
            body = f'<div class="metric-row">{metric(str(lng_impact["world_lng_at_risk_pct"]) + "%", "WORLD LNG AT RISK", "red")}{metric(lng_impact["daily_cost_est"], "DAILY COST EST.", "amber")}</div><div style="margin-top:10px">{importers}</div><div class="sub-label" style="margin-top:10px">{escape(lng_impact["note"])}</div>'
            st.markdown(panel("LNG SUPPLY IMPACT", body, "globe"), unsafe_allow_html=True)

        s1, s2 = st.columns(2)
        with s1:
            bullets = "".join(f'<li class="sub-label" style="margin-bottom:7px">{escape(b)}</li>' for b in supply_chain["bullets"])
            body = f'<div class="metric-row">{metric(supply_chain["shipping_rate_change"], "SHIPPING RATES", "red")}{metric(supply_chain["cpi_impact"], "CPI IMPACT", "amber")}{metric(supply_chain["spr_days"], "SPR RESERVE")}</div><ul style="margin:14px 0 0 18px;padding:0">{bullets}</ul>'
            st.markdown(panel("SUPPLY CHAIN DISRUPTIONS", body, "chart"), unsafe_allow_html=True)
        with s2:
            routes = "".join(f'<div class="route"><div style="display:flex;justify-content:space-between;gap:10px"><b>{escape(name)}</b><span>{badge(a, "moderate")} {badge(b, "high")}</span></div><div class="sub-label" style="margin-top:5px">{escape(desc)}</div></div>' for name, a, b, desc in alt_routes)
            st.markdown(panel("ALTERNATIVE ROUTES", routes, "ship"), unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Product pages
# -----------------------------------------------------------------------------
with tab_timeline:
    page_hero("OPERATIONS / EVENT STREAM", "Crisis Timeline", "A chronologically ordered incident stream for maritime, military, and diplomatic developments.")
    combined = [(d, a, k, v, desc) for d, a, k, v, desc in vessel_incidents["log"]] + [(d, a, k, v, desc) for d, a, k, v, desc in strike_exchange["log"]]
    combined.sort(key=lambda x: dt.datetime.strptime(x[0], "%b %d, %Y"), reverse=True)
    timeline_left, timeline_right = st.columns(2, gap="large")
    for index, event in enumerate(combined):
        with (timeline_left if index % 2 == 0 else timeline_right):
            st.markdown(timeline_item(*event), unsafe_allow_html=True)

with tab_actors:
    page_hero("NETWORK / ACTORS", "Key Actors", "The regional and international actors shaping access, risk, diplomacy, and energy flows.")
    actors = [("Iran / IRGC", "Primary regional actor. Maritime incidents and strike activity attributed to Iran/IRGC."), ("United States", "Major military actor, including naval activity and reported strikes."), ("United Kingdom", "Included in maritime incident statistics under the US/UK grouping."), ("Qatar", "Diplomatic mediator referenced in the peace-talks section."), ("Oman", "Intermediary in diplomacy and negotiation channels."), ("Saudi Arabia & UAE", "Gulf energy exporters with alternative infrastructure for rerouting.")]
    actor_cards = "".join(f'<div class="actor-card"><div class="actor-index">0{i + 1:02d}</div><div class="actor-name">{escape(name)}</div><div class="actor-rule"></div><div class="sub-label">{escape(description)}</div><div class="actor-link">VIEW PROFILE →</div></div>' for i, (name, description) in enumerate(actors))
    st.markdown(f'<div class="card-grid grid-3">{actor_cards}</div>', unsafe_allow_html=True)

with tab_blog:
    page_hero("INTELLIGENCE / ANALYSIS", "Featured Analysis", "Long-form briefs on blockade dynamics, shipping access, and escalation risk.")
    article_cards = "".join(f'<div class="article-card"><div class="article-art art-{i + 1}"><span class="badge badge-high">{escape(kind.upper())}</span></div><div class="article-content"><div class="news-meta">{escape(read_time)}</div><div class="article-title">{escape(title)}</div><div class="sub-label">{escape(summary)}</div><div class="article-link">READ BRIEF →</div></div></div>' for i, (title, kind, read_time, summary) in enumerate(analysis_items))
    st.markdown(f'<div class="card-grid grid-3">{article_cards}</div>', unsafe_allow_html=True)

with tab_news:
    page_hero("SIGNALS / MEDIA WATCH", "Latest News", "A monitored feed of market, security, and regional developments affecting Hormuz passage.")
    news_left, news_right = st.columns([1.6, 1], gap="large")
    with news_left:
        feed_items = "".join(f'<div class="news-item"><div class="news-title">{escape(title)}</div><div class="news-meta">{escape(source)} · {escape(age)}</div><div class="sub-label" style="margin-top:6px">{escape(summary)}</div></div>' for title, summary, source, age in news_items)
        st.markdown(f'<div class="feed-card"><div class="panel-title">LIVE SIGNAL FEED</div>{feed_items}</div>', unsafe_allow_html=True)
    with news_right:
        st.markdown('<div class="quote-card"><div class="page-kicker">MONITOR NOTE</div><div class="quote-mark">“</div><div class="quote-text">The Strait is not only a chokepoint. It is a live negotiation between naval power, insurance markets, and commercial patience.</div><div class="news-meta">HORMUZ INTELLIGENCE DESK · SAMPLE EDITORIAL</div></div>', unsafe_allow_html=True)

with tab_about:
    page_hero("SYSTEM / METHODOLOGY", "About the Monitor", "How this interface organizes operational, market, and geopolitical signals into one decision surface.")
    purpose_card = panel("PURPOSE", '<div class="card-title">A focused operational picture of the world’s most consequential maritime chokepoint.</div><div class="sub-label" style="margin-top:14px">The monitor brings traffic, shipping, energy and conflict indicators into one readable intelligence surface. It supports orientation and analysis—not navigation or trading decisions.</div>', "globe")

    ais_status_label = "CONNECTED (AISStream)" if ais_connected else "UNAVAILABLE (AISStream)"
    ais_status_class = "" if ais_connected else "red"
    brent_status_label = "LIVE (U.S. EIA)" if (brent_data and not brent_data.get("stale")) else ("STALE (U.S. EIA)" if brent_data else "UNAVAILABLE (U.S. EIA)")
    brent_status_class = "" if (brent_data and not brent_data.get("stale")) else "amber"

    status_card = f'''<div class="method-card"><div class="panel-title">SYSTEM STATUS</div>
        <div class="status-line"><span class="status-dot {ais_status_class}"></span>AIS TRANSIT LAYER<span>{escape(ais_status_label)}</span></div>
        <div class="status-line"><span class="status-dot {brent_status_class}"></span>ENERGY MARKET LAYER<span>{escape(brent_status_label)}</span></div>
        <div class="status-line"><span class="status-dot red"></span>INCIDENT LAYER<span>MANUAL</span></div>
        <div class="sub-label" style="margin-top:18px">Last interface refresh · UTC synchronized</div>
    </div>'''

    methodology_card = panel("DATA METHODOLOGY", '<div class="card-title">Signals are separated by source, confidence and update cadence.</div><div class="sub-label" style="margin-top:14px">Vessel tracking is connected to AISStream for live corridor activity; daily Brent spot prices are fetched from the official U.S. EIA API v2. Disruption indices and incident logs reflect verified reporting.</div>', "chart")
    disclaimer_card = panel("OPERATING BOUNDARY", '<div class="card-title">Context, not instruction.</div><div class="sub-label" style="margin-top:14px">Information may be incomplete, delayed or disputed. Do not use this monitor for navigation, safety-critical operations or financial decisions.</div>', "alert")
    st.markdown(f'<div class="about-grid">{purpose_card}{status_card}{methodology_card}{disclaimer_card}</div>', unsafe_allow_html=True)

with tab_faq:
    page_hero("REFERENCE / HELP", "Frequently Asked Questions", "Definitions and operating notes for the monitor's status, market, and flow indicators.")
    faq = [
        ("Is the vessel data live?", "Yes. Live vessel activity in the Strait of Hormuz bounding box is streamed from AISStream via WebSocket to the Flask backend, tracking active ships, underway/stationary status, and ship types. If the API key is not configured, the card clearly displays 'Live vessel feed unavailable'."),
        ("What does the closure timer show?", "It calculates the elapsed time from the CLOSED_SINCE value to the current UTC time."),
        ("What does the Brent chart show?", "It plots daily Europe Brent Spot Price FOB (RBRTE) data retrieved directly from the official U.S. Energy Information Administration (EIA) API v2 over a 45-day window."),
        ("Can the dashboard be connected to APIs?", "Yes. Vessel tracking and Brent crude pricing are fully integrated with the Flask backend API, while keeping the Streamlit layout resilient to intermittent connection outages."),
        ("What is implied flow?", "It is an estimated throughput measure derived from available transit and energy-flow indicators; it should be treated as an estimate rather than a direct count of barrels moved.")
    ]
    faq_left, faq_right = st.columns(2, gap="large")
    for i, (question, answer) in enumerate(faq):
        with (faq_left if i % 2 == 0 else faq_right):
            with st.expander(question, expanded=(i == 0)):
                st.write(answer)

st.markdown('<div class="footer">STRAIT OF HORMUZ · INFORMATION DASHBOARD · LIVE AISSTREAM & U.S. EIA INTEGRATED · NOT FOR NAVIGATION OR TRADING</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    pass
