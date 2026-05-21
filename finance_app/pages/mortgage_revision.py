import pandas as pd
import dash
from dash import html, dcc, Input, Output, dash_table

from components.mortgage_payment_card import build_mortgage_payment_card
from components.mortgage_interest_card import build_mortgage_interest_card
from components.mortgage_amortization_card import build_mortgage_amortization_card

from services.finance_queries import (
    get_mortgage_payment_insight,
    get_mortgage_interest_insight,
    get_mortgage_amortization_insight,
    get_mortgage_trend_last_10_years,
    get_mortgage_amortization_schedule,
)

from utils.formatters import format_eur_es, format_pct_es, deviation_class

dash.register_page(__name__, path="/mortgage-revision", name="Mortgage Revision")

# Get available years from mortgage data
def get_available_mortgage_years():
    from services.trino_client import get_engine
    engine = get_engine()
    query = "SELECT DISTINCT CAST(charge_date_sk / 10000 AS INTEGER) AS year FROM iceberg.gold.fact_mortgage_payment ORDER BY year DESC"
    df = pd.read_sql(query, engine)
    return df["year"].astype(str).tolist() if not df.empty else [str(pd.Timestamp.now().year)]

years_df = get_available_mortgage_years()
year_options = [{"label": y, "value": y} for y in sorted(years_df, reverse=True)]
default_year = year_options[0]["value"] if year_options else str(pd.Timestamp.now().year)


def build_mortgage_trend_figure(df):
    if df.empty:
        return {"data": [], "layout": {}}

    # Create traces for payment, interest, amortization
    traces = []

    # Payment trace
    traces.append({
        "x": df["year"],
        "y": df["total_payment"],
        "name": "Payment",
        "type": "scatter",
        "mode": "lines+markers",
        "line": {"color": "rgba(190, 62, 70, 0.8)", "width": 3},
        "marker": {"size": 6, "color": "rgba(190, 62, 70, 1)"},
        "hovertemplate": "<b>%{x}</b><br>Payment: %{y:,.0f}€<extra></extra>",
    })

    # Interest trace
    traces.append({
        "x": df["year"],
        "y": df["total_interest"],
        "name": "Interest",
        "type": "scatter",
        "mode": "lines+markers",
        "line": {"color": "rgba(214, 143, 34, 0.8)", "width": 3},
        "marker": {"size": 6, "color": "rgba(214, 143, 34, 1)"},
        "hovertemplate": "<b>%{x}</b><br>Interest: %{y:,.0f}€<extra></extra>",
    })

    # Amortization trace
    traces.append({
        "x": df["year"],
        "y": df["total_amortization"],
        "name": "Amortization",
        "type": "scatter",
        "mode": "lines+markers",
        "line": {"color": "rgba(25, 115, 184, 0.8)", "width": 3},
        "marker": {"size": 6, "color": "rgba(25, 115, 184, 1)"},
        "hovertemplate": "<b>%{x}</b><br>Amortization: %{y:,.0f}€<extra></extra>",
    })

    layout = {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "margin": {"l": 40, "r": 20, "t": 20, "b": 40},
        "xaxis": {
            "showgrid": True,
            "gridcolor": "rgba(0,0,0,0.1)",
            "tickfont": {"size": 12},
        },
        "yaxis": {
            "showgrid": True,
            "gridcolor": "rgba(0,0,0,0.1)",
            "tickformat": ",.0f",
            "tickprefix": "€",
            "tickfont": {"size": 12},
        },
        "showlegend": True,
        "legend": {"orientation": "h", "y": -0.2},
        "hovermode": "closest",
    }

    return {"data": traces, "layout": layout}


layout = html.Div(
    children=[
        html.Div(
            className="filters-row",
            children=[
                html.Div("Year", className="filter-group-label"),
                dcc.Dropdown(
                    id="mortgage-year-filter",
                    options=year_options,
                    value=default_year,
                    clearable=False,
                    className="filter-year",
                ),
            ],
        ),
        html.Div(
            className="top-summary-grid",
            children=[
                build_mortgage_payment_card(),
                build_mortgage_interest_card(),
                build_mortgage_amortization_card(),
            ],
        ),
        html.Div(
            className="panel mortgage-schedule-panel",
            children=[
                html.H3("Mortgage Amortization Schedule", className="panel-title"),
                dcc.Loading(
                    dash_table.DataTable(
                        id="mortgage-amortization-schedule-table",
                        columns=[
                            {"name": "Year", "id": "year"},
                            {"name": "Total Payment", "id": "total_payment", "type": "numeric", "format": {"specifier": ",.0f"}},
                            {"name": "Total Interest", "id": "total_interest", "type": "numeric", "format": {"specifier": ",.0f"}},
                            {"name": "Total Amortization", "id": "total_amortization", "type": "numeric", "format": {"specifier": ",.0f"}},
                            {"name": "Ending Principal", "id": "ending_principal", "type": "numeric", "format": {"specifier": ",.0f"}},
                        ],
                        data=[],
                        page_size=12,
                        sort_action="native",
                        style_table={"overflowX": "auto", "width": "100%"},
                        style_cell={
                            "padding": "10px 12px",
                            "fontSize": "13px",
                            "border": "none",
                            "backgroundColor": "white",
                            "color": "#2c3e50",
                            "textAlign": "center",
                        },
                        style_cell_conditional=[
                            {"if": {"column_id": "year"}, "textAlign": "left", "minWidth": "100px", "width": "100px", "maxWidth": "100px"},
                            {"if": {"column_id": "total_payment"}, "minWidth": "150px", "width": "150px", "maxWidth": "150px"},
                            {"if": {"column_id": "total_interest"}, "minWidth": "150px", "width": "150px", "maxWidth": "150px"},
                            {"if": {"column_id": "total_amortization"}, "minWidth": "150px", "width": "150px", "maxWidth": "150px"},
                            {"if": {"column_id": "ending_principal"}, "minWidth": "150px", "width": "150px", "maxWidth": "150px"},
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
                        style_data_conditional=[
                            {"if": {"state": "active"}, "backgroundColor": "rgba(25, 115, 184, 0.10)", "border": "1px solid rgba(25, 115, 184, 0.18)", "color": "#072146"},
                            {"if": {"state": "selected"}, "backgroundColor": "rgba(25, 115, 184, 0.14)", "border": "1px solid rgba(25, 115, 184, 0.24)", "color": "#072146"},
                            {"if": {"filter_query": "{projected} = True"}, "backgroundColor": "rgba(246, 232, 161, 0.18)"},
                        ],
                    )
                ),
                html.Div(
                    className="mortgage-schedule-summary",
                    children=[
                        html.Div(
                            [
                                html.Span("Total interest paid:", className="schedule-summary-label"),
                                html.Span(id="mortgage-schedule-total-interest", className="schedule-summary-value"),
                            ],
                            className="schedule-summary-item",
                        ),
                        html.Div(
                            [
                                html.Span("Total amortization paid:", className="schedule-summary-label"),
                                html.Span(id="mortgage-schedule-total-amortization", className="schedule-summary-value"),
                            ],
                            className="schedule-summary-item",
                        ),
                    ],
                ),
            ],
        ),
    ]
)


@dash.callback(
    [
        Output("mortgage-payment-current", "children"),
        Output("mortgage-payment-avg-10y", "children"),
        Output("mortgage-payment-vs-avg", "children"),
        Output("mortgage-payment-vs-avg", "className"),
        Output("mortgage-payment-insight-chart", "figure"),
        Output("mortgage-payment-accumulated-to-year", "children"),

        Output("mortgage-interest-current", "children"),
        Output("mortgage-interest-avg-10y", "children"),
        Output("mortgage-interest-vs-avg", "children"),
        Output("mortgage-interest-vs-avg", "className"),
        Output("mortgage-interest-insight-chart", "figure"),
        Output("mortgage-interest-accumulated-to-year", "children"),

        Output("mortgage-amortization-current", "children"),
        Output("mortgage-amortization-avg-10y", "children"),
        Output("mortgage-amortization-vs-avg", "children"),
        Output("mortgage-amortization-vs-avg", "className"),
        Output("mortgage-amortization-insight-chart", "figure"),
        Output("mortgage-amortization-accumulated-to-year", "children"),

        Output("mortgage-amortization-schedule-table", "data"),
        Output("mortgage-schedule-total-interest", "children"),
        Output("mortgage-schedule-total-amortization", "children"),
    ],
    [Input("mortgage-year-filter", "value"), Input("visibility-store", "data")]
)
def update_mortgage_dashboard(year, visibility_data):
    hidden = not bool(visibility_data and visibility_data.get("visible", True))
    if not year:
        empty_figure = {"data": [], "layout": {}}
        return (
            "-", "-", "-", "metric-value metric-neutral", empty_figure, "-",
            "-", "-", "-", "metric-value metric-neutral", empty_figure, "-",
            "-", "-", "-", "metric-value metric-neutral", empty_figure, "-",
            [],
            "-", "-",
        )

    # Get insights
    payment_insight = get_mortgage_payment_insight(year)
    interest_insight = get_mortgage_interest_insight(year)
    amortization_insight = get_mortgage_amortization_insight(year)

    # Get amortization schedule data
    schedule_df = get_mortgage_amortization_schedule()
    total_projected_payment = schedule_df["total_payment"].sum() if not schedule_df.empty else 0.0
    total_projected_interest = schedule_df["total_interest"].sum() if not schedule_df.empty else 0.0
    total_projected_amortization = schedule_df["total_amortization"].sum() if not schedule_df.empty else 0.0
    selected_year_int = int(year)
    accumulated_payment_to_year = schedule_df[schedule_df["year"] <= selected_year_int]["total_payment"].sum() if not schedule_df.empty else 0.0
    accumulated_interest_to_year = schedule_df[schedule_df["year"] <= selected_year_int]["total_interest"].sum() if not schedule_df.empty else 0.0
    accumulated_amortization_to_year = schedule_df[schedule_df["year"] <= selected_year_int]["total_amortization"].sum() if not schedule_df.empty else 0.0

    # Build sparkline figures
    def build_sparkline(years, values, line_color, fill_color, dot_color, fillpattern_shape=None, fillpattern_fg=None, fillpattern_bg=None, hidden=False):
        if not values:
            return {"data": [], "layout": {}}

        y_min = min(values) if values else 0
        y_max = max(values) if values else 1

        lower = y_min * 1.25 if y_min < 0 else 0
        upper = y_max * 1.5 if y_max != 0 else 1

        data = [
            {
                "x": years,
                "y": values,
                "customdata": [format_eur_es(v, masked=hidden) for v in values],
                "type": "scatter",
                "mode": "lines+markers",
                "hoveron": "points",
                "fill": "tozeroy",
                "line": {
                    "color": line_color,
                    "width": 1.6,
                    "shape": "spline",
                    "smoothing": 0.8,
                },
                "marker": {
                    "size": 5,
                    "color": dot_color,
                    "line": {
                        "width": 1,
                        "color": "rgba(255,255,255,0.95)",
                    },
                },
                "fillcolor": fill_color,
                "hovertemplate": "<b>%{x}</b><br>Value: %{customdata}<extra></extra>",
                "fillpattern": {
                    "shape": fillpattern_shape,
                    "size": 6,
                    "solidity": 0.2,
                    "fgcolor": fillpattern_fg,
                    "bgcolor": fillpattern_bg,
                } if fillpattern_shape else None,
            }
        ]

        return {
            "data": data,
            "layout": {
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "margin": {"l": 0, "r": 0, "t": 0, "b": 0},
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
                    "range": [lower, upper],
                },
                "showlegend": False,
                "hovermode": "closest",
            },
        }

    payment_figure = build_sparkline(
        payment_insight["series_years"],
        payment_insight["series_values"],
        "rgba(190, 62, 70, 0.65)",
        "rgba(190, 62, 70, 0.04)",
        "rgba(190, 62, 70, 0.95)",
        "/",
        "rgba(190, 62, 70, 0.12)",
        "rgba(190, 62, 70, 0.01)",
        hidden=hidden,
    )

    interest_figure = build_sparkline(
        interest_insight["series_years"],
        interest_insight["series_values"],
        "rgba(214, 143, 34, 0.65)",
        "rgba(214, 143, 34, 0.025)",
        "rgba(214, 143, 34, 0.95)",
        "|",
        "rgba(214, 143, 34, 0.18)",
        "rgba(214, 143, 34, 0.01)",
        hidden=hidden,
    )

    amortization_figure = build_sparkline(
        amortization_insight["series_years"],
        amortization_insight["series_values"],
        "rgba(25, 115, 184, 0.65)",
        "rgba(25, 115, 184, 0.025)",
        "rgba(25, 115, 184, 0.95)",
        "\\",
        "rgba(25, 115, 184, 0.12)",
        "rgba(25, 115, 184, 0.01)",
        hidden=hidden,
    )

    return (
        format_eur_es(payment_insight["current"], masked=hidden),
        format_eur_es(payment_insight["avg_10y"], masked=hidden),
        format_pct_es(payment_insight["pct_vs_avg"], masked=hidden),
        deviation_class("expense", payment_insight["pct_vs_avg"]),  # Higher payment is bad
        payment_figure,
        f"{format_eur_es(accumulated_payment_to_year, masked=hidden)}/{format_eur_es(total_projected_payment, masked=hidden)} ({format_pct_es(accumulated_payment_to_year / total_projected_payment * 100, masked=hidden) if total_projected_payment > 0 else '0,00%'})",

        format_eur_es(interest_insight["current"], masked=hidden),
        format_eur_es(interest_insight["avg_10y"], masked=hidden),
        format_pct_es(interest_insight["pct_vs_avg"], masked=hidden),
        deviation_class("expense", interest_insight["pct_vs_avg"]),  # Higher interest is bad
        interest_figure,
        f"{format_eur_es(accumulated_interest_to_year, masked=hidden)}/{format_eur_es(total_projected_interest, masked=hidden)} ({format_pct_es(accumulated_interest_to_year / total_projected_interest * 100, masked=hidden) if total_projected_interest > 0 else '0,00%'})",

        format_eur_es(amortization_insight["current"], masked=hidden),
        format_eur_es(amortization_insight["avg_10y"], masked=hidden),
        format_pct_es(amortization_insight["pct_vs_avg"], masked=hidden),
        deviation_class("income", amortization_insight["pct_vs_avg"]),  # Higher amortization is good
        amortization_figure,
        f"{format_eur_es(accumulated_amortization_to_year, masked=hidden)}/{format_eur_es(total_projected_amortization, masked=hidden)} ({format_pct_es(accumulated_amortization_to_year / total_projected_amortization * 100, masked=hidden) if total_projected_amortization > 0 else '0,00%'})",

        schedule_df.to_dict("records"),
        format_eur_es(total_projected_interest, masked=hidden),
        format_eur_es(total_projected_amortization, masked=hidden),
    )