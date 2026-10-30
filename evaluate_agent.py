
import json
from pathlib import Path
from datetime import datetime

from agent_integration import run_agent

ROOT = Path(__file__).parent
CASES_FILE = ROOT / "eval" / "eval_cases.json"
RESULTS_FILE = ROOT / "eval" / "latest_results.json"
REPORT_FILE = ROOT / "eval" / "EVALUATION_REPORT.md"


def main():
    cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))

    results = []

    print(f"Running {len(cases)} AI-C2 evaluation cases...\n")

    for case in cases:
        case_id = case["id"]
        prompt = case["prompt"]

        print(f"Running {case_id}...")

        try:
            answer, events = run_agent(prompt)

            used_tools = [
                event["tool"]
                for event in events
                if event["event"] == "tool_call"
            ]

            missing_tools = [
                tool for tool in case["expected_tools"]
                if tool not in used_tools
            ]

            keywords = [
                keyword.lower()
                for keyword in case["expected_any_keywords"]
            ]

            keyword_found = any(
                keyword in answer.lower()
                for keyword in keywords
            )

            passed = not missing_tools and keyword_found

            result = {
                "id": case_id,
                "prompt": prompt,
                "passed": passed,
                "expected_tools": case["expected_tools"],
                "used_tools": used_tools,
                "missing_tools": missing_tools,
                "keyword_found": keyword_found,
                "answer": answer,
                "error": None
            }

        except Exception as exc:
            result = {
                "id": case_id,
                "prompt": prompt,
                "passed": False,
                "expected_tools": case["expected_tools"],
                "used_tools": [],
                "missing_tools": case["expected_tools"],
                "keyword_found": False,
                "answer": "",
                "error": str(exc)
            }

        results.append(result)

        status = "PASS" if result["passed"] else "FAIL"
        print(f"{case_id}: {status}\n")

    passed_count = sum(item["passed"] for item in results)
    total = len(results)
    percentage = (passed_count / total * 100) if total else 0

    report = [
        "# AI-C2 Evaluation Report",
        "",
        f"Run date: {datetime.now().astimezone().isoformat()}",
        "",
        f"Pass rate: {passed_count}/{total} ({percentage:.1f}%)",
        "",
        "## Test results",
        ""
    ]

    for item in results:
        status = "PASS" if item["passed"] else "FAIL"
        report.append(f"### {item['id']} — {status}")
        report.append(f"Prompt: {item['prompt']}")
        report.append(f"Expected tools: {', '.join(item['expected_tools'])}")
        report.append(f"Used tools: {', '.join(item['used_tools']) or 'None'}")
        report.append(f"Keyword found: {item['keyword_found']}")

        if item["error"]:
            report.append(f"Error: {item['error']}")

        report.append("")

    RESULTS_FILE.write_text(
        json.dumps({
            "passed": passed_count,
            "total": total,
            "pass_rate": percentage,
            "results": results
        }, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    REPORT_FILE.write_text("\n".join(report), encoding="utf-8")

    print("=" * 40)
    print(f"AI-C2 RESULT: {passed_count}/{total}")
    print(f"PASS RATE: {percentage:.1f}%")
    print(f"Report saved: {REPORT_FILE}")


if __name__ == "__main__":
    main()
