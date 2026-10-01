# Making this less synthetic

The strongest upgrade is replacing the synthetic diesel series with a real one.

## Real diesel prices (verified source, check the page for the current download option)
Natural Resources Canada publishes weekly retail diesel prices, a Canada average plus
individual cities, on its "Transportation fuel prices > Diesel" pages. Download the weekly
Canada series and save it as `data/diesel_weekly.csv` with exactly these columns:

```
week_start,diesel_cpl
2025-09-30,158.4
...
```

Then run `python src/generate_shipments.py` again. The generator uses the file when it
exists. Cover the full period 2025-09-25 to 2026-09-26, or edit START/END in the script.

If you do this, say so in the README ("diesel prices: real, NRCan weekly Canada average;
shipments: synthetic") and re-run the analysis, because finding #4 will change.

## Real freight data for a second project
Public freight datasets exist (for example Statistics Canada trucking surveys and the US
Bureau of Transportation Statistics Freight Analysis Framework), but I have not checked which
tables are currently available or what their licences allow. Verify that before building on one.
Public freight data is usually aggregated by commodity and region, so it supports lane-level
cost and volume analysis, not carrier performance. Carrier on-time data is rarely public.
