"""Usage: python -m ai_eval.run_eval --responses ai_eval/responses/responses_v1.json --label v1

Scores a set of recorded model responses against the prompt suite, appends the run to reports/run_history.json,
and writes a Jira-importable CSV of failures. To evaluate a live model, generate a responses JSON
({prompt_id: response_text}) with your model of choice and pass it in.
"""
import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import yaml

from ai_eval.evaluators import evaluate

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "ai_eval" / "prompts" / "test_prompts.yaml"
HISTORY = ROOT / "reports" / "run_history.json"


def run(responses: dict, label: str) -> dict:
    cases = yaml.safe_load(PROMPTS.read_text())
    results = [evaluate(c, responses.get(c["id"])) for c in cases]
    by_cat = defaultdict(lambda: [0, 0])
    for r in results:
        by_cat[r["category"]][0] += 1
        by_cat[r["category"]][1] += r["passed"]
    return {"label": label, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total": len(results), "passed": sum(r["passed"] for r in results),
            "by_category": {k: {"total": v[0], "passed": v[1]} for k, v in by_cat.items()},
            "results": results}


def save_run(run_data: dict, history_path: Path = HISTORY) -> None:
    history = json.loads(history_path.read_text()) if history_path.exists() else []
    history = [h for h in history if h["label"] != run_data["label"]] + [run_data]
    history_path.parent.mkdir(exist_ok=True)
    history_path.write_text(json.dumps(history, indent=2))


def write_jira_csv(run_data: dict, path: Path) -> int:
    """CSV with Summary / Description / Priority / Labels columns for Jira's CSV importer."""
    cases = {c["id"]: c for c in yaml.safe_load(PROMPTS.read_text())}
    failed = [r for r in run_data["results"] if not r["passed"]]
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Summary", "Description", "Priority", "Labels"])
        for r in failed:
            guard = r["category"] in ("Guardrails", "Privacy")
            reasons = "; ".join(f"{k}: {v}" for k, v in r["failures"].items())
            w.writerow([f"[AI eval {run_data['label']}] {r['id']} failed ({r['category']})",
                        f"Prompt: {cases[r['id']]['prompt']}\nFailures: {reasons}",
                        "High" if guard else "Medium", f"ai-eval,{r['category'].lower().replace(' ', '-')}"])
    return len(failed)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--responses", required=True)
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    data = run(json.loads(Path(a.responses).read_text()), a.label)
    save_run(data)
    n = write_jira_csv(data, ROOT / "reports" / f"failures_{a.label}.csv")
    print(f"{a.label}: {data['passed']}/{data['total']} passed, {n} failures exported")
    for r in data["results"]:
        if not r["passed"]:
            print(f"  FAIL {r['id']} ({r['category']}): {r['failures']}")
