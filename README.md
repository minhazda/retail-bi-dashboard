# Retail Sales BI Dashboard (Power BI)

An end-to-end **Power BI** sales-analytics dashboard on retail transaction data: a
star-schema data model, DAX measures, and three reporting pages (Executive overview,
Product analysis, Customer / RFM). Built to demonstrate the BI skills Bangladeshi data
roles ask for most — **Power BI, DAX, data modelling, dashboards, and reporting**.

> **Author:** Md Minhazur Rahman · [github.com/minhazda](https://github.com/minhazda) ·
> [linkedin.com/in/mohammadminhaz](https://www.linkedin.com/in/mohammadminhaz/)

## Status

The data model, DAX measures, and step-by-step build guide below are complete —
the report itself is built interactively in Power BI Desktop, so the published
dashboard link and screenshot land here once that manual build step is done.

## What it demonstrates

| Skill | Where |
|-------|-------|
| Data modelling (star schema) | 1 fact + 4 dimension tables, relationships |
| DAX | 12 measures incl. time-intelligence (MoM, YoY, YTD) |
| ETL / data prep | `prepare_data.py` (Power Query steps documented) |
| Dashboarding & reporting | 3 interactive pages, KPIs, drill, slicers |
| Customer analytics | RFM segmentation |

## The data

Run the prep script (or use the CSVs already in `data/`):

```bash
pip install pandas numpy
python prepare_data.py        # writes data/*.csv
```

A realistic synthetic online-retail dataset (60,000 sales lines, 2 years, 13 countries,
~2,000 customers, seasonal Q4 lift, ~2% returns) in a clean **star schema**:

| Table | Grain | Key columns |
|-------|-------|-------------|
| `fact_sales` | one order line | InvoiceNo, InvoiceDate, CustomerID, ProductID, Quantity, UnitPrice, Revenue, IsReturn |
| `dim_product` | product | ProductID, Product, Category, UnitPrice |
| `dim_customer` | customer | CustomerID, Country |
| `dim_country` | country | Country, Region |
| `dim_date` | day | Date, Year, Quarter, MonthNo, Month, MonthName, Weekday, IsWeekend |

> To use **real** data instead, export the UCI Online Retail II dataset into the same
> column shape and drop the CSVs into `data/` — the model and DAX are unchanged.

---

## Build it in Power BI (step by step)

### 1. Install Power BI Desktop (free)
Microsoft Store → search **Power BI Desktop** → Install. (Windows only; free.)

### 2. Load the data
`Home → Get data → Text/CSV` → import each file in `data/`:
`fact_sales.csv`, `dim_product.csv`, `dim_customer.csv`, `dim_country.csv`, `dim_date.csv`.
For each, click **Transform Data** to open Power Query and confirm column types
(dates as Date, Revenue/UnitPrice as Decimal, Quantity as Whole number), then **Close & Apply**.
*(This Power Query step is your "ETL" — note it on your CV.)*

### 3. Model the relationships
Go to **Model view** and draw these (drag key → key, single direction, 1-to-many):
- `dim_product[ProductID]` → `fact_sales[ProductID]`
- `dim_customer[CustomerID]` → `fact_sales[CustomerID]`
- `dim_date[Date]` → `fact_sales[InvoiceDate]`
- `dim_country[Country]` → `dim_customer[Country]`

Select `dim_date` → **Table tools → Mark as date table** → Date column. (Required for time intelligence.)

### 4. Create the DAX measures
Right-click `fact_sales` → **New measure**, paste each (one measure per box):

```DAX
Net Revenue       = SUM ( fact_sales[Revenue] )
Gross Revenue     = CALCULATE ( [Net Revenue], fact_sales[IsReturn] = FALSE )
Returns Value     = CALCULATE ( [Net Revenue], fact_sales[IsReturn] = TRUE )
Total Orders      = DISTINCTCOUNT ( fact_sales[InvoiceNo] )
Units Sold        = SUM ( fact_sales[Quantity] )
Unique Customers  = DISTINCTCOUNT ( fact_sales[CustomerID] )
Avg Order Value   = DIVIDE ( [Net Revenue], [Total Orders] )
Return Rate %     = DIVIDE ( ABS ( [Returns Value] ), [Gross Revenue] )
```

```DAX
Revenue YTD = CALCULATE ( [Net Revenue], DATESYTD ( dim_date[Date] ) )

Revenue MoM % =
VAR Prev = CALCULATE ( [Net Revenue], DATEADD ( dim_date[Date], -1, MONTH ) )
RETURN DIVIDE ( [Net Revenue] - Prev, Prev )

Revenue YoY % =
VAR Prev = CALCULATE ( [Net Revenue], DATEADD ( dim_date[Date], -1, YEAR ) )
RETURN DIVIDE ( [Net Revenue] - Prev, Prev )
```

Format `Return Rate %`, `Revenue MoM %`, `Revenue YoY %` as **Percentage**; revenue measures as **Whole number / currency**.

### 5. RFM customer segmentation (one calculated table)
**Modeling → New table**:

```DAX
RFM =
VAR LastDate = MAX ( fact_sales[InvoiceDate] )
RETURN
ADDCOLUMNS (
    VALUES ( dim_customer[CustomerID] ),
    "Recency",   DATEDIFF ( CALCULATE ( MAX ( fact_sales[InvoiceDate] ) ), LastDate, DAY ),
    "Frequency", CALCULATE ( DISTINCTCOUNT ( fact_sales[InvoiceNo] ) ),
    "Monetary",  CALCULATE ( [Gross Revenue] )
)
```
Add a segment column (**New column** on the RFM table):
```DAX
Segment =
SWITCH ( TRUE (),
    [Frequency] >= 6 && [Monetary] >= 4000, "Champions",
    [Frequency] >= 3, "Loyal",
    [Recency] <= 30,  "Recent",
    "At risk" )
```

### 6. Build the three report pages

**Page 1 — Executive overview**
- 4 **Card** visuals: `Net Revenue`, `Total Orders`, `Avg Order Value`, `Unique Customers`.
- **Line chart**: Axis `dim_date[Month]`, Values `Net Revenue` (shows the Q4 lift).
- **Map** (filled map): Location `dim_country[Country]`, Size `Net Revenue`.
- **Bar chart**: Top 10 products — Axis `dim_product[Product]`, Values `Net Revenue`, Top-N filter = 10.
- **Slicers**: `dim_date[Year]`, `dim_country[Region]`.

**Page 2 — Product analysis**
- **Matrix**: Rows `Category` → `Product`, Columns `dim_date[Quarter]`, Values `Net Revenue`.
- **Bar**: `Return Rate %` by Category.
- **Decomposition tree** (optional): `Net Revenue` by Region → Country → Category.

**Page 3 — Customers (RFM)**
- **Clustered column**: `Segment` (from RFM) vs count of customers.
- **Scatter**: X `Recency`, Y `Frequency`, Size `Monetary`, Legend `Segment`.
- **Table**: top customers by `Monetary`.

### 7. Theme + publish
- `View → Themes → Browse for themes` → load `theme.json` (in this repo) for instant polish.
- **Publish**: `Home → Publish` → sign in with a free Power BI account → choose *My workspace*.
- In the Power BI Service, open the report → `File → Embed report → Publish to web (public)` → copy the link → paste it in the **Live dashboard** section above and on your LinkedIn.

---

## Files

```
prepare_data.py     generates the star-schema CSVs (deterministic)
data/               fact_sales.csv + dim_*.csv (ready to import)
theme.json          Power BI theme for consistent styling
docs/dashboard.png  (add your screenshot here)
RetailBI.pbix       (add your built report here)
```

MIT © Md Minhazur Rahman
