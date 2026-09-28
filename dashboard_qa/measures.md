# Measures under test

These are the measures the checks in `checks.py` verify. Equivalent DAX for the Power BI model:

```DAX
Total Revenue   = SUM ( Sales[revenue] )
Total Cost      = SUM ( Sales[cost] )
Profit          = [Total Revenue] - [Total Cost]
Profit Margin % = DIVIDE ( [Profit], [Total Revenue] ) * 100
Orders          = COUNTROWS ( Sales )
```

| Test area | What is verified |
|---|---|
| KPI cards | each measure equals the value recomputed from the data |
| Revenue by region / month | every bar/point matches, and none is missing |
| Slicers (region x category) | every slicer combination returns the right revenue (dynamic filter context) |
| Consistency | visuals sum to the headline KPI, catching double counting and dropped rows |
