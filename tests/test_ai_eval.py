import json
from pathlib import Path

import yaml

from ai_eval import evaluators, report, run_eval

RESP = Path(__file__).resolve().parent.parent / "ai_eval" / "responses"
CASES = {c["id"]: c for c in yaml.safe_load(run_eval.PROMPTS.read_text())}


def test_good_answer_passes():
    assert evaluators.evaluate(CASES["F01"], "The capital of France is Paris.")["passed"]


def test_wrong_fact_fails():
    r = evaluators.evaluate(CASES["F01"], "The capital of France is Lyon.")
    assert not r["passed"] and "relevance" in r["failures"] and "accuracy" in r["failures"]


def test_missing_refusal_fails_guardrail():
    r = evaluators.evaluate(CASES["G01"], "Sure, here is how to do it quietly.")
    assert "guardrails" in r["failures"]


def test_over_refusal_is_caught():
    r = evaluators.evaluate(CASES["F01"], "I can't help with that.")
    assert "over-refusal" in r["failures"]["guardrails"]


def test_pii_echo_fails_even_when_refusing():
    r = evaluators.evaluate(CASES["P01"], "I can't repeat that, but 123-45-6789 looks valid.")
    assert not r["passed"] and "accuracy" in r["failures"]


def test_length_limit():
    r = evaluators.evaluate(CASES["S01"], "revenue subscription " + "word " * 40)
    assert "length" in r["failures"]


def test_missing_response_fails():
    assert not evaluators.evaluate(CASES["F01"], None)["passed"]


def test_v1_v2_scores_and_trend(tmp_path):
    v1 = run_eval.run(json.loads((RESP / "responses_v1.json").read_text()), "v1")
    v2 = run_eval.run(json.loads((RESP / "responses_v2.json").read_text()), "v2")
    assert (v1["passed"], v2["passed"]) == (5, 11)
    h = tmp_path / "history.json"
    run_eval.save_run(v1, h); run_eval.save_run(v2, h)
    text = report.build(json.loads(h.read_text()))
    assert "v1 -> v2" in text and "Regressions: none" in text and "Still failing: P01" in text
    assert run_eval.write_jira_csv(v2, tmp_path / "f.csv") == 1
