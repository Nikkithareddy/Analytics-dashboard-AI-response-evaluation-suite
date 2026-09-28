"""Creates the sales dataset and simulated Power BI visual exports.

The exports stand in for what you get from Power BI's "Export data" on each visual. To test a real dashboard,
export the same visuals to CSV and drop them in data/dashboard_exports/ (see README for the expected columns).
"""
import random
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
REGIONS = ["North", "South", "East", "West"]
CATEGORIES = {"Electronics": 300.0, "Furniture": 180.0, "Clothing": 45.0}


def make_sales(seed: int = 42, rows: int = 600) -> pd.DataFrame:
    rng = random.Random(seed)
    start, out = date(2025, 1, 1), []
    for i in range(rows):
        cat = rng.choice(list(CATEGORIES))
        units = rng.randint(1, 20)
        revenue = round(units * CATEGORIES[cat] * rng.uniform(0.9, 1.1), 2)
        out.append({
            "order_id": 5000 + i,
            "order_date": (start + timedelta(days=rng.randint(0, 364))).isoformat(),
            "region": rng.choice(REGIONS), "category": cat, "units": units,
            "revenue": revenue, "cost": round(revenue * rng.uniform(0.55, 0.8), 2),
        })
    return pd.DataFrame(out)


def export_visuals(df: pd.DataFrame, out_dir: Path, inject_error: bool = False) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    rev, cost = df["revenue"].sum(), df["cost"].sum()
    kpis = pd.DataFrame({"measure": ["Total Revenue", "Total Cost", "Profit", "Profit Margin %", "Orders"],
                         "value": [rev, cost, rev - cost, (rev - cost) / rev * 100, len(df)]})
    by_region = df.groupby("region", as_index=False)["revenue"].sum()
    by_month = (df.assign(month=df["order_date"].str[:7]).groupby("month", as_index=False)["revenue"].sum())
    slicer = df.groupby(["region", "category"], as_index=False)["revenue"].sum()
    if inject_error:  # simulate a wrong DAX filter context on one visual
        by_region.loc[by_region["region"] == "East", "revenue"] += 1500
        slicer.loc[(slicer["region"] == "East") & (slicer["category"] == "Furniture"), "revenue"] += 1500
    for name, frame in {"kpis": kpis, "revenue_by_region": by_region,
                        "revenue_by_month": by_month, "slicer_region_category": slicer}.items():
        frame.round(2).to_csv(out_dir / f"{name}.csv", index=False)


if __name__ == "__main__":
    sales = make_sales()
    DATA.mkdir(exist_ok=True)
    sales.to_csv(DATA / "sales.csv", index=False)
    export_visuals(sales, DATA / "dashboard_exports", inject_error="--inject-error" in sys.argv)
    print(f"wrote {len(sales)} sales rows and visual exports to {DATA}")
