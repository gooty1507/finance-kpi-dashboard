"""
generate_data.py

Generates fully SYNTHETIC data for the executive KPI dashboard: 24 months of
P&L, monthly cash flow by activity, top-customer profitability, and a
point-in-time balance sheet snapshot. Nothing here is real company data --
it's randomly generated with a fixed seed so results are reproducible.

Run this once before building the dashboard:

    python data/generate_data.py

Outputs:
    monthly_pnl.csv           -- 24 months of revenue / COGS / opex / net income
    cash_flow.csv              -- 24 months of operating / investing / financing CF
    customer_profitability.csv -- top 10 customers by revenue and margin
    balance_sheet.csv          -- a single point-in-time balance sheet snapshot
"""

import numpy as np
import pandas as pd
from pathlib import Path

SEED = 11
rng = np.random.default_rng(SEED)
OUT_DIR = Path(__file__).parent

# ---------------------------------------------------------------------------
# 24 months of P&L
# ---------------------------------------------------------------------------

n_months = 24
dates = pd.date_range(end=pd.Timestamp("2026-08-01"), periods=n_months, freq="MS")

month_idx = np.arange(n_months)
base_revenue = 2_400_000
trend = base_revenue * (1 + 0.018) ** month_idx
seasonality = 1 + 0.08 * np.sin(2 * np.pi * (month_idx % 12) / 12 - np.pi / 2)
noise = rng.normal(1.0, 0.03, size=n_months)
revenue = (trend * seasonality * noise).round(0)

cogs_pct = rng.uniform(0.44, 0.49, size=n_months)
opex_pct = rng.uniform(0.28, 0.33, size=n_months)
cogs = (revenue * cogs_pct).round(0)
opex = (revenue * opex_pct).round(0)
net_income = revenue - cogs - opex

pnl = pd.DataFrame({
    "month": dates.strftime("%Y-%m"),
    "revenue": revenue.astype(int),
    "cogs": cogs.astype(int),
    "opex": opex.astype(int),
    "net_income": net_income.astype(int),
})
pnl["net_margin_pct"] = (pnl.net_income / pnl.revenue).round(4)
pnl.to_csv(OUT_DIR / "monthly_pnl.csv", index=False)

# ---------------------------------------------------------------------------
# 24 months of cash flow by activity
# ---------------------------------------------------------------------------

operating_cf = (net_income * rng.uniform(1.05, 1.25, size=n_months)).round(0)
investing_cf = -(revenue * rng.uniform(0.03, 0.07, size=n_months)).round(0)
financing_cf = np.where(
    month_idx % 6 == 0,
    -(revenue * rng.uniform(0.08, 0.15, size=n_months)).round(0),
    -(revenue * rng.uniform(0.0, 0.01, size=n_months)).round(0),
)

cash_flow = pd.DataFrame({
    "month": dates.strftime("%Y-%m"),
    "operating_cf": operating_cf.astype(int),
    "investing_cf": investing_cf.astype(int),
    "financing_cf": financing_cf.astype(int),
})
cash_flow["net_change_in_cash"] = (
    cash_flow.operating_cf + cash_flow.investing_cf + cash_flow.financing_cf
)
cash_flow.to_csv(OUT_DIR / "cash_flow.csv", index=False)

# ---------------------------------------------------------------------------
# Top 10 customers by revenue and gross margin
# ---------------------------------------------------------------------------

customer_names = [
    "Harborview Capital", "Silverline Partners", "Union Peak Advisors",
    "Delta Bridge Holdings", "Northgate Financial", "Crestline Data Services",
    "BlueWave Software Inc.", "Meridian Office Supplies", "Apex Facilities Group",
    "Ashford Global Markets",
]

cust_revenue = np.sort(rng.uniform(180_000, 1_450_000, size=10))[::-1].round(0)
cust_margin_pct = rng.uniform(0.18, 0.52, size=10)

customer_profitability = pd.DataFrame({
    "customer": customer_names,
    "revenue": cust_revenue.astype(int),
    "gross_margin_pct": cust_margin_pct.round(4),
})
customer_profitability["margin_dollars"] = (
    customer_profitability.revenue * customer_profitability.gross_margin_pct
).round(0).astype(int)
customer_profitability = customer_profitability.sort_values("revenue", ascending=False)
customer_profitability.to_csv(OUT_DIR / "customer_profitability.csv", index=False)

# ---------------------------------------------------------------------------
# Point-in-time balance sheet snapshot
# ---------------------------------------------------------------------------

balance_sheet = pd.DataFrame([
    {"category": "Assets", "line_item": "Cash & Equivalents", "amount": 6_850_000},
    {"category": "Assets", "line_item": "Accounts Receivable", "amount": 4_120_000},
    {"category": "Assets", "line_item": "Fixed Assets (net)", "amount": 9_430_000},
    {"category": "Liabilities", "line_item": "Accounts Payable", "amount": 2_760_000},
    {"category": "Liabilities", "line_item": "Long-Term Debt", "amount": 5_500_000},
    {"category": "Equity", "line_item": "Retained Earnings & Capital", "amount": 12_140_000},
])
balance_sheet.to_csv(OUT_DIR / "balance_sheet.csv", index=False)

print("Synthetic data generated in:", OUT_DIR)
print(f"  monthly_pnl.csv             : {len(pnl)} rows")
print(f"  cash_flow.csv                : {len(cash_flow)} rows")
print(f"  customer_profitability.csv   : {len(customer_profitability)} rows")
print(f"  balance_sheet.csv            : {len(balance_sheet)} rows")
