import argparse
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from graph.workflow import build_workflow, get_initial_state

try:
    import colorama
    colorama.init()
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    CYAN   = "\033[96m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"
except ImportError:
    GREEN = YELLOW = RED = CYAN = BOLD = RESET = ""


def print_banner():
    print(f"\n{BOLD}{CYAN}{'─' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  🔬 Multi-Agent Research & Report Generation System{RESET}")
    print(f"{BOLD}{CYAN}{'─' * 60}{RESET}")
    print(f"  Agents:  Planner → Researcher → Writer → Critic")
    print(f"  LLM:     Groq / llama-3.3-70b-versatile")
    print(f"  Search:  Tavily Web Search API")
    print(f"{CYAN}{'─' * 60}{RESET}\n")


def print_step(step_num: int, label: str, message: str, status: str = "info"):
    icons  = {"info": "⏳", "success": "✅", "error": "❌", "warn": "⚠️"}
    colors = {"info": YELLOW, "success": GREEN, "error": RED, "warn": YELLOW}
    icon  = icons.get(status, "•")
    color = colors.get(status, RESET)
    print(f"  {color}[Step {step_num}/4] {icon} {label:<14}{RESET} {message}")


def validate_environment():
    missing = [k for k in ["GROQ_API_KEY", "TAVILY_API_KEY"] if not os.getenv(k)]
    if missing:
        print(f"\n{RED}Missing environment variables:{RESET}")
        for key in missing:
            print(f"  - {key}")
        print(f"\nAdd them to your .env file and retry.\n")
        sys.exit(1)


def save_report(report: str, output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n  {GREEN}Saved to: {BOLD}{output_path}{RESET}")


def run_pipeline(topic: str, output_path: str | None = None):
    print(f"\n{BOLD}Research Topic:{RESET} {topic}\n{'─' * 60}")

    workflow = build_workflow()
    initial_state = get_initial_state(topic)

    step_map = {
        "planner":    (1, "Planner"),
        "researcher": (2, "Researcher"),
        "writer":     (3, "Writer"),
        "critic":     (4, "Critic"),
    }

    final_state = None

    for chunk in workflow.stream(initial_state):
        for node_name, updates in chunk.items():
            step_num, label = step_map.get(node_name, (0, node_name.capitalize()))
            error = updates.get("error", "")

            if node_name == "planner":
                if error:
                    print_step(step_num, label, error, "error")
                else:
                    plan = updates.get("plan", [])
                    print_step(step_num, label, f"Created plan with {len(plan)} subtopics", "success")
                    for i, subtopic in enumerate(plan, 1):
                        print(f"           {i}. {subtopic}")
                    print()

            elif node_name == "researcher":
                if error:
                    print_step(step_num, label, error, "error")
                else:
                    n = len(updates.get("research", {}))
                    print_step(step_num, label, f"Researched {n} subtopics via Tavily", "success")
                    print()

            elif node_name == "writer":
                if error:
                    print_step(step_num, label, error, "error")
                else:
                    print_step(step_num, label, "Draft report generated", "success")
                    print()

            elif node_name == "critic":
                if updates.get("final_report"):
                    print_step(step_num, label, "Report reviewed and finalized", "success")
                    final_state = updates
                else:
                    print_step(step_num, label, "Critic returned empty — using draft", "warn")
                print()

    if not final_state or not final_state.get("final_report"):
        print(f"\n{RED}Pipeline finished but no report was generated.{RESET}")
        sys.exit(1)

    final_report = final_state["final_report"]

    print(f"{'─' * 60}\n{BOLD}{GREEN}Final Research Report:{RESET}\n")
    print(final_report)
    print(f"\n{'─' * 60}")

    if output_path is None:
        safe_topic = topic[:40].strip().replace(" ", "_").replace("/", "-")
        timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"report_{safe_topic}_{timestamp}.txt"

    save_report(final_report, output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Multi-Agent Research & Report Generation System")
    parser.add_argument("--topic", type=str, default=None)
    parser.add_argument("--output", type=str, default=None)
    return parser.parse_args()


if __name__ == "__main__":
    print_banner()
    validate_environment()

    args = parse_args()
    topic = args.topic

    if not topic:
        topic = input("Enter research topic: ").strip()
        if not topic:
            print(f"\n{RED}Topic cannot be empty.{RESET}\n")
            sys.exit(1)

    try:
        run_pipeline(topic=topic, output_path=args.output)
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Interrupted.{RESET}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n{RED}Error: {e}{RESET}\n")
        sys.exit(1)
