import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()


def search_web(query: str, max_results: int = 5) -> str:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY not set."

    client = TavilyClient(api_key=api_key)

    try:
        response = client.search(
            query=query,
            max_results=max_results,
            include_answer=True,
            include_raw_content=False,
        )

        parts = []
        if response.get("answer"):
            parts.append(f"Overview: {response['answer']}\n")

        for i, result in enumerate(response.get("results", []), start=1):
            title = result.get("title", "No title")
            url = result.get("url", "")
            content = result.get("content", "No content available.")
            parts.append(f"[{i}] {title}\n    URL: {url}\n    {content}\n")

        return "\n".join(parts) if parts else "No results found."

    except Exception as e:
        return f"Search error for '{query}': {str(e)}"
