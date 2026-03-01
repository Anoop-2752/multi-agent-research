import time
import streamlit as st
from datetime import datetime
from graph.workflow import build_workflow, get_initial_state
from tools.pdf_export import generate_pdf

st.set_page_config(
    page_title="Multi-Agent Research System",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Password gate ──────

pwd = st.text_input("Enter password to access the app", type="password")
if pwd != st.secrets.get("APP_PASSWORD", ""):
    st.stop()

st.markdown("""
<style>
.hero {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    padding: 2.5rem 2.5rem 2rem;
    border-radius: 16px;
    margin-bottom: 1.8rem;
    color: white;
}
.hero h1 {
    color: white;
    font-size: 2.1rem;
    margin: 0 0 0.4rem;
    font-weight: 800;
    letter-spacing: -0.5px;
}
.hero p { color: #a5b4fc; margin: 0; font-size: 1rem; }
.hero .badge {
    display: inline-block;
    background: rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 20px;
    padding: 0.2rem 0.7rem;
    font-size: 0.78rem;
    color: #c7d2fe;
    margin: 0.8rem 0.3rem 0 0;
}

.step-card {
    border-radius: 14px;
    padding: 1.2rem 0.8rem;
    text-align: center;
    min-height: 115px;
    border: 2px solid transparent;
    transition: all 0.3s ease;
}
.step-card.waiting {
    background: linear-gradient(145deg, #1e1b4b, #2e2a6e);
    border-color: #4338ca;
}
.step-card.running {
    background: linear-gradient(145deg, #4338ca, #6366f1);
    border-color: #818cf8;
    box-shadow: 0 0 0 4px rgba(99,102,241,0.25), 0 4px 15px rgba(67,56,202,0.4);
}
.step-card.done {
    background: linear-gradient(145deg, #1e1b4b, #3730a3);
    border-color: #4338ca;
    box-shadow: 0 4px 12px rgba(55,48,163,0.3);
}
.step-card.failed {
    background: linear-gradient(145deg, #991b1b, #dc2626);
    border-color: #f87171;
}

.step-icon   { font-size: 1.6rem; margin-bottom: 0.3rem; }
.step-name   { font-weight: 700; font-size: 0.95rem; }
.step-status { font-size: 0.78rem; margin-top: 0.2rem; }

.metric-box {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.metric-val   { font-size: 2rem; font-weight: 800; color: #4338ca; line-height: 1; }
.metric-label { font-size: 0.8rem; color: #64748b; margin-top: 0.3rem; }

.example-btn button {
    background: #ede9fe !important;
    color: #5b21b6 !important;
    border: 1px solid #ddd6fe !important;
    border-radius: 20px !important;
    font-size: 0.83rem !important;
}
.example-btn button:hover {
    background: #ddd6fe !important;
}

.report-wrap {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 2.5rem 3rem;
    line-height: 1.8;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
</style>
""", unsafe_allow_html=True)

# ── Hero ─────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="hero">
    <h1>🔬 Multi-Agent Research System</h1>
    <p>Four AI agents collaborate to research any topic and generate a structured report</p>
    <span class="badge">LangGraph</span>
    <span class="badge">Groq llama-3.3-70b</span>
    <span class="badge">Tavily Search</span>
    <span class="badge">LangSmith</span>
</div>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────

defaults = {
    "final_report": None,
    "run_complete": False,
    "research_topic": "",
    "plan": [],
    "research": {},
    "metrics": {},
    "prefill_topic": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Input ─────────────────────────────────────────────────────────────────────

col_in, col_btn = st.columns([5, 1])
with col_in:
    topic = st.text_input(
        "topic",
        value=st.session_state.prefill_topic,
        placeholder="e.g.  The impact of AI on the future of work",
        label_visibility="collapsed",
    )
with col_btn:
    go = st.button("Generate →", type="primary", use_container_width=True, disabled=not topic.strip())

# Example topic chips
st.markdown("<p style='margin:0.6rem 0 0.3rem;font-size:0.85rem;color:#64748b'>Try an example:</p>", unsafe_allow_html=True)
examples = [
    "Future of quantum computing",
    "AI in healthcare",
    "Climate change solutions",
    "Rise of autonomous vehicles",
]
ex_cols = st.columns(len(examples))
for i, (col, ex) in enumerate(zip(ex_cols, examples)):
    with col:
        st.markdown('<div class="example-btn">', unsafe_allow_html=True)
        if st.button(ex, key=f"ex_{i}", use_container_width=True):
            st.session_state.prefill_topic = ex
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# ── Pipeline step cards ────────────────────────────────────────────────────────

AGENTS = [
    ("1️⃣", "Planner",    "Breaks topic into subtopics"),
    ("2️⃣", "Researcher", "Searches web for each subtopic"),
    ("3️⃣", "Writer",     "Drafts the structured report"),
    ("4️⃣", "Critic",     "Reviews and polishes"),
]

def render_step(icon, name, desc, status="waiting"):
    status_icons   = {"waiting": "⬜", "running": "🔄", "done": "✅", "failed": "🔴"}
    status_labels  = {"waiting": "Waiting", "running": "Running…", "done": "Done", "failed": "Failed"}
    # waiting uses dark text; running/done/failed use white text
    text_color = "#ffffff"
    sub_color  = "rgba(255,255,255,0.6)"
    return f"""
    <div class="step-card {status}">
        <div class="step-icon">{icon}</div>
        <div class="step-name" style="color:{text_color}">{name}</div>
        <div class="step-status" style="color:{sub_color}">{status_icons[status]} {status_labels[status]}</div>
        <div style="font-size:0.72rem;color:{sub_color};margin-top:0.25rem">{desc}</div>
    </div>"""

st.markdown("#### Agent Pipeline")
pipeline_cols = st.columns(4)
placeholders = []
for col, (icon, name, desc) in zip(pipeline_cols, AGENTS):
    with col:
        ph = st.empty()
        ph.markdown(render_step(icon, name, desc, "waiting"), unsafe_allow_html=True)
        placeholders.append((ph, icon, name, desc))

# ── Run the pipeline ──────────────────────────────────────────────────────────

if go and topic.strip():
    # Reset state for a fresh run
    for k in ("final_report", "plan", "research", "metrics", "run_complete"):
        st.session_state[k] = None if k == "final_report" else ({} if k in ("research", "metrics") else ([] if k == "plan" else False))
    st.session_state.research_topic = topic.strip()
    st.session_state.prefill_topic = topic.strip()

    status_map = {"planner": 0, "researcher": 1, "writer": 2, "critic": 3}
    start_time = time.time()

    progress_bar = st.progress(0, text="Starting pipeline…")

    try:
        workflow = build_workflow()
        initial_state = get_initial_state(topic.strip())

        for chunk in workflow.stream(initial_state):
            for node_name, updates in chunk.items():
                idx = status_map.get(node_name, -1)
                error = updates.get("error", "")

                # Mark current node as running first, then done/failed
                if idx >= 0:
                    ph, icon, name, desc = placeholders[idx]
                    if error:
                        ph.markdown(render_step(icon, name, desc, "failed"), unsafe_allow_html=True)
                    else:
                        ph.markdown(render_step(icon, name, desc, "done"), unsafe_allow_html=True)

                    progress_bar.progress((idx + 1) / 4, text=f"Step {idx+1}/4 — {name} complete")

                # Collect outputs into session state
                if node_name == "planner" and not error:
                    st.session_state.plan = updates.get("plan", [])

                elif node_name == "researcher" and not error:
                    st.session_state.research = updates.get("research", {})

                elif node_name == "critic":
                    final = updates.get("final_report", "")
                    if final:
                        elapsed = round(time.time() - start_time)
                        words = len(final.split())
                        sections = final.count("\n## ")
                        st.session_state.final_report = final
                        st.session_state.run_complete = True
                        st.session_state.metrics = {
                            "subtopics": len(st.session_state.plan),
                            "words": words,
                            "sections": sections,
                            "time": f"{elapsed}s",
                        }

        progress_bar.progress(1.0, text="✅ Pipeline complete!")

    except Exception as e:
        st.error(f"Pipeline failed: {str(e)}")
        st.exception(e)

# ── Results ───────────────────────────────────────────────────────────────────

if st.session_state.run_complete and st.session_state.final_report:
    st.divider()

    # Metrics row
    m = st.session_state.metrics
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="metric-box"><div class="metric-val">{m.get("subtopics","—")}</div><div class="metric-label">Subtopics Researched</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-box"><div class="metric-val">{m.get("words","—")}</div><div class="metric-label">Words in Report</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-box"><div class="metric-val">{m.get("sections","—")}</div><div class="metric-label">Report Sections</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="metric-box"><div class="metric-val">{m.get("time","—")}</div><div class="metric-label">Time Taken</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Output tabs
    tab_report, tab_plan, tab_research = st.tabs(["📄 Final Report", "📋 Research Plan", "🔍 Research Notes"])

    with tab_report:
        safe = st.session_state.research_topic[:35].replace(" ", "_").replace("/", "-")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        btn_txt, btn_pdf, _ = st.columns([1, 1, 4])
        with btn_txt:
            st.download_button(
                "⬇ Download .txt",
                data=st.session_state.final_report,
                file_name=f"report_{safe}_{ts}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with btn_pdf:
            try:
                pdf_bytes = generate_pdf(
                    st.session_state.final_report,
                    st.session_state.research_topic,
                )
                st.download_button(
                    "⬇ Download .pdf",
                    data=pdf_bytes,
                    file_name=f"report_{safe}_{ts}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.warning(f"PDF generation failed: {e}")
        st.markdown('<div class="report-wrap">', unsafe_allow_html=True)
        st.markdown(st.session_state.final_report)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_plan:
        if st.session_state.plan:
            st.markdown(f"**{len(st.session_state.plan)} subtopics identified for:** _{st.session_state.research_topic}_")
            st.divider()
            for i, subtopic in enumerate(st.session_state.plan, 1):
                st.markdown(f"**{i}.** {subtopic}")
        else:
            st.info("Plan data not available.")

    with tab_research:
        if st.session_state.research:
            for subtopic, summary in st.session_state.research.items():
                with st.expander(f"🔍 {subtopic}"):
                    st.markdown(summary)
        else:
            st.info("Research data not available.")

    st.caption(
        f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')} · "
        f"Topic: _{st.session_state.research_topic}_"
    )
