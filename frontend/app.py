
import sys
import os
import json
import html as html_lib

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.graph_objects as go
from datetime import date, timedelta
from pipeline import run_pipeline, ask_question



def score_color(score: float) -> str:
    if score >= 7:
        return "score-high"
    elif score >= 4:
        return "score-med"
    return "score-low"

def score_verdict(score: float) -> str:
    if score < 0:
        return "Unavailable"
    elif score >= 7:
        return "High Distortion"
    elif score >= 4:
        return "Moderate Drift"
    return "Low Drift"

def cred_color(rating: str) -> str:
    return {
        "reliable": "#27ae60",
        "mixed":    "#e67e22",
        "tabloid":  "#e74c3c",
        "unknown":  "#555555",
    }.get(rating, "#555555")

def e(text) -> str:
    return html_lib.escape(str(text))



EXAMPLES = [
    {
        "tag": "Political",
        "claim": "Imran Khan arrested May 2023",
        "date_from": "2023-05-09",
        "date_to": "2023-05-25",
        "why": "High narrative drift — origin vs 'abduction' framing",
    },
    {
        "tag": "Elections",
        "claim": "2024 Pakistan election results rigged",
        "date_from": "2024-02-08",
        "date_to": "2024-02-25",
        "why": "ARY/Geo divergence + international pickup",
    },
    {
        "tag": "Economy",
        "claim": "Pakistan IMF deal 2023",
        "date_from": "2023-06-01",
        "date_to": "2023-07-15",
        "why": "Multiple credible sources, moderate drift",
    },
]



st.set_page_config(
    page_title="Misinformation Trail Tracker",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Lora:ital,wght@0,400;0,600;1,400&display=swap');

html, body, [class*="css"] { font-family: 'Inter', system-ui, sans-serif; }

.stApp { background: #111111 !important; }
.block-container { padding-top: 2rem !important; max-width: 1100px; }

p, li, span, div, label { color: #d0d0d0; }

.masthead {
    border-bottom: 2px solid #333;
    padding-bottom: 1.25rem;
    margin-bottom: 2rem;
}
.masthead-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #555;
    margin-bottom: 0.4rem;
}
.masthead-title {
    font-family: 'Lora', Georgia, serif;
    font-size: 2.4rem;
    font-weight: 600;
    color: #f0f0f0;
    line-height: 1.15;
    margin-bottom: 0.4rem;
}
.masthead-deck { font-size: 1rem; color: #777; font-weight: 400; max-width: 680px; line-height: 1.6; }

.section-rule {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #555;
    border-bottom: 1px solid #222;
    padding-bottom: 0.4rem;
    margin: 2rem 0 1rem;
}

.score-block {
    padding: 1.5rem;
    border: 1px solid #2a2a2a;
    border-radius: 4px;
    background: #1a1a1a;
    text-align: center;
}
.score-num { font-size: 3.2rem; font-weight: 700; line-height: 1; letter-spacing: -0.02em; }
.score-label { font-size: 0.68rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; margin-top: 0.4rem; color: #555; }
.score-verdict { font-size: 0.85rem; font-weight: 600; margin-top: 0.35rem; }
.score-high { color: #e74c3c; }
.score-med  { color: #e67e22; }
.score-low  { color: #27ae60; }

.stat-box { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 4px; padding: 1.2rem 1.5rem; }
.stat-label { font-size: 0.65rem; font-weight: 600; letter-spacing: 0.09em; text-transform: uppercase; color: #555; margin-bottom: 0.25rem; }
.stat-value { font-size: 1.5rem; font-weight: 700; color: #f0f0f0; line-height: 1; }
.stat-sub { font-size: 0.75rem; color: #555; margin-top: 0.2rem; }

.framing-pair { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1rem 0; }
.framing-card { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 4px; padding: 1rem 1.25rem; }
.framing-card-label { font-size: 0.63rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.5rem; }
.label-early { color: #27ae60; }
.label-late  { color: #e74c3c; }
.framing-card p { font-size: 0.9rem; color: #bbb; line-height: 1.6; margin: 0; }

.changes-list { list-style: none; padding: 0; margin: 0.5rem 0 0; }
.changes-list li {
    font-size: 0.875rem; color: #aaa;
    padding: 0.35rem 0; border-bottom: 1px solid #1e1e1e;
    display: flex; gap: 0.6rem; align-items: flex-start;
}
.changes-list li:last-child { border-bottom: none; }
.changes-list li::before { content: '>>'; color: #444; flex-shrink: 0; font-size: 0.7rem; margin-top: 0.15rem; font-weight: 600; }

.summary-text {
    font-family: 'Lora', Georgia, serif;
    font-size: 1.0rem;
    line-height: 1.8;
    color: #ccc;
    background: #1a1a1a;
    border-left: 3px solid #444;
    padding: 1rem 1.5rem;
    border-radius: 0 4px 4px 0;
    margin: 0.75rem 0;
}

.tl-row { display: flex; gap: 1.25rem; padding: 0.7rem 0; border-bottom: 1px solid #1e1e1e; align-items: flex-start; }
.tl-row:last-child { border-bottom: none; }
.tl-date { font-size: 0.75rem; color: #555; white-space: nowrap; width: 82px; flex-shrink: 0; padding-top: 0.1rem; font-variant-numeric: tabular-nums; }
.tl-outlet { font-size: 0.82rem; font-weight: 600; color: #e0e0e0; }
.tl-title { font-size: 0.81rem; color: #777; margin-top: 0.1rem; line-height: 1.4; }

.origin-card { background: #1a1a1a; border: 1px solid #2a2a2a; border-top: 3px solid #e0e0e0; border-radius: 0 0 4px 4px; padding: 1rem 1.25rem; }
.origin-tag { font-size: 0.6rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: #555; margin-bottom: 0.3rem; }
.origin-outlet { font-size: 1rem; font-weight: 700; color: #f0f0f0; }
.origin-headline { font-size: 0.875rem; color: #888; margin-top: 0.2rem; font-style: italic; }
.origin-date { font-size: 0.75rem; color: #555; margin-top: 0.25rem; }

.cred-bar-row { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem; font-size: 0.82rem; }
.cred-bar-label { width: 70px; color: #666; }
.cred-bar-track { flex: 1; height: 5px; background: #222; border-radius: 3px; overflow: hidden; }
.cred-bar-fill { height: 100%; border-radius: 3px; }
.cred-bar-count { color: #555; width: 28px; text-align: right; font-size: 0.78rem; }

.qa-block { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 4px; padding: 1.25rem 1.5rem; font-size: 0.9rem; line-height: 1.8; color: #ccc; white-space: pre-wrap; }

.example-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; margin: 0.5rem 0 1.5rem; }
.example-card { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 4px; padding: 0.9rem 1rem; cursor: pointer; }
.example-card:hover { border-color: #444; }
.example-claim { font-size: 0.88rem; font-weight: 600; color: #e0e0e0; margin-bottom: 0.3rem; }
.example-dates { font-size: 0.72rem; color: #555; }
.example-tag { font-size: 0.62rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #888; margin-bottom: 0.4rem; }

input, textarea, select { background: #1a1a1a !important; color: #f0f0f0 !important; border-color: #333 !important; }
.stTextInput input { background: #1a1a1a !important; color: #f0f0f0 !important; }

hr { border-color: #222 !important; }

.stCaption p { color: #555 !important; }

.streamlit-expanderHeader { color: #aaa !important; }

.stTab { color: #aaa !important; }

.stDeployButton { display: none; }
</style>
<div class="masthead">
  <div class="masthead-label">South Asian Media Intelligence</div>
  <div class="masthead-title">Misinformation Trail Tracker</div>
  <div class="masthead-deck">Enter any claim. See where it started, how it spread, and what changed along the way — traced across Pakistani and South Asian news sources.</div>
</div>
""", unsafe_allow_html=True)



st.markdown('<div class="example-grid">', unsafe_allow_html=True)
for ex in EXAMPLES:
    st.markdown(f"""
    <div class="example-card">
        <div class="example-tag">{e(ex['tag'])}</div>
        <div class="example-claim">{e(ex['claim'])}</div>
        <div class="example-dates">{e(ex['date_from'])}  to  {e(ex['date_to'])}</div>
        <div style="font-size:0.72rem;color:#444;margin-top:0.3rem;">{e(ex['why'])}</div>
    </div>""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

ex_cols = st.columns(3)
for i, (col, ex) in enumerate(zip(ex_cols, EXAMPLES)):
    with col:
        if st.button(f"Use example {i+1}", key=f"ex_{i}", use_container_width=True):
            st.session_state["prefill_claim"]     = ex["claim"]
            st.session_state["prefill_date_from"] = date.fromisoformat(ex["date_from"])
            st.session_state["prefill_date_to"]   = date.fromisoformat(ex["date_to"])
            st.rerun()

st.markdown('<div class="section-rule">Analyze a claim</div>', unsafe_allow_html=True)

prefill_claim     = st.session_state.get("prefill_claim", "")
prefill_date_from = st.session_state.get("prefill_date_from", date.today() - timedelta(days=30))
prefill_date_to   = st.session_state.get("prefill_date_to",   date.today())

with st.form("analyze_form"):
    claim_input = st.text_input(
        "Claim",
        value=prefill_claim,
        placeholder="e.g. ECP deleted votes in 2024 election",
        label_visibility="collapsed",
    )
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        date_from = st.date_input("From", value=prefill_date_from)
    with c2:
        date_to = st.date_input("To", value=prefill_date_to)
    with c3:
        st.write("")
        submitted = st.form_submit_button("Analyze", use_container_width=True, type="primary")

st.divider()

if "result" not in st.session_state:
    st.session_state.result = None

if submitted and claim_input.strip():
    with st.spinner("Fetching articles and analyzing — takes 20-60 seconds..."):
        try:
            st.session_state.result = run_pipeline(claim_input.strip(), str(date_from), str(date_to))
        except Exception as ex:
            st.error(f"Something went wrong: {ex}")
            st.stop()
elif submitted:
    st.warning("Please enter a claim to analyze.")

result = st.session_state.result
if not result:
    st.stop()

if "error" in result:
    st.error(result["error"])
    st.stop()

mutation    = result.get("mutation", {})
timeline    = result.get("timeline", {})
credibility = result.get("credibility", {})
score       = float(mutation.get("mutation_score", -1))
origin      = timeline.get("origin") or {}



st.markdown('<div class="section-rule">Summary</div>', unsafe_allow_html=True)
col_score, col_articles, col_first, col_outlet = st.columns(4)

with col_score:
    sc = score_color(score)
    display = f"{score:.1f}/10" if score >= 0 else "N/A"
    st.markdown(f"""<div class="score-block">
        <div class="score-num {sc}">{display}</div>
        <div class="score-label">Mutation Score</div>
        <div class="score-verdict {sc}">{score_verdict(score)}</div>
    </div>""", unsafe_allow_html=True)

with col_articles:
    st.markdown(f"""<div class="stat-box">
        <div class="stat-label">Articles Found</div>
        <div class="stat-value">{result.get("total_articles", 0)}</div>
        <div class="stat-sub">across {len(result.get("queries_used", []))} search queries</div>
    </div>""", unsafe_allow_html=True)

with col_first:
    st.markdown(f"""<div class="stat-box">
        <div class="stat-label">First Seen</div>
        <div class="stat-value" style="font-size:1.1rem;">{e(timeline.get("origin_date", "—"))}</div>
        <div class="stat-sub">earliest article date</div>
    </div>""", unsafe_allow_html=True)

with col_outlet:
    st.markdown(f"""<div class="stat-box">
        <div class="stat-label">Origin Outlet</div>
        <div class="stat-value" style="font-size:1rem;line-height:1.2;">{e(origin.get("outlet", "—"))}</div>
        <div class="stat-sub">broke the story first</div>
    </div>""", unsafe_allow_html=True)



st.markdown('<div class="section-rule">How the Story Changed</div>', unsafe_allow_html=True)

summary = mutation.get("mutation_summary", "")
if summary:
    st.markdown(f'<div class="summary-text">{e(summary)}</div>', unsafe_allow_html=True)

early_f = mutation.get("early_framing", "")
late_f  = mutation.get("late_framing", "")
if early_f or late_f:
    st.markdown(f"""<div class="framing-pair">
        <div class="framing-card">
            <div class="framing-card-label label-early">Early framing</div>
            <p>{e(early_f)}</p>
        </div>
        <div class="framing-card">
            <div class="framing-card-label label-late">Late framing</div>
            <p>{e(late_f)}</p>
        </div>
    </div>""", unsafe_allow_html=True)

changes = mutation.get("key_changes", [])
if changes:
    items = "".join(f"<li>{e(c)}</li>" for c in changes)
    st.markdown(f'<ul class="changes-list">{items}</ul>', unsafe_allow_html=True)



if origin:
    st.markdown('<div class="section-rule">Origin Article</div>', unsafe_allow_html=True)
    url = e(origin.get("url", "#"))
    st.markdown(f"""<div class="origin-card">
        <div class="origin-tag">First known coverage</div>
        <div class="origin-outlet">{e(origin.get("outlet", "Unknown"))}</div>
        <div class="origin-headline">"{e(origin.get("title", ""))}"</div>
        <div class="origin-date">{e(origin.get("date", ""))} &nbsp;·&nbsp; <a href="{url}" target="_blank" style="color:#555;text-decoration:underline;">View article</a></div>
    </div>""", unsafe_allow_html=True)



st.markdown('<div class="section-rule">Coverage Timeline</div>', unsafe_allow_html=True)

buckets = timeline.get("buckets", [])
tab_labels = [f"{b['label']} ({len(b['articles'])})" for b in buckets if b["articles"]]
tabs = st.tabs(tab_labels) if tab_labels else []

bucket_idx = 0
for bucket in buckets:
    arts = bucket.get("articles", [])
    if not arts:
        continue
    with tabs[bucket_idx]:
        rows = ""
        for a in arts[:10]:
            r = a.get("credibility", "unknown")
            dot_color = cred_color(r)
            rows += f"""<div class="tl-row">
                <div class="tl-date">{e(a.get("date", ""))}</div>
                <div>
                    <div class="tl-outlet"><span style="color:{dot_color};font-size:0.6rem;">&#9679;</span> {e(a.get("outlet", "?"))}</div>
                    <div class="tl-title">{e(a.get("title", "")[:130])}</div>
                </div>
            </div>"""
        st.markdown(rows, unsafe_allow_html=True)
        if len(arts) > 10:
            st.caption(f"Showing 10 of {len(arts)} articles in this period.")
    bucket_idx += 1



st.markdown('<div class="section-rule">Source Credibility</div>', unsafe_allow_html=True)

cred_left, cred_right = st.columns([1, 2])
breakdown = credibility.get("breakdown", {})
total = credibility.get("total", 1) or 1

with cred_left:
    for lbl in ["reliable", "mixed", "tabloid", "unknown"]:
        count = breakdown.get(lbl, 0)
        pct = round(count / total * 100)
        fc = cred_color(lbl)
        st.markdown(f"""<div class="cred-bar-row">
            <div class="cred-bar-label">{lbl.capitalize()}</div>
            <div class="cred-bar-track"><div class="cred-bar-fill" style="width:{pct}%;background:{fc};"></div></div>
            <div class="cred-bar-count">{count}</div>
        </div>""", unsafe_allow_html=True)

    top = credibility.get("top_sources", [])
    if top:
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("Most cited outlets:")
        for s in top:
            st.markdown(f"**{e(s['outlet'])}** — {s['count']} articles")

with cred_right:
    labels = ["reliable", "mixed", "tabloid", "unknown"]
    vals   = [breakdown.get(l, 0) for l in labels]
    colors = [cred_color(l) for l in labels]
    fig = go.Figure(go.Pie(
        labels=[l.capitalize() for l in labels],
        values=vals,
        hole=0.6,
        marker=dict(colors=colors, line=dict(color="#111", width=3)),
        textinfo="percent",
        textfont=dict(size=12, color="#ccc"),
        direction="clockwise",
        sort=False,
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ccc"),
        showlegend=False,
        margin=dict(t=10, b=10, l=10, r=10),
        height=200,
    )
    st.plotly_chart(fig, use_container_width=True)



st.divider()
st.subheader("Ask about these articles")
st.caption("Answers are drawn only from the articles fetched above — no guessing.")

with st.form("qa_form"):
    qa_q  = st.text_input("Question", placeholder="How was the story described in the first 3 days?", label_visibility="collapsed")
    qa_go = st.form_submit_button("Ask")

if qa_go and qa_q.strip():
    with st.spinner("Looking through articles..."):
        qa_result = ask_question(qa_q.strip())
    st.markdown(f'<div class="qa-block">{e(qa_result.get("answer", "No answer."))}</div>', unsafe_allow_html=True)
    with st.expander("Sources used"):
        for s in qa_result.get("sources", []):
            url = s.get("url", "")
            link = f" [(link)]({url})" if url else ""
            st.markdown(f"**{e(s.get('outlet', '?'))}** — {e(s.get('date', ''))}{link}")



st.divider()
st.download_button(
    "Download full report (JSON)",
    data=json.dumps(result, indent=2, default=str),
    file_name=f"report_{result['claim'][:30].replace(' ', '_')}.json",
    mime="application/json",
)
