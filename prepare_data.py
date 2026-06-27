"""Generate a realistic retail sales dataset as a Power BI-ready star schema.

Deterministic (seeded) so anyone can reproduce the exact dashboard. Writes five
CSVs to ./data: fact_sales + dim_product, dim_customer, dim_country, dim_date.

The data is synthetic but modelled on real online-retail behaviour (UK-dominant,
multi-country, seasonal Q4 lift, repeat customers, ~2% returns) so the dashboard
looks and behaves like a real sales BI report.

    pip install pandas numpy
    python prepare_data.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 7
OUT = Path(__file__).parent / "data"
START, END = "2024-01-01", "2025-12-31"

COUNTRIES = {
    "United Kingdom": ("Europe", 0.55),
    "Germany": ("Europe", 0.08),
    "France": ("Europe", 0.07),
    "EIRE": ("Europe", 0.05),
    "Spain": ("Europe", 0.04),
    "Netherlands": ("Europe", 0.04),
    "Belgium": ("Europe", 0.03),
    "Australia": ("Oceania", 0.03),
    "United States": ("Americas", 0.03),
    "Bangladesh": ("Asia", 0.03),
    "India": ("Asia", 0.02),
    "UAE": ("Asia", 0.02),
    "Other": ("Other", 0.01),
}

CATEGORIES = {
    "Home Decor": (8, 45),
    "Kitchen": (5, 60),
    "Gifts": (3, 30),
    "Stationery": (1, 15),
    "Garden": (10, 80),
    "Toys": (4, 40),
    "Lighting": (12, 90),
}


def _products(rng) -> pd.DataFrame:
    rows = []
    pid = 10000
    for cat, (lo, hi) in CATEGORIES.items():
        for n in range(rng.integers(10, 16)):
            pid += 1
            price = round(float(rng.uniform(lo, hi)), 2)
            rows.append({"ProductID": pid, "Product": f"{cat} Item {n + 1}", "Category": cat, "UnitPrice": price})
    return pd.DataFrame(rows)


def _customers(rng, n=2000) -> pd.DataFrame:
    names = list(COUNTRIES)
    weights = np.array([COUNTRIES[c][1] for c in names])
    weights = weights / weights.sum()
    cc = rng.choice(names, size=n, p=weights)
    return pd.DataFrame({"CustomerID": np.arange(20001, 20001 + n), "Country": cc})


def _dim_date() -> pd.DataFrame:
    d = pd.date_range(START, END, freq="D")
    return pd.DataFrame({
        "Date": d,
        "Year": d.year,
        "Quarter": "Q" + d.quarter.astype(str),
        "MonthNo": d.month,
        "Month": d.strftime("%b %Y"),
        "MonthName": d.strftime("%B"),
        "Day": d.day,
        "Weekday": d.strftime("%a"),
        "IsWeekend": d.weekday >= 5,
    })


def main() -> None:
    rng = np.random.default_rng(SEED)
    OUT.mkdir(parents=True, exist_ok=True)

    products = _products(rng)
    customers = _customers(rng)
    dim_country = pd.DataFrame(
        [{"Country": c, "Region": COUNTRIES[c][0]} for c in COUNTRIES]
    )
    dim_date = _dim_date()

    days = pd.to_datetime(dim_date["Date"]).to_numpy()
    # seasonal weight: Q4 (Oct-Dec) lift for gifting
    months = pd.to_datetime(days).month
    day_weight = np.where(np.isin(months, [11, 12]), 2.4, np.where(months == 10, 1.5, 1.0))
    day_weight = day_weight / day_weight.sum()

    n_lines = 60000
    cust_idx = rng.integers(0, len(customers), n_lines)
    prod_idx = rng.integers(0, len(products), n_lines)
    line_days = rng.choice(len(days), size=n_lines, p=day_weight)

    qty = rng.integers(1, 13, n_lines)
    is_return = rng.random(n_lines) < 0.02
    qty = np.where(is_return, -rng.integers(1, 4, n_lines), qty)

    cust = customers.iloc[cust_idx].reset_index(drop=True)
    prod = products.iloc[prod_idx].reset_index(drop=True)
    dates = pd.to_datetime(days[line_days])

    # invoice no: group ~3 lines per invoice by (customer, day)
    base_invoice = 500000 + (cust_idx * 7 + line_days) % 90000
    fact = pd.DataFrame({
        "InvoiceNo": ["C" + str(x) if r else str(x) for x, r in zip(base_invoice, is_return)],
        "InvoiceDate": dates.normalize(),
        "CustomerID": cust["CustomerID"].to_numpy(),
        "ProductID": prod["ProductID"].to_numpy(),
        "Quantity": qty,
        "UnitPrice": prod["UnitPrice"].to_numpy(),
    })
    fact["Revenue"] = (fact["Quantity"] * fact["UnitPrice"]).round(2)
    fact["IsReturn"] = is_return

    products.to_csv(OUT / "dim_product.csv", index=False)
    customers.to_csv(OUT / "dim_customer.csv", index=False)
    dim_country.to_csv(OUT / "dim_country.csv", index=False)
    dim_date.to_csv(OUT / "dim_date.csv", index=False)
    fact.to_csv(OUT / "fact_sales.csv", index=False)

    rev = fact.loc[~fact["IsReturn"], "Revenue"].sum()
    print(f"Wrote {len(fact):,} sales rows to {OUT}/")
    print(f"  products={len(products)} customers={len(customers)} countries={len(dim_country)} "
          f"days={len(dim_date)}")
    print(f"  gross revenue (excl. returns): {rev:,.0f}")


if __name__ == "__main__":
    main()
