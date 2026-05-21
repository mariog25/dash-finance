import pandas as pd
import dash
from dash import html, dcc, Input, Output, dash_table
import plotly.graph_objects as go

from components.merchant_card import build_merchant_summary_card
from services.finance_queries import (
    get_available_months,
    get_merchant_monthly_total,
    get_merchant_transactions,
)
from utils.formatters import format_eur_es, format_pct_es, deviation_class

dash.register_page(__name__, path="/merchant-revision", name="Merchant Revision")

months_df = get_available_months()
months_df["month_str"] = months_df["month"].astype(str)
months_df["year"] = months_df["month_str"].str[:4]
months_df["month_num"] = months_df["month_str"].str[5:7]

year_options = [
    {"label": y, "value": y}
    for y in sorted(months_df["year"].dropna().unique(), reverse=True)
]

month_names = {
    "01": "January",
    "02": "February",
    "03": "March",
    "04": "April",
    "05": "May",
    "06": "June",
    "07": "July",
    "08": "August",
    "09": "September",
    "10": "October",
    "11": "November",
    "12": "December",
}

month_options = [
    {"label": month_names[f"{m:02d}"], "value": f"{m:02d}"}
    for m in range(1, 13)
]

default_year = year_options[0]["value"] if year_options else None
default_month = months_df["month_num"].iloc[0] if not months_df.empty else None


def empty_trend_figure(message: str = "No trend data"):
    return {
        "data": [],
        "layout": {
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "margin": {"l": 0, "r": 0, "t": 0, "b": 0},
            "xaxis": {"visible": False},
            "yaxis": {"visible": False},
            "annotations": [
                {
                    "text": message,
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 0.5,
                    "showarrow": False,
                    "font": {"size": 12, "color": "#7b8a9a"},
                }
            ],
            "showlegend": False,
        },
    }


def build_merchant_trend_figure(series_months: list, series_values: list, hidden: bool = False):
    """Build a trend chart for merchant data."""
    if not series_months or not series_values:
        return empty_trend_figure()

    return {
        "data": [
            {
                "x": series_months,
                "y": series_values,
                "customdata": [format_eur_es(v, masked=hidden) for v in series_values],
                "type": "scatter",
                "mode": "lines+markers",
                "fill": "tozeroy",
                "line": {
                    "color": "#1973B8",
                    "width": 1.4,
                    "shape": "spline",
                    "smoothing": 0.8,
                },
                "marker": {
                    "size": 3,
                    "color": "#1973B8",
                },
                "fillcolor": "rgba(25, 115, 184, 0.03)",
                "hovertemplate": (
                    "<b>%{x}</b><br>"
                    "Amount: %{customdata}<extra></extra>"
                ),
            }
        ],
        "layout": {
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "margin": {"l": 0, "r": 0, "t": 8, "b": 0},
            "xaxis": {
                "showgrid": False,
                "showticklabels": False,
                "zeroline": False,
                "fixedrange": True,
            },
            "yaxis": {
                "showgrid": False,
                "showticklabels": False,
                "zeroline": False,
                "fixedrange": True,
            },
            "showlegend": False,
            "hovermode": "closest",
            "hoverlabel": {
                "bgcolor": "rgba(255,255,255,0.96)",
                "bordercolor": "#1973B8",
                "font": {"size": 12, "color": "#072146"},
            },
        },
    }


layout = html.Div(
    children=[
        html.Div(
            className="filters-row",
            children=[
                html.Div("Period", className="filter-group-label"),
                dcc.Dropdown(
                    id="merchant-year-filter",
                    options=year_options,
                    value=default_year,
                    clearable=False,
                    className="filter-year",
                ),
                dcc.Dropdown(
                    id="merchant-month-filter",
                    options=month_options,
                    value=default_month,
                    clearable=False,
                    className="filter-month",
                ),
                html.Div("Merchant Name", className="filter-group-label", style={"marginLeft": "40px"}),
                dcc.Input(
                    id="merchant-name-input",
                    type="text",
                    placeholder="Enter merchant name...",
                    className="filter-text-input",
                    style={"marginLeft": "8px"},
                ),
            ],
        ),
        html.Div(
            className="panel-grid",
            children=[build_merchant_summary_card()],
        ),
        html.Div(
            className="panel merchant-detail",
            children=[
                html.Div(id="merchant-detail-title", children="Enter a merchant name to view transactions"),
                dcc.Loading(
                    dash_table.DataTable(
                        id="merchant-transactions-table",
                        columns=[
                            {"name": "Date", "id": "txn_date"},
                            {"name": "Merchant Norm", "id": "merchant_norm"},
                            {"name": "Concept Norm", "id": "concept_norm"},
                            {"name": "Amount", "id": "amount"},
                        ],
                        css=[
                            {
                                "selector": "table",
                                "rule": "border-collapse: separate; border-spacing: 0; min-width: 760px;"
                            }
                        ],
                        style_table={
                            "overflowX": "auto",
                            "width": "100%",
                        },
                        style_cell={
                            "padding": "10px 12px",
                            "fontSize": "13px",
                            "border": "none",
                            "backgroundColor": "white",
                            "color": "#2c3e50",
                            "textAlign": "center",
                        },
                        style_cell_conditional=[
                            {
                                "if": {"column_id": "merchant_norm"},
                                "textAlign": "left",
                                "minWidth": "260px",
                                "width": "260px",
                                "maxWidth": "260px",
                            },
                            {
                                "if": {"column_id": "concept_norm"},
                                "textAlign": "left",
                                "minWidth": "200px",
                                "width": "200px",
                                "maxWidth": "200px",
                            },
                            {
                                "if": {"column_id": "txn_date"},
                                "minWidth": "110px",
                                "width": "110px",
                                "maxWidth": "110px",
                            },
                            {
                                "if": {"column_id": "amount"},
                                "minWidth": "110px",
                                "width": "110px",
                                "maxWidth": "110px",
                            },
                        ],
                        style_header={
                            "backgroundColor": "white",
                            "fontWeight": "600",
                            "color": "#072146",
                            "borderBottom": "1px solid #e6ebf2",
                        },
                        style_data={
                            "borderBottom": "1px solid #f0f3f7",
                        },
                        data=[],
                        cell_selectable=False,
                        row_selectable=False,
                        column_selectable=False,
                        page_size=10,
                        style_data_conditional=[
                            {
                                "if": {"state": "active"},
                                "backgroundColor": "rgba(25, 115, 184, 0.10)",
                                "border": "1px solid rgba(25, 115, 184, 0.18)",
                                "color": "#072146",
                            },
                            {
                                "if": {"state": "selected"},
                                "backgroundColor": "rgba(25, 115, 184, 0.14)",
                                "border": "1px solid rgba(25, 115, 184, 0.24)",
                                "color": "#072146",
                            },
                        ],
                    )
                )
            ],
        )
    ],
)


@dash.callback(
    Output("merchant-current-value", "children"),
    Output("merchant-summary-subtitle", "children"),
    Output("merchant-avg-12m", "children"),
    Output("merchant-vs-avg", "children"),
    Output("merchant-vs-avg", "className"),
    Output("merchant-accumulated-12m", "children"),
    Output("merchant-trend-chart", "figure"),
    Output("merchant-transactions-table", "data"),
    Output("merchant-detail-title", "children"),
    Input("merchant-year-filter", "value"),
    Input("merchant-month-filter", "value"),
    Input("merchant-name-input", "value"),
    Input("visibility-store", "data"),
)
def update_merchant_data(year, month, merchant_name, visibility_data):
    hidden = not bool(visibility_data and visibility_data.get("visible", True))
    if not year or not month or not merchant_name:
        return (
            "-", "No merchant selected",
            "-", "-", "metric-value metric-neutral", "-",
            empty_trend_figure(), [], "Enter a merchant name to view transactions"
        )

    merchant_name = merchant_name.strip()
    if not merchant_name:
        return (
            "-", "No merchant selected",
            "-", "-", "metric-value metric-neutral", "-",
            empty_trend_figure(), [], "Enter a merchant name to view transactions"
        )

    selected_month = f"{year}-{month}-01"

    merchant_data = get_merchant_monthly_total(merchant_name, selected_month)
    transactions_df = get_merchant_transactions(merchant_name, selected_month)

    if merchant_data["current_total"] == 0.0:
        return (
            "-", f"No transactions found for '{merchant_name}'",
            "-", "-", "metric-value metric-neutral", "-",
            empty_trend_figure(), [], f"No transactions for '{merchant_name}'"
        )

    # Format card values
    current_value = format_eur_es(merchant_data["current_total"], masked=hidden)
    avg_12m = format_eur_es(merchant_data["avg_12m"], masked=hidden)
    pct_vs_avg = format_pct_es(merchant_data["pct_vs_avg"], masked=hidden)
    deviation_cls = deviation_class("expense", merchant_data["pct_vs_avg"])
    accumulated_12m = format_eur_es(merchant_data["accumulated_12m"], masked=hidden)

    # Build trend chart
    trend_fig = build_merchant_trend_figure(
        merchant_data["series_months"],
        merchant_data["series_values"],
        hidden=hidden,
    )

    # Format transactions table
    if not transactions_df.empty:
        transactions_df["amount"] = transactions_df["amount"].apply(lambda v: format_eur_es(v, masked=hidden))
        table_data = transactions_df.to_dict("records")
    else:
        table_data = []

    return (
        current_value,
        f"Merchant: {merchant_name}",
        avg_12m,
        pct_vs_avg,
        deviation_cls,
        accumulated_12m,
        trend_fig,
        table_data,
        f"Transactions - {merchant_name}"
    )