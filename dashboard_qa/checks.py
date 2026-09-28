"""Compares dashboard visual exports against values recomputed from the underlying data."""
from pathlib import Path

import pandas as pd

TOL = 0.01  # absolute tolerance (exports are rounded to 2 dp)


def _row(check_id, area, item, expected, actual):
    ok = actual is not None and abs(float(expected) - float(actual)) <= TOL
    return {"check_id": check_id, "area": area, "item": item, "expected": round(float(expected), 2),
            "actual": None if actual is None else round(float(actual), 2), "passed": ok}


def _lookup(frame, key_cols, key, value_col):
    m = frame
    for col, val in zip(key_cols, key if isinstance(key, tuple) else (key,)):
        m = m[m[col] == val]
    return float(m[value_col].iloc[0]) if len(m) else None   # None = missing from the visual


def run_checks(sales: pd.DataFrame, export_dir: Path) -> list[dict]:
    export_dir = Path(export_dir)
    rev, cost = sales["revenue"].sum(), sales["cost"].sum()
    res = []

    kpis = pd.read_csv(export_dir / "kpis.csv")
    expected = {"Total Revenue": rev, "Total Cost": cost, "Profit": rev - cost,
                "Profit Margin %": (rev - cost) / rev * 100, "Orders": len(sales)}
    for m, exp in expected.items():
        res.append(_row("KPI", "KPI cards", m, exp, _lookup(kpis, ["measure"], m, "value")))

    by_region = pd.read_csv(export_dir / "revenue_by_region.csv")
    for region, exp in sales.groupby("region")["revenue"].sum().items():
        res.append(_row("REGION", "Revenue by region", region, exp, _lookup(by_region, ["region"], region, "revenue")))

    by_month = pd.read_csv(export_dir / "revenue_by_month.csv")
    monthly = sales.assign(month=sales["order_date"].str[:7]).groupby("month")["revenue"].sum()
    for month, exp in monthly.items():
        res.append(_row("MONTH", "Revenue by month", month, exp, _lookup(by_month, ["month"], month, "revenue")))

    slicer = pd.read_csv(export_dir / "slicer_region_category.csv")
    for (region, cat), exp in sales.groupby(["region", "category"])["revenue"].sum().items():
        res.append(_row("SLICER", "Slicer: region x category", f"{region} / {cat}", exp,
                        _lookup(slicer, ["region", "category"], (region, cat), "revenue")))

    # Internal consistency: visuals must add up to the headline KPI
    kpi_rev = _lookup(kpis, ["measure"], "Total Revenue", "value")
    res.append(_row("SUM-REGION", "Consistency", "Region visual sums to Total Revenue KPI", kpi_rev, by_region["revenue"].sum()))
    res.append(_row("SUM-MONTH", "Consistency", "Month visual sums to Total Revenue KPI", kpi_rev, by_month["revenue"].sum()))
    res.append(_row("SUM-SLICER", "Consistency", "Slicer combos sum to Total Revenue KPI", kpi_rev, slicer["revenue"].sum()))
    return res
