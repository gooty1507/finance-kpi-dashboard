"""
build_dashboard.py -- Builds a self-contained interactive executive KPI
dashboard as a single HTML file (Plotly.js via CDN).

Mirrors the resume's "Analytics & Visualization... Power BI, Tableau" and
"Reporting: P&L Analysis, Cash Flow Statements, KPI Dashboards, Executive
Presentations, Balance Sheets" bullets -- built as a code-first, open
alternative to a Power BI/Tableau workbook: no BI license required, fully
versionable in git, and viewable in any browser.

Chart choices follow a standard data-viz discipline: one axis per chart (no
dual-axis charts), a fixed categorical color order, sequential color only for
true magnitude encoding, hover tooltips on every series, and legends only
where there's more than one series to distinguish.

Usage
-----
    python build_dashboard.py
    python build_dashboard.py --data-dir ./data --output dashboard.html
"""

import argparse
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.offline import plot as plotly_plot

HERE = Path(__file__).parent

# --- Validated categorical palette (see dataviz skill / references/palette.md) ---
SLOT_1_BLUE = "#2a78d6"
SLOT_2_ORANGE = "#eb6834"
SLOT_3_AQUA = "#1baf7a"
SLOT_4_YELLOW = "#eda100"
SLOT_6_GREEN = "#008300"
SLOT_8_RED = "#e34948"

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="system-ui, -apple-system, 'Segoe UI', sans-serif", color="#0b0b0b", size=13),
    margin=dict(l=56, r=24, t=16, b=44),
    hoverlabel=dict(bgcolor="#0b0b0b", font_color="#ffffff", font_size=12),
    xaxis=dict(showgrid=False, linecolor="#c3c2b7", tickfont=dict(color="#898781"), nticks=8),
    yaxis=dict(gridcolor="#e1e0d9", zeroline=False, tickfont=dict(color="#898781")),
)
# Extra top margin for charts that also show a legend row above the plot.
CHART_LAYOUT_WITH_LEGEND = {**CHART_LAYOUT, "margin": dict(l=56, r=24, t=40, b=44)}


def chart_div(fig: go.Figure, title: str, include_js: bool = False) -> str:
    plot_html = plotly_plot(fig, output_type="div", include_plotlyjs=include_js,
                             config={"displaylogo": False, "responsive": True})
    return f'<h3 class="chart-title">{title}</h3>{plot_html}'


def build_revenue_chart(pnl: pd.DataFrame) -> str:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=pnl.month, y=pnl.revenue, mode="lines", name="Revenue",
        line=dict(color=SLOT_1_BLUE, width=2.5, shape="spline", smoothing=0.3),
        fill="tozeroy", fillcolor="rgba(42,120,214,0.08)",
        hovertemplate="%{x}<br>Revenue: $%{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(**CHART_LAYOUT, showlegend=False,
                       height=300, yaxis_tickprefix="$", yaxis_tickformat=",.2s")
    return chart_div(fig, "Monthly Revenue")


def build_margin_chart(pnl: pd.DataFrame) -> str:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=pnl.month, y=pnl.net_margin_pct * 100, mode="lines+markers", name="Net margin",
        line=dict(color=SLOT_3_AQUA, width=2.5),
        marker=dict(size=6),
        hovertemplate="%{x}<br>Net margin: %{y:.1f}%<extra></extra>",
    ))
    fig.update_layout(**CHART_LAYOUT, showlegend=False,
                       height=300, yaxis_ticksuffix="%")
    return chart_div(fig, "Net Margin %")


def build_pnl_breakdown_chart(pnl: pd.DataFrame) -> str:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=pnl.month, y=pnl.cogs, name="COGS", marker_color=SLOT_2_ORANGE,
                          hovertemplate="%{x}<br>COGS: $%{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Bar(x=pnl.month, y=pnl.opex, name="Opex", marker_color=SLOT_4_YELLOW,
                          hovertemplate="%{x}<br>Opex: $%{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Bar(x=pnl.month, y=pnl.net_income, name="Net income", marker_color=SLOT_6_GREEN,
                          hovertemplate="%{x}<br>Net income: $%{y:,.0f}<extra></extra>"))
    fig.update_layout(**CHART_LAYOUT_WITH_LEGEND,
                       barmode="stack", height=360, yaxis_tickprefix="$", yaxis_tickformat=",.2s",
                       legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0))
    return chart_div(fig, "P&L Breakdown (Revenue = COGS + Opex + Net Income)")


def build_cash_flow_chart(cash_flow: pd.DataFrame) -> str:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=cash_flow.month, y=cash_flow.operating_cf, name="Operating",
                          marker_color=SLOT_1_BLUE,
                          hovertemplate="%{x}<br>Operating CF: $%{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Bar(x=cash_flow.month, y=cash_flow.investing_cf, name="Investing",
                          marker_color=SLOT_2_ORANGE,
                          hovertemplate="%{x}<br>Investing CF: $%{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Bar(x=cash_flow.month, y=cash_flow.financing_cf, name="Financing",
                          marker_color=SLOT_8_RED,
                          hovertemplate="%{x}<br>Financing CF: $%{y:,.0f}<extra></extra>"))
    fig.update_layout(**CHART_LAYOUT_WITH_LEGEND, barmode="relative",
                       height=360, yaxis_tickprefix="$", yaxis_tickformat=",.2s",
                       legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0))
    fig.add_hline(y=0, line_color="#c3c2b7", line_width=1)
    return chart_div(fig, "Cash Flow by Activity")


def build_customer_chart(cust: pd.DataFrame) -> str:
    cust = cust.sort_values("revenue", ascending=True)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=cust.revenue, y=cust.customer, orientation="h", name="Revenue",
        marker=dict(
            color=cust.gross_margin_pct, colorscale=[[0, "#cde2fb"], [1, "#184f95"]],
            colorbar=dict(title="Gross<br>margin", tickformat=".0%", thickness=14),
        ),
        customdata=cust.gross_margin_pct,
        hovertemplate="%{y}<br>Revenue: $%{x:,.0f}<br>Gross margin: %{customdata:.1%}<extra></extra>",
    ))
    fig.update_layout(**CHART_LAYOUT, showlegend=False,
                       height=380, xaxis_tickprefix="$", xaxis_tickformat=",.2s")
    return chart_div(fig, "Top Customers -- Revenue (bar) & Gross Margin (color)")


def build_balance_sheet_chart(bs: pd.DataFrame) -> str:
    color_map = {"Assets": SLOT_1_BLUE, "Liabilities": SLOT_2_ORANGE, "Equity": SLOT_3_AQUA}
    bs = bs.iloc[::-1]
    fig = go.Figure()
    for category, color in color_map.items():
        sub = bs[bs.category == category]
        fig.add_trace(go.Bar(
            x=sub.amount, y=sub.line_item, orientation="h", name=category,
            marker_color=color,
            hovertemplate="%{y}<br>$%{x:,.0f}<extra></extra>",
        ))
    fig.update_layout(**CHART_LAYOUT_WITH_LEGEND, height=340,
                       xaxis_tickprefix="$", xaxis_tickformat=",.2s",
                       legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0))
    return chart_div(fig, "Balance Sheet Snapshot")


def kpi_tile(label: str, value: str, sub: str, accent: str) -> str:
    return f"""
    <div class="kpi-tile" style="--accent:{accent}">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}</div>
      <div class="kpi-sub">{sub}</div>
    </div>"""


PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Executive KPI Dashboard</title>
{plotly_js}
<style>
  :root {{
    color-scheme: light;
    --surface-1: #fcfcfb;
    --page-plane: #f9f9f7;
    --text-primary: #0b0b0b;
    --text-secondary: #52514e;
    --text-muted: #898781;
    --border: rgba(11,11,11,0.10);
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      color-scheme: dark;
      --surface-1: #1a1a19;
      --page-plane: #0d0d0d;
      --text-primary: #ffffff;
      --text-secondary: #c3c2b7;
      --text-muted: #898781;
      --border: rgba(255,255,255,0.10);
    }}
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--page-plane);
    color: var(--text-primary);
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  }}
  header {{
    padding: 28px 32px 8px;
  }}
  header h1 {{
    margin: 0 0 4px;
    font-size: 22px;
    font-weight: 700;
  }}
  header p {{
    margin: 0;
    color: var(--text-secondary);
    font-size: 14px;
    max-width: 720px;
  }}
  main {{
    padding: 20px 32px 40px;
    max-width: 1280px;
    margin: 0 auto;
  }}
  .kpi-row {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 14px;
    margin-bottom: 22px;
  }}
  .kpi-tile {{
    background: var(--surface-1);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 18px;
    border-top: 3px solid var(--accent);
  }}
  .kpi-label {{
    font-size: 12px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 6px;
  }}
  .kpi-value {{
    font-size: 26px;
    font-weight: 700;
    font-variant-numeric: proportional-nums;
  }}
  .kpi-sub {{
    font-size: 12.5px;
    color: var(--text-secondary);
    margin-top: 4px;
  }}
  .chart-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(440px, 1fr));
    gap: 16px;
  }}
  .chart-card {{
    background: var(--surface-1);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 8px 12px 4px;
  }}
  .chart-card.full {{
    grid-column: 1 / -1;
  }}
  .chart-title {{
    margin: 10px 4px 0;
    font-size: 15px;
    font-weight: 600;
  }}
  footer {{
    padding: 12px 32px 32px;
    color: var(--text-muted);
    font-size: 12px;
    max-width: 1280px;
    margin: 0 auto;
  }}
</style>
</head>
<body>
<header>
  <h1>Executive KPI Dashboard</h1>
  <p>Trailing-twelve-month performance across revenue, margin, cash flow, and customer profitability.
     Built with Python + Plotly on fully synthetic data -- a code-first, open alternative to a
     Power BI / Tableau workbook.</p>
</header>
<main>
  <div class="kpi-row">
    {kpi_tiles}
  </div>
  <div class="chart-grid">
    <div class="chart-card">{revenue_chart}</div>
    <div class="chart-card">{margin_chart}</div>
    <div class="chart-card full">{pnl_chart}</div>
    <div class="chart-card full">{cash_flow_chart}</div>
    <div class="chart-card">{customer_chart}</div>
    <div class="chart-card">{balance_sheet_chart}</div>
  </div>
</main>
<footer>
  Data is fully synthetic (see data/generate_data.py). Generated by build_dashboard.py.
</footer>
<script>
  // Plotly's responsive:true only recomputes on a window resize event, and the
  // CSS grid can settle each chart's final width a tick after Plotly's first
  // render -- force one resize pass after everything has laid out so no chart
  // is left rendered at a stale (pre-grid) width.
  window.addEventListener('load', function () {{
    requestAnimationFrame(function () {{
      document.querySelectorAll('.plotly-graph-div').forEach(function (gd) {{
        Plotly.Plots.resize(gd);
      }});
    }});
  }});
</script>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="Build the executive KPI dashboard HTML file.")
    parser.add_argument("--data-dir", default=str(HERE / "data"))
    parser.add_argument("--output", default=str(HERE / "dashboard.html"))
    args = parser.parse_args()

    data_dir = Path(args.data_dir)

    pnl = pd.read_csv(data_dir / "monthly_pnl.csv")
    cash_flow = pd.read_csv(data_dir / "cash_flow.csv")
    customers = pd.read_csv(data_dir / "customer_profitability.csv")
    balance_sheet = pd.read_csv(data_dir / "balance_sheet.csv")

    # --- KPI calculations (trailing twelve months vs. prior twelve) ---
    last12 = pnl.iloc[-12:]
    prior12 = pnl.iloc[-24:-12]
    ttm_revenue = last12.revenue.sum()
    prior_ttm_revenue = prior12.revenue.sum()
    yoy_growth = (ttm_revenue - prior_ttm_revenue) / prior_ttm_revenue
    ttm_net_income = last12.net_income.sum()
    ttm_net_margin = ttm_net_income / ttm_revenue
    ttm_operating_cf = cash_flow.iloc[-12:].operating_cf.sum()

    kpi_tiles = "".join([
        kpi_tile("TTM Revenue", f"${ttm_revenue / 1e6:,.1f}M", "trailing 12 months", SLOT_1_BLUE),
        kpi_tile("YoY Revenue Growth", f"{yoy_growth:+.1%}", "vs. prior 12 months", SLOT_3_AQUA),
        kpi_tile("TTM Net Margin", f"{ttm_net_margin:.1%}", f"${ttm_net_income / 1e6:,.1f}M net income", SLOT_6_GREEN),
        kpi_tile("TTM Operating Cash Flow", f"${ttm_operating_cf / 1e6:,.1f}M", "trailing 12 months", SLOT_2_ORANGE),
    ])

    # Embed plotly.js inline so the dashboard is a single, fully self-contained
    # file with no external CDN dependency (works offline, no CDN outage risk).
    from plotly.offline.offline import get_plotlyjs
    plotly_js = f"<script>{get_plotlyjs()}</script>"

    html = PAGE_TEMPLATE.format(
        kpi_tiles=kpi_tiles,
        revenue_chart=build_revenue_chart(pnl),
        margin_chart=build_margin_chart(pnl),
        pnl_chart=build_pnl_breakdown_chart(pnl),
        cash_flow_chart=build_cash_flow_chart(cash_flow),
        customer_chart=build_customer_chart(customers),
        balance_sheet_chart=build_balance_sheet_chart(balance_sheet),
        plotly_js=plotly_js,
    )

    out_path = Path(args.output)
    out_path.write_text(html)

    print("Dashboard built:", out_path)
    print(f"  TTM Revenue            : ${ttm_revenue:,.0f}")
    print(f"  YoY Revenue Growth     : {yoy_growth:+.1%}")
    print(f"  TTM Net Margin         : {ttm_net_margin:.1%}")
    print(f"  TTM Operating Cash Flow: ${ttm_operating_cf:,.0f}")


if __name__ == "__main__":
    main()
