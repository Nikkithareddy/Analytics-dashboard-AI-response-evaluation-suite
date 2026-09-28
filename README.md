# Analytics Dashboard & AI Response Evaluation Suite

Two QA tools built with **Python, MS Excel/CSV, Jira-ready exports and Git**:

1. **Dashboard QA**: checks that a BI dashboard (Power BI) shows the right numbers.
2. **AI response evaluation**: scores AI answers for relevance, accuracy and guardrail adherence, and tracks results over time.

## 1. Dashboard QA (`dashboard_qa/`)
Recomputes every figure from the underlying data and compares it with what the dashboard visuals show.

| Area | What is verified |
|---|---|
| KPI cards | Total Revenue, Total Cost, Profit, Profit Margin %, Orders |
| Charts | revenue by region and by month: every value present and correct |
| Slicers | every region x category combination returns the right revenue (dynamic filter context) |
| Consistency | visuals sum to the headline KPI (catches double counting and dropped rows) |

The measures under test are documented, with DAX, in `dashboard_qa/measures.md`.

**About the data:** there is no `.pbix` file here. `data/sales.csv` is generated sample data, and `data/dashboard_exports/*.csv`
simulate Power BI's "Export data" output for each visual. To test a real report, export the same visuals to CSV
(`kpis.csv: measure,value`, `revenue_by_region.csv: region,revenue`, `revenue_by_month.csv: month,revenue`,
`slicer_region_category.csv: region,category,revenue`) and point `checks.run_checks()` at them with your source data.
`python dashboard_qa/make_data.py --inject-error` builds exports with a wrong East figure to show detection.

## 2. AI response evaluation (`ai_eval/`)
- `prompts/test_prompts.yaml`: 12 structured test prompts across factual accuracy, summarization, relevance,
  guardrails (harmful request, malware, prompt injection), privacy (PII echo) and boundaries (medical). Each has expected
  terms, forbidden terms, refuse/don't-refuse expectation and a length limit.
- `evaluators.py`: rule-based scoring. A prompt passes only if every dimension passes, including **over-refusal** checks.
- `prompts/judge_prompt_template.md`: rubric prompt for an LLM-as-judge when rules aren't enough (tone, nuance).
- `run_eval.py`: scores a responses file, appends to `reports/run_history.json`, and writes a **Jira-importable CSV** of failures.
- `report.py`: `reports/trend_report.md` showing pass rate per run and category, plus fixed/regressed/still-failing prompts.

```bash
pip install -r requirements.txt
python -m ai_eval.run_eval --responses ai_eval/responses/responses_v1.json --label v1
python -m ai_eval.run_eval --responses ai_eval/responses/responses_v2.json --label v2
python -m ai_eval.report
pytest
```
`responses_v1.json` / `responses_v2.json` are **hand-written sample responses** (v1 with deliberate faults, v2 improved with one
remaining privacy failure), not output from a live model. To evaluate a real model, save its answers as `{prompt_id: text}` JSON
and pass that file with a new `--label`.

## Structure
```
dashboard_qa/   make_data.py, checks.py, measures.md
ai_eval/        prompts/, responses/, evaluators.py, run_eval.py, report.py
data/           sample sales data + simulated dashboard exports
reports/        run history, trend report, failure CSVs for Jira import
tests/          pytest suites for both tools
```
