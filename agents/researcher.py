import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from tools.search import search_web

load_dotenv()

SUMMARIZE_PROMPT = """You are a meticulous research analyst. You will receive raw web \
search results for a specific subtopic. Your job is to synthesize this information into \
a clear, factual research summary.

Guidelines:
- Write 2–4 well-structured paragraphs.
- Include key facts, statistics, expert opinions, and recent developments.
- Be objective and cite specific details from the search results.
- Do not add information that is not present in the search results.
- Write in third person, encyclopedic style."""


class ResearcherAgent:

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError("GROQ_API_KEY not found.")

        self.llm = ChatGroq(
            api_key=api_key,
            model="llama-3.3-70b-versatile",
            temperature=0.2,
        )

    def _summarize(self, subtopic: str, raw_results: str) -> str:
        if not raw_results or raw_results.startswith("Search error") or raw_results == "No results found.":
            return f"No data retrieved for '{subtopic}': {raw_results}"

        messages = [
            SystemMessage(content=SUMMARIZE_PROMPT),
            HumanMessage(
                content=(
                    f"Subtopic: {subtopic}\n\n"
                    f"Search Results:\n{raw_results}\n\n"
                    f"Write a comprehensive research summary for this subtopic."
                )
            ),
        ]

        try:
            response = self.llm.invoke(messages)
            return response.content.strip()
        except Exception as e:
            return f"Summary failed for '{subtopic}': {str(e)}"

    def run(self, plan: list[str]) -> dict[str, str]:
        if not plan:
            raise ValueError("Plan is empty.")

        research: dict[str, str] = {}
        for subtopic in plan:
            raw_results = search_web(query=subtopic, max_results=5)
            research[subtopic] = self._summarize(subtopic, raw_results)

        return research
