import pandas as pd

from dashboard_qa import checks, make_data


def build(tmp_path, inject=False):
    sales = make_data.make_sales()
    make_data.export_visuals(sales, tmp_path, inject_error=inject)
    return sales, checks.run_checks(sales, tmp_path)


def test_clean_exports_pass_all_checks(tmp_path):
    _, res = build(tmp_path)
    assert len(res) == 5 + 4 + 12 + 12 + 3
    assert all(r["passed"] for r in res), [r for r in res if not r["passed"]]


def test_wrong_measure_is_detected(tmp_path):
    _, res = build(tmp_path, inject=True)
    failed = {(r["check_id"], r["item"]) for r in res if not r["passed"]}
    assert ("REGION", "East") in failed
    assert ("SLICER", "East / Furniture") in failed
    assert ("SUM-REGION", "Region visual sums to Total Revenue KPI") in failed   # consistency check catches it too
    assert not any(item in ("North", "South", "West") for _, item in failed)     # no false positives


def test_missing_visual_row_is_reported(tmp_path):
    sales, _ = build(tmp_path)
    f = tmp_path / "revenue_by_region.csv"
    df = pd.read_csv(f)
    df[df["region"] != "West"].to_csv(f, index=False)
    res = checks.run_checks(sales, tmp_path)
    west = next(r for r in res if r["check_id"] == "REGION" and r["item"] == "West")
    assert not west["passed"] and west["actual"] is None


def test_profit_margin_formula(tmp_path):
    sales, res = build(tmp_path)
    kpi = next(r for r in res if r["item"] == "Profit Margin %")
    expected = (sales["revenue"].sum() - sales["cost"].sum()) / sales["revenue"].sum() * 100
    assert abs(kpi["expected"] - expected) < 0.01
