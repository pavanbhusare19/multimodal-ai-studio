
import os
import json
import ast
import operator
import logging
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

LOG_DIR = ROOT / "logs"
NOTES_DIR = ROOT / "notes"
LOG_DIR.mkdir(exist_ok=True)
NOTES_DIR.mkdir(exist_ok=True)

TRACE_FILE = LOG_DIR / "agent_traces.jsonl"
logger = logging.getLogger("researchmate_integration")


@tool
def calculate(expression: str) -> str:
    """Calculate basic arithmetic expressions."""

    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)

        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value

        if isinstance(node, ast.BinOp) and type(node.op) in operators:
            left = evaluate(node.left)
            right = evaluate(node.right)

            if isinstance(node.op, ast.Pow) and abs(right) > 8:
                raise ValueError("Exponent is too large.")

            return operators[type(node.op)](left, right)

        if isinstance(node, ast.UnaryOp) and type(node.op) in operators:
            return operators[type(node.op)](evaluate(node.operand))

        raise ValueError("Only basic arithmetic is allowed.")

    try:
        if len(expression) > 100:
            raise ValueError("Expression is too long.")

        return str(evaluate(ast.parse(expression, mode="eval")))

    except Exception as exc:
        return f"Calculation error: {exc}"


@tool
def save_research_note(title: str, note: str) -> str:
    """Save a research finding in the local notes file."""

    target = NOTES_DIR / "research_notes.md"

    with target.open("a", encoding="utf-8") as file:
        file.write(f"\n## {title.strip()}\n\n{note.strip()}\n")

    return "Saved research note successfully."


def build_agent():
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("GROQ_API_KEY is missing.")

    if not os.getenv("TAVILY_API_KEY"):
        raise RuntimeError("TAVILY_API_KEY is missing.")

    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    model = ChatGroq(model=model_name, temperature=0)
    search = TavilySearch(max_results=5)

    system_prompt = """
You are ResearchMate, a careful research and calculation assistant.

MANDATORY TOOL RULES:
1. Whenever a user requests arithmetic, you MUST call the calculate tool.
2. Never calculate arithmetic mentally or simply write a result without calling calculate.
3. Whenever a request includes both web research and arithmetic, you MUST call BOTH tools:
   - Call tavily_search for the web research.
   - Call calculate for the arithmetic.
4. Do not skip a required tool even if another tool has already been called.
5. Use the actual tool results in your final answer.
6. Never claim a tool was used unless its tool call succeeded.
7. Use save_research_note when asked to save findings.
8. Explain tool failures honestly.
9. End with a short Steps taken section.
 """

    return create_agent(
        model=model,
        tools=[search, calculate, save_research_note],
        system_prompt=system_prompt
    )


def extract_text(result):
    messages = result.get("messages", [])

    if not messages:
        return str(result)

    content = messages[-1].content

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        return "\n".join(
            str(part.get("text", part))
            if isinstance(part, dict)
            else str(part)
            for part in content
        )

    return str(content)


def extract_tool_events(result):
    events = []

    for message in result.get("messages", []):
        for call in getattr(message, "tool_calls", None) or []:
            events.append({
                "event": "tool_call",
                "tool": call.get("name", "unknown"),
                "input": call.get("args", {}),
                "reason": "Selected by the agent."
            })

        if getattr(message, "type", "") == "tool":
            events.append({
                "event": "tool_result",
                "tool": getattr(message, "name", "unknown"),
                "output_preview": str(message.content)[:500]
            })

    return events


def run_agent(question: str):
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    agent = build_agent()
    started = datetime.now().astimezone().isoformat()

    result = agent.invoke({
        "messages": [{"role": "user", "content": question.strip()}]
    })

    answer = extract_text(result)
    events = extract_tool_events(result)

    record = {
        "timestamp": started,
        "question": question,
        "tool_trace": events,
        "answer": answer
    }

    with TRACE_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")

    return answer, events
