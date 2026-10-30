import os
import json
import re
import ast
import operator
import urllib.request
from datetime import datetime

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from google import genai
from google.genai import types
from agent_integration import run_agent

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").lower()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434"
).rstrip("/")

client = (
    genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    if os.getenv("GEMINI_API_KEY")
    else None
)


# --------------------------------------------------
# GEMINI TEXT / IMAGE PROVIDER
# --------------------------------------------------

def ask_gemini(prompt, image=None, mime_type="image/jpeg"):
    if client is None:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add it to your .env file."
        )

    contents = [prompt]

    if image is not None:
        contents.append(
            types.Part.from_bytes(
                data=image,
                mime_type=mime_type
            )
        )

    response = client.models.generate_content(
        model=MODEL,
        contents=contents
    )

    return response.text or "The model returned an empty response."


# --------------------------------------------------
# OLLAMA LOCAL TEXT PROVIDER
# --------------------------------------------------

def ask_ollama(prompt):
    url = OLLAMA_BASE_URL + "/api/generate"

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            result = json.loads(response.read().decode("utf-8"))
    except Exception as error:
        raise RuntimeError(
            "Could not connect to Ollama. Make sure Ollama is running "
            f"and model '{OLLAMA_MODEL}' is installed. Details: {error}"
        )

    answer = result.get("response", "").strip()

    if not answer:
        raise RuntimeError("Ollama returned an empty response.")

    return answer


# --------------------------------------------------
# TEXT PROVIDER ROUTER
# --------------------------------------------------

def ask_text(prompt):
    if AI_PROVIDER == "ollama":
        return ask_ollama(prompt)

    if AI_PROVIDER == "gemini":
        return ask_gemini(prompt)

    raise ValueError("Invalid AI_PROVIDER. Use 'ollama' or 'gemini'.")


# --------------------------------------------------
# SAFE CALCULATOR TOOL
# --------------------------------------------------

ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow
}


def calculate_node(node):
    if isinstance(node, ast.Constant):
        if type(node.value) not in (int, float):
            raise ValueError("Only numbers are allowed.")
        return node.value

    if isinstance(node, ast.UnaryOp):
        value = calculate_node(node.operand)

        if isinstance(node.op, ast.UAdd):
            return value
        if isinstance(node.op, ast.USub):
            return -value

        raise ValueError("Unsupported unary operation.")

    if isinstance(node, ast.BinOp):
        operation = ALLOWED_OPERATORS.get(type(node.op))

        if operation is None:
            raise ValueError("Unsupported mathematical operation.")

        left = calculate_node(node.left)
        right = calculate_node(node.right)

        if isinstance(node.op, ast.Pow) and abs(right) > 10:
            raise ValueError("Exponent is too large.")

        result = operation(left, right)

        if isinstance(result, (int, float)) and abs(result) > 1e100:
            raise ValueError("Result is too large.")

        return result

    raise ValueError("Invalid mathematical expression.")


def calculator(expression):
    if len(expression) > 100:
        raise ValueError("Expression is too long.")

    tree = ast.parse(expression, mode="eval")
    return str(calculate_node(tree.body))


# --------------------------------------------------
# AGENT TOOL EXECUTION
# --------------------------------------------------

def run_agent_tool(tool_name, arguments):
    if tool_name == "calculator":
        return {
            "ok": True,
            "result": calculator(arguments.get("expression", ""))
        }

    if tool_name == "save_note":
        os.makedirs("notes", exist_ok=True)
        path = os.path.join("notes", "agent_notes.txt")

        with open(path, "a", encoding="utf-8") as file:
            file.write(
                f"\n[{datetime.now().isoformat()}] "
                f"{arguments.get('note', '')}\n"
            )

        return {"ok": True, "result": "Note saved."}

    return {"ok": False, "error": f"Unknown tool: {tool_name}"}


# --------------------------------------------------
# CONTENT PIPELINE SECTION PARSER
# --------------------------------------------------

def extract_content_sections(text):
    """
    Split the one-call model response into the four UI fields.
    If the model does not follow the requested headings, preserve
    its complete answer in the final field instead of losing content.
    """
    labels = {
        "research": r"RESEARCH",
        "outline": r"OUTLINE",
        "draft": r"DRAFT",
        "final": r"FINAL POLISHED ARTICLE"
    }

    pattern = re.compile(
        r"(?im)^\s*(?:#+\s*)?(?:\d+\s*[\).:-]\s*)?"
        r"(RESEARCH|OUTLINE|DRAFT|FINAL POLISHED ARTICLE)\s*:?\s*$"
    )

    matches = list(pattern.finditer(text))

    if len(matches) < 2:
        return {
            "research": "Included in the generated content below.",
            "outline": "Included in the generated content below.",
            "draft": "Included in the generated content below.",
            "final": text.strip()
        }

    sections = {}
    for index, match in enumerate(matches):
        heading = match.group(1).upper()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        content = text[start:end].strip()

        if heading == "RESEARCH":
            sections["research"] = content
        elif heading == "OUTLINE":
            sections["outline"] = content
        elif heading == "DRAFT":
            sections["draft"] = content
        elif heading == "FINAL POLISHED ARTICLE":
            sections["final"] = content

    if not sections.get("final"):
        sections["final"] = text.strip()

    for key in ("research", "outline", "draft"):
        sections.setdefault(
            key,
            "This section was not separately identified by the model. "
            "See the final generated content."
        )

    return sections


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

@app.get("/")
def home():
    return render_template("index.html")


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "provider": AI_PROVIDER,
        "model": OLLAMA_MODEL if AI_PROVIDER == "ollama" else MODEL,
        "gemini_api_configured": client is not None
    })


# --------------------------------------------------
# AI AGENT CHAT
# --------------------------------------------------

@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()

    if not message:
        return jsonify({"error": "Please enter a message."}), 400

    match = re.search(
        r"(?:calculate|what is)\s+([0-9+\-*/(). %]+)\??$",
        message,
        re.IGNORECASE
    )

    tool_event = None

    try:
        if match:
            expression = match.group(1).strip()
            tool_event = {
                "tool": "calculator",
                "arguments": {"expression": expression}
            }

            result = run_agent_tool("calculator", tool_event["arguments"])
            answer = result["result"] if result["ok"] else result["error"]
        else:
            answer = ask_text(
                "You are MultiModal AI Studio, a helpful AI assistant. "
                "Give accurate, clear and concise answers. "
                "If a question requires calculation, explain the steps. "
                "Do not claim to browse the internet unless a search tool is connected.\n\n"
                + message
            )

        return jsonify({
            "answer": answer,
            "tool_event": tool_event,
            "provider": AI_PROVIDER
        })

    except Exception as error:
        return jsonify({"error": str(error)}), 500


# --------------------------------------------------
# RESEARCHMATE AGENT API
# --------------------------------------------------

@app.post("/api/agent")
def researchmate_agent():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()

    if not message:
        return jsonify({
            "error": "Please enter a message."
        }), 400

    if len(message) > 10000:
        return jsonify({
            "error": "Message is too long. Maximum 10000 characters."
        }), 400

    try:
        answer, events = run_agent(message)

        return jsonify({
            "answer": answer,
            "tool_events": events,
            "agent": "ResearchMate",
            "status": "success"
        })

    except Exception as error:
        app.logger.exception("ResearchMate agent failed")
        return jsonify({
            "error": str(error),
            "agent": "ResearchMate",
            "status": "error"
        }), 500

# --------------------------------------------------
# IMAGE UNDERSTANDING - GEMINI
# --------------------------------------------------

@app.post("/api/analyze-image")
def analyze_image():
    uploaded = request.files.get("image")
    question = request.form.get(
        "question",
        "Describe this image and identify important details."
    )

    if not uploaded:
        return jsonify({"error": "Choose an image first."}), 400

    if uploaded.mimetype not in ("image/jpeg", "image/png", "image/webp"):
        return jsonify({"error": "Use a JPG, PNG, or WebP image."}), 400

    try:
        image_data = uploaded.read()

        answer = ask_gemini(
            "Analyze the uploaded image. Answer the user's question "
            "carefully. Do not guess details that are not visible.\n"
            f"Question: {question}",
            image=image_data,
            mime_type=uploaded.mimetype
        )

        return jsonify({
            "answer": answer,
            "provider": "gemini"
        })

    except Exception as error:
        return jsonify({"error": str(error)}), 500


# --------------------------------------------------
# FAST CONTENT PIPELINE - ONE MODEL REQUEST
# --------------------------------------------------

@app.post("/api/content")
def content_pipeline():
    data = request.get_json(silent=True) or {}

    topic = (data.get("topic") or "").strip()
    content_type = data.get("content_type", "Blog post")
    audience = data.get("audience", "general readers")
    tone = data.get("tone", "professional and engaging")

    if len(topic) < 4:
        return jsonify({
            "error": "Enter a topic with at least 4 characters."
        }), 400

    prompt = f"""
You are an AI content production assistant.

Create a complete content package about: {topic}

Content type: {content_type}
Target audience: {audience}
Tone: {tone}

IMPORTANT:
- Complete all four stages in this single response.
- Use the exact section headings shown below.
- Keep the research concise and do not invent citations.
- Do not pretend to have browsed the internet.
- Make the final article clear, useful, original and polished.

RESEARCH
Provide a short research brief. Identify facts that would need external verification.

OUTLINE
Create a logical outline with headings and subheadings.

DRAFT
Write a complete first draft based on the outline.

FINAL POLISHED ARTICLE
Provide the refined, publication-ready version.
"""

    try:
        # One LLM call instead of four separate calls.
        generated = ask_text(prompt)
        sections = extract_content_sections(generated)

        return jsonify({
            "research": sections["research"],
            "outline": sections["outline"],
            "draft": sections["draft"],
            "final": sections["final"],
            "provider": AI_PROVIDER
        })

    except Exception as error:
        return jsonify({"error": str(error)}), 500


# --------------------------------------------------
# EVALUATION
# --------------------------------------------------

@app.post("/api/evaluate")
def evaluate():
    checks = []

    try:
        checks.append({
            "name": "Calculator tool",
            "passed": calculator("2 + 3 * 4") == "14"
        })
    except Exception:
        checks.append({
            "name": "Calculator tool",
            "passed": False
        })

    try:
        unsafe_rejected = False
        try:
            calculator("__import__('os').system('whoami')")
        except Exception:
            unsafe_rejected = True

        checks.append({
            "name": "Unsafe expression rejected",
            "passed": unsafe_rejected
        })
    except Exception:
        checks.append({
            "name": "Unsafe expression rejected",
            "passed": False
        })

    checks.append({
        "name": "AI provider configured",
        "passed": AI_PROVIDER in ("ollama", "gemini")
    })

    checks.append({
        "name": "Gemini API configured",
        "passed": client is not None
    })

    return jsonify({
        "checks": checks,
        "passed": sum(1 for item in checks if item["passed"]),
        "total": len(checks)
    })


# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=False
    )
