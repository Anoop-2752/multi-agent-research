import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

SYSTEM_PROMPT = """You are a senior editor and research quality analyst. You will receive \
a research report draft. Your job is to critically review it and produce an improved \
final version.

Review checklist (apply all fixes silently — do not include the checklist in output):
✓ Remove any vague, redundant, or padding sentences.
✓ Ensure every section has a strong opening sentence.
✓ Fix any grammatical errors or awkward phrasing.
✓ Ensure all Markdown formatting is correct and consistent.
✓ Verify the Executive Summary accurately reflects the body.
✓ Make the Conclusion punchy with actionable bullet points.
✓ Add a "---" horizontal rule between major sections for readability.
✓ Ensure the tone is professional, objective, and authoritative.

Output requirements:
- Return ONLY the final improved report in Markdown format.
- Do NOT include editorial comments, review notes, or a changelog.
- The output should be ready to publish without further editing."""


class CriticAgent:

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError("GROQ_API_KEY not found.")

        self.llm = ChatGroq(
            api_key=api_key,
            model="llama-3.3-70b-versatile",
            temperature=0.2,
        )

    def run(self, draft: str) -> str:
        if not draft or not draft.strip():
            raise ValueError("Draft is empty.")

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Review and improve this report draft:\n\n{draft}"),
        ]

        try:
            response = self.llm.invoke(messages)
            return response.content.strip()
        except Exception as e:
            raise RuntimeError(f"Critic failed: {e}") from e
