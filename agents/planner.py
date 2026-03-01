import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

SYSTEM_PROMPT = """You are an expert research planner with deep experience in academic \
and professional research across all domains.

Your job is to decompose a broad research topic into 4–6 specific, focused subtopics \
that together provide comprehensive coverage of the subject.

Rules:
- Return ONLY a numbered list. No preamble, no headers, no explanations.
- Each subtopic should be concrete and searchable (good for web queries).
- Order subtopics logically (background → current state → applications → challenges).

Example output format:
1. Historical background and origin of [topic]
2. Core mechanisms and how [topic] works
3. Real-world applications of [topic]
4. Current challenges and limitations
5. Future directions and emerging trends"""


class PlannerAgent:

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError("GROQ_API_KEY not found.")

        self.llm = ChatGroq(
            api_key=api_key,
            model="llama-3.3-70b-versatile",
            temperature=0.3,
        )

    def run(self, topic: str) -> list[str]:
        if not topic or not topic.strip():
            raise ValueError("Research topic cannot be empty.")

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Create a research plan for: {topic}"),
        ]

        try:
            response = self.llm.invoke(messages)
            raw_output = response.content.strip()
        except Exception as e:
            raise RuntimeError(f"Planner failed: {e}") from e

        subtopics = []
        for line in raw_output.splitlines():
            line = line.strip()
            if line and line[0].isdigit():
                parts = line.split(maxsplit=1)
                if len(parts) == 2:
                    text = parts[1].strip().lstrip(".-)")
                    if text:
                        subtopics.append(text)

        return subtopics if subtopics else [topic]
