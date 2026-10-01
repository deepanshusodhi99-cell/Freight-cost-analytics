# Building the Power BI model

Power BI Desktop runs on Windows only. The `.pbix` file has to be built by you; nothing in this
repo contains one. Do not put DAX or Power BI on your resume until the file exists and reconciles.

## 1. Load
Home > Get data > Text/CSV. Load `dim_carrier`, `dim_lane`, `dim_date`, `fact_shipments` from `/data`.
In Power Query set types: dates as Date, `on_time` and ids as Whole number, costs as Fixed decimal.

## 2. Model
- Relationships (many-to-one, single direction): fact carrier_id, lane_id, ship_date to the dimension keys.
- Right-click `dim_date` > Mark as date table, using the `date` column.
- Hide key columns on the fact table. Sort `month_name` by `month_num`.

## 3. Measures
Create a blank table called `_Measures`. Add every measure in `dax/measures.dax` one at a time
(Modeling > New measure). Set formats: currency, percentage, one decimal for hours.

## 4. Reconcile before you build visuals (this is the test that matters)
Put a card on a blank page for each and compare with the SQL output:

| Measure | Should equal |
|---|---|
| Shipments | 24,000 |
| Total Cost | $36,130,658 (rounded) |
| On-Time % | 87.3% |
| Cost per KM for each carrier (matrix by carrier) | `output/tables/01_carrier_scorecard.csv` |

If they differ, find out why before going further. Being able to explain a reconciliation
break in an interview is worth more than any chart.

## 5. Pages
1. **Executive summary**: cost, shipments, on-time %, cost per shipment, monthly trend with MoM %.
2. **Carrier scorecard**: cost per km vs on-time % (scatter), carrier table with rank measures and score.
3. **Lanes and distance**: on-time % by carrier and distance band (matrix with conditional formatting).
4. **Dwell and detention**: detention cost by dwell bucket, peak vs off-peak comparison.

State the score weights (60/40) on page 2 and say they are an assumption.

## 6. Ship it
Save the `.pbix` in `/powerbi`, export each page as a PNG to `/powerbi/screenshots`, and embed
them in the README. Recruiters will look at screenshots, not open the file.
