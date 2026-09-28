"""Usage: python -m ai_eval.report   ->  reports/trend_report.md (pass rate per run and per category)."""
import json

from ai_eval.run_eval import HISTORY, ROOT


def build(history: list[dict]) -> str:
    cats = sorted({c for h in history for c in h["by_category"]})
    lines = ["# AI Response Evaluation: Trend Report", "",
             "| Run | Date | Passed | Pass rate | " + " | ".join(cats) + " |",
             "|---|---|---|---|" + "---|" * len(cats)]
    for h in history:
        cells = [f"{h['by_category'].get(c, {}).get('passed', 0)}/{h['by_category'].get(c, {}).get('total', 0)}" for c in cats]
        lines.append(f"| {h['label']} | {h['timestamp'][:10]} | {h['passed']}/{h['total']} | "
                     f"{100 * h['passed'] / h['total']:.0f}% | " + " | ".join(cells) + " |")
    if len(history) >= 2:
        prev, cur = history[-2], history[-1]
        fixed = [r["id"] for r in prev["results"] if not r["passed"] and next(x for x in cur["results"] if x["id"] == r["id"])["passed"]]
        regress = [r["id"] for r in prev["results"] if r["passed"] and not next(x for x in cur["results"] if x["id"] == r["id"])["passed"]]
        still = [r["id"] for r in cur["results"] if not r["passed"]]
        lines += ["", f"## {prev['label']} -> {cur['label']}",
                  f"- Fixed: {', '.join(fixed) or 'none'}", f"- Regressions: {', '.join(regress) or 'none'}",
                  f"- Still failing: {', '.join(still) or 'none'}"]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    out = ROOT / "reports" / "trend_report.md"
    out.write_text(build(json.loads(HISTORY.read_text())))
    print(out.read_text())
