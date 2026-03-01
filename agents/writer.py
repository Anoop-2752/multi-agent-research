import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

SYSTEM_PROMPT = """You are a senior technical writer and research journalist with expertise \
in producing clear, authoritative research reports.

Your task is to synthesize provided research notes into a polished, well-structured \
Markdown report. The report should be informative, engaging, and suitable for a \
professional or academic audience.

Report structure requirements:
1. # Title (descriptive, professional)
2. ## Executive Summary (2–3 sentences summarizing the entire report)
3. One ## Section per subtopic with:
   - A short introductory sentence for the section
   - The substantive content from the research notes
   - Smooth transitions
4. ## Conclusion (key takeaways and implications, 3–5 bullet points)
5. ## References (list "Web search via Tavily" as the data source)

Writing guidelines:
- Use clear, precise language — no fluff or filler.
- Use **bold** for key terms on first use.
- Keep paragraphs to 3–5 sentences.
- Do not invent facts not present in the research notes.
- Output only valid Markdown."""


def _format_research(research: dict[str, str]) -> str:
    sections = []
    for i, (subtopic, summary) in enumerate(research.items(), start=1):
        sections.append(f"### Subtopic {i}: {subtopic}\n{summary}")
    return "\n\n".join(sections)


class WriterAgent:

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError("GROQ_API_KEY not found.")

        self.llm = ChatGroq(
            api_key=api_key,
            model="llama-3.3-70b-versatile",
            temperature=0.6,
        )

    def run(self, topic: str, research: dict[str, str]) -> str:
        if not research:
            raise ValueError("No research data to write from.")

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Research Topic: {topic}\n\n"
                    f"Research Notes:\n{_format_research(research)}\n\n"
                    f"Write a comprehensive research report based on the notes above."
                )
            ),
        ]

        try:
            response = self.llm.invoke(messages)
            return response.content.strip()
        except Exception as e:
            raise RuntimeError(f"Writer failed: {e}") from e
