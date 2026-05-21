import pandas as pd
import dash
from dash import html, dcc, Input, Output

from components.monthly_trend_panel import build_monthly_trend_figure, empty_bar_figure
from services.finance_queries import (
    get_available_months,
    get_same_month_last_years,
    get_yearly_totals_last_years,
)


dash.register_page(__name__, path="/year-evolution", name="Year Evolution")

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


layout = html.Div(
    children=[
        html.Div(
            className="filters-row",
            children=[
                html.Div("Period", className="filter-group-label"),
                dcc.Dropdown(
                    id="year-filter",
                    options=year_options,
                    value=year_options[0]["value"] if year_options else None,
                    clearable=False,
                    className="filter-year",
                ),
                dcc.Dropdown(
                    id="month-filter",
                    options=month_options,
                    value=month_options[0]["value"] if month_options else None,
                    clearable=False,
                    className="filter-month",
                ),
            ],
        ),
        html.Div(
            className="panel-grid year-evolution-desktop",
            children=[
                html.Div(
                    className="panel panel-full-width",
                    children=[
                        html.H3("Selected Month Comparison", className="panel-title"),
                        dcc.Graph(id="year-evolution-month-compare-chart-desktop", figure=empty_bar_figure("Loading month comparison")),
                    ],
                ),
                html.Div(
                    className="panel panel-full-width",
                    children=[
                        html.H3("Annual Totals", className="panel-title"),
                        dcc.Graph(id="year-evolution-year-total-chart-desktop", figure=empty_bar_figure("Loading annual totals")),
                    ],
                ),
            ],
        ),
        html.Div(
            className="panel-grid year-evolution-mobile",
            children=[
                html.Div(
                    className="panel panel-full-width",
                    children=[
                        html.H3("Selected Month Comparison", className="panel-title"),
                        dcc.Graph(id="year-evolution-month-compare-chart-mobile", figure=empty_bar_figure("Loading month comparison")),
                    ],
                ),
                html.Div(
                    className="panel panel-full-width",
                    children=[
                        html.H3("Annual Totals", className="panel-title"),
                        dcc.Graph(id="year-evolution-year-total-chart-mobile", figure=empty_bar_figure("Loading annual totals")),
                    ],
                ),
            ],
        ),
    ],
)


@dash.callback(
    Output("year-evolution-month-compare-chart-desktop", "figure"),
    Output("year-evolution-year-total-chart-desktop", "figure"),
    Output("year-evolution-month-compare-chart-mobile", "figure"),
    Output("year-evolution-year-total-chart-mobile", "figure"),
    Input("year-filter", "value"),
    Input("month-filter", "value"),
    Input("visibility-store", "data"),
)
def update_year_evolution(year, month, visibility_data):
    hidden = not bool(visibility_data and visibility_data.get("visible", True))
    if not year or not month:
        empty = empty_bar_figure()
        return empty, empty, empty, empty

    selected_month = f"{year}-{month}-01"
    
    # Desktop: 10 years
    month_df_desktop = get_same_month_last_years(selected_month, years_back=10)
    annual_df_desktop = get_yearly_totals_last_years(selected_month, years_back=10)
    
    # Mobile: 4 years
    month_df_mobile = get_same_month_last_years(selected_month, years_back=4)
    annual_df_mobile = get_yearly_totals_last_years(selected_month, years_back=4)

    if month_df_desktop.empty or annual_df_desktop.empty:
        return empty_bar_figure("No comparison data"), empty_bar_figure("No annual totals data"), empty_bar_figure("No comparison data"), empty_bar_figure("No annual totals data")

    # Process desktop data
    month_df_desktop["label"] = month_df_desktop["year"].astype(str)
    month_df_desktop["is_selected"] = month_df_desktop["year"] == int(year)
    annual_df_desktop["label"] = annual_df_desktop["year"].astype(str)
    annual_df_desktop["is_selected"] = annual_df_desktop["year"] == int(year)

    # Process mobile data
    month_df_mobile["label"] = month_df_mobile["year"].astype(str)
    month_df_mobile["is_selected"] = month_df_mobile["year"] == int(year)
    annual_df_mobile["label"] = annual_df_mobile["year"].astype(str)
    annual_df_mobile["is_selected"] = annual_df_mobile["year"] == int(year)

    month_fig_desktop = build_monthly_trend_figure(month_df_desktop, show_savings_bar=False, show_cumulative_savings=False, chart_type="area", hidden=hidden)
    annual_fig_desktop = build_monthly_trend_figure(annual_df_desktop, show_savings_bar=False, show_cumulative_savings=True, hidden=hidden)
    
    month_fig_mobile = build_monthly_trend_figure(month_df_mobile, show_savings_bar=False, show_cumulative_savings=False, chart_type="area", hidden=hidden)
    annual_fig_mobile = build_monthly_trend_figure(annual_df_mobile, show_savings_bar=False, show_cumulative_savings=True, hidden=hidden)

    return month_fig_desktop, annual_fig_desktop, month_fig_mobile, annual_fig_mobile
