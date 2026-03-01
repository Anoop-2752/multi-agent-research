# Pipeline: Planner → Researcher → Writer → Critic
# Each node returns only the fields it updates. Errors are stored in state["error"]
# so downstream nodes can skip gracefully instead of crashing.

from typing import TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

from agents.planner import PlannerAgent
from agents.researcher import ResearcherAgent
from agents.writer import WriterAgent
from agents.critic import CriticAgent

load_dotenv()


class ResearchState(TypedDict):
    topic: str
    plan: list[str]
    research: dict[str, str]
    draft: str
    final_report: str
    current_step: str
    error: str


def make_planner_node(agent: PlannerAgent):
    def planner_node(state: ResearchState) -> dict:
        try:
            plan = agent.run(state["topic"])
            return {"plan": plan, "current_step": "planning_complete", "error": ""}
        except Exception as e:
            return {"plan": [], "current_step": "planning_failed", "error": str(e)}
    return planner_node


def make_researcher_node(agent: ResearcherAgent):
    def researcher_node(state: ResearchState) -> dict:
        if state.get("error"):
            return {"current_step": "research_skipped"}
        try:
            research = agent.run(state["plan"])
            return {"research": research, "current_step": "research_complete", "error": ""}
        except Exception as e:
            return {"research": {}, "current_step": "research_failed", "error": str(e)}
    return researcher_node


def make_writer_node(agent: WriterAgent):
    def writer_node(state: ResearchState) -> dict:
        if state.get("error"):
            return {"current_step": "writing_skipped"}
        try:
            draft = agent.run(state["topic"], state["research"])
            return {"draft": draft, "current_step": "writing_complete", "error": ""}
        except Exception as e:
            return {"draft": "", "current_step": "writing_failed", "error": str(e)}
    return writer_node


def make_critic_node(agent: CriticAgent):
    def critic_node(state: ResearchState) -> dict:
        if state.get("error"):
            # if earlier steps failed but we still have a draft, use it as final
            if state.get("draft"):
                return {"final_report": state["draft"], "current_step": "complete_with_errors"}
            return {"current_step": "critic_skipped"}
        try:
            final_report = agent.run(state["draft"])
            return {"final_report": final_report, "current_step": "complete", "error": ""}
        except Exception as e:
            # critic failure is non-fatal — fall back to the draft
            return {
                "final_report": state.get("draft", ""),
                "current_step": "complete_with_critic_error",
                "error": str(e),
            }
    return critic_node


def build_workflow():
    planner = PlannerAgent()
    researcher = ResearcherAgent()
    writer = WriterAgent()
    critic = CriticAgent()

    graph = StateGraph(ResearchState)
    graph.add_node("planner", make_planner_node(planner))
    graph.add_node("researcher", make_researcher_node(researcher))
    graph.add_node("writer", make_writer_node(writer))
    graph.add_node("critic", make_critic_node(critic))

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "researcher")
    graph.add_edge("researcher", "writer")
    graph.add_edge("writer", "critic")
    graph.add_edge("critic", END)

    return graph.compile()


def get_initial_state(topic: str) -> ResearchState:
    return ResearchState(
        topic=topic,
        plan=[],
        research={},
        draft="",
        final_report="",
        current_step="starting",
        error="",
    )
