import streamlit as st
from datetime import datetime
from graph.workflow import build_workflow, get_initial_state

st.set_page_config(
    page_title="Multi-Agent Research System",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .main-title {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0;
    }
    .report-container {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 2rem;
        margin-top: 1rem;
    }
    hr { border-color: #e2e8f0; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="main-title">🔬 Multi-Agent Research System</p>', unsafe_allow_html=True)
st.markdown(
    "Powered by **LangGraph** · **Groq (llama-3.3-70b)** · **Tavily Search**  \n"
    "_Enter a topic and let 4 AI agents collaborate to produce a research report._"
)
st.divider()

if "final_report" not in st.session_state:
    st.session_state.final_report = None
if "research_topic" not in st.session_state:
    st.session_state.research_topic = ""
if "run_complete" not in st.session_state:
    st.session_state.run_complete = False

col_input, col_btn = st.columns([4, 1])
with col_input:
    topic = st.text_input(
        label="Research Topic",
        placeholder="e.g. The future of quantum computing in cryptography",
        label_visibility="collapsed",
    )
with col_btn:
    generate_clicked = st.button(
        "Generate Report",
        type="primary",
        use_container_width=True,
        disabled=not topic.strip(),
    )

if generate_clicked and topic.strip():
    st.session_state.final_report = None
    st.session_state.run_complete = False
    st.session_state.research_topic = topic.strip()

    st.divider()

    col_progress, col_output = st.columns([1, 2])

    with col_progress:
        st.markdown("### 🤖 Agent Pipeline")
        status_planner    = st.empty()
        status_researcher = st.empty()
        status_writer     = st.empty()
        status_critic     = st.empty()

        status_planner.markdown("⬜ **Planner** — waiting")
        status_researcher.markdown("⬜ **Researcher** — waiting")
        status_writer.markdown("⬜ **Writer** — waiting")
        status_critic.markdown("⬜ **Critic** — waiting")

    with col_output:
        st.markdown("### 📋 Live Output")
        live_box = st.empty()
        live_box.info("Starting pipeline…")

    try:
        workflow = build_workflow()
        initial_state = get_initial_state(topic.strip())

        for chunk in workflow.stream(initial_state):
            for node_name, updates in chunk.items():

                if node_name == "planner":
                    plan = updates.get("plan", [])
                    if updates.get("error"):
                        status_planner.markdown("🔴 **Planner** — failed")
                        live_box.error(f"Planner error: {updates['error']}")
                    else:
                        status_planner.markdown("✅ **Planner** — done")
                        plan_text = "\n".join(f"- {s}" for s in plan)
                        live_box.success(f"**Research Plan Created** ({len(plan)} subtopics)\n\n{plan_text}")

                elif node_name == "researcher":
                    research = updates.get("research", {})
                    if updates.get("error"):
                        status_researcher.markdown("🔴 **Researcher** — failed")
                        live_box.error(f"Researcher error: {updates['error']}")
                    else:
                        status_researcher.markdown("✅ **Researcher** — done")
                        live_box.success(f"**Web Research Complete** — gathered data for {len(research)} subtopics")

                elif node_name == "writer":
                    if updates.get("error"):
                        status_writer.markdown("🔴 **Writer** — failed")
                        live_box.error(f"Writer error: {updates['error']}")
                    else:
                        status_writer.markdown("✅ **Writer** — done")
                        live_box.success("**Draft Report Generated** — sending to Critic for review…")

                elif node_name == "critic":
                    final = updates.get("final_report", "")
                    if final:
                        status_critic.markdown("✅ **Critic** — done")
                        live_box.success("**Report finalized!** Scroll down to read.")
                        st.session_state.final_report = final
                        st.session_state.run_complete = True
                    else:
                        status_critic.markdown("🔴 **Critic** — failed")
                        live_box.error("Critic agent returned an empty report.")

    except Exception as e:
        st.error(f"Pipeline failed: {str(e)}")
        st.exception(e)

if st.session_state.run_complete and st.session_state.final_report:
    st.divider()

    report_col, download_col = st.columns([5, 1])
    with report_col:
        st.markdown("## 📄 Final Research Report")
    with download_col:
        safe_topic = (
            st.session_state.research_topic[:40]
            .strip()
            .replace(" ", "_")
            .replace("/", "-")
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="⬇ Download",
            data=st.session_state.final_report,
            file_name=f"report_{safe_topic}_{timestamp}.txt",
            mime="text/plain",
            use_container_width=True,
            type="secondary",
        )

    with st.container():
        st.markdown('<div class="report-container">', unsafe_allow_html=True)
        st.markdown(st.session_state.final_report)
        st.markdown("</div>", unsafe_allow_html=True)

    st.caption(
        f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')} · "
        f"Topic: _{st.session_state.research_topic}_"
    )

with st.sidebar:
    st.markdown("### About")
    st.markdown(
        """
        **Multi-Agent Research System** orchestrates 4 AI agents in sequence
        to autonomously research any topic and produce a structured report.

        **Agent Pipeline:**
        1. 🧠 **Planner** — Decomposes topic into subtopics
        2. 🔍 **Researcher** — Searches web via Tavily
        3. ✍️ **Writer** — Drafts structured Markdown report
        4. 🎯 **Critic** — Reviews and polishes the report

        **Tech Stack:**
        - [LangGraph](https://github.com/langchain-ai/langgraph) — Agent orchestration
        - [Groq](https://groq.com) — LLM inference (llama-3.3-70b)
        - [Tavily](https://tavily.com) — AI web search
        - [Streamlit](https://streamlit.io) — Frontend UI
        - [LangSmith](https://smith.langchain.com) — Tracing & monitoring
        """
    )
    st.divider()
    st.markdown("Built as an AI Engineer portfolio project.")
