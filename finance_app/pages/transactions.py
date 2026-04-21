import pandas as pd
import dash
from dash import html, dcc, Input, Output, dash_table
import plotly.graph_objects as go

from components.category_donut_card import build_category_donut_card
from services.finance_queries import (
    get_available_months,
    get_monthly_expense_breakdown_by_category,
    get_category_12m_trend,
    get_transactions_by_category,
)
from utils.formatters import format_eur_es

dash.register_page(__name__, path="/transactions", name="Detailed Operations")


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


def empty_donut_figure(message: str = "No data available"):
    return {
        "data": [],
        "layout": {
            "paper_bgcolor": "rgba(255,255,255,1)",
            "plot_bgcolor": "rgba(255,255,255,1)",
            "margin": {"l": 20, "r": 20, "t": 20, "b": 20},
            "annotations": [
                {
                    "text": message,
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 0.5,
                    "showarrow": False,
                    "font": {"size": 14, "color": "#7b8a9a"},
                }
            ],
            "showlegend": False,
        },
    }


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


def get_hovered_label(hover_data):
    if hover_data and "points" in hover_data and hover_data["points"]:
        return hover_data["points"][0].get("label")
    return None


def build_category_donut_figure(
    df: pd.DataFrame,
    category_l1: str,
    title: str,
    hovered_label: str | None = None,
    selected_label: str | None = None,
    avg_12m: float = 0.0,
    pct_vs_avg: float = 0.0,
    deviation_color: str = "#7b8a9a",
):
    required_cols = {"category_l1", "category_l2", "total_amount"}

    if df is None or df.empty or not required_cols.issubset(df.columns):
        return empty_donut_figure(f"No {title.lower()} data")

    cat_df = df[df["category_l1"] == category_l1].copy()

    if cat_df.empty:
        return empty_donut_figure(f"No {title.lower()} data")

    cat_df["category_l2"] = cat_df["category_l2"].fillna("other")
    cat_df["total_amount"] = cat_df["total_amount"].astype(float)

    total = cat_df["total_amount"].sum()

    pulls = [
        0.06 if label == hovered_label else 0.0
        for label in cat_df["category_l2"]
    ]

    line_colors_base = [
        "#1973B8",
        "#00A86B",
        "#F8CD51",
        "#DA3851",
        "#6B5DD3",
        "#F57C00",
        "#009688",
        "#9C27B0",
    ]
    line_colors = [
        line_colors_base[i % len(line_colors_base)]
        for i in range(len(cat_df))
    ]

    segment_fill_colors = []
    segment_line_widths = []
    segment_line_colors = []

    for i, label in enumerate(cat_df["category_l2"]):
        base_color = line_colors[i]

        is_selected = label == selected_label
        is_hovered = label == hovered_label

        if is_selected:
            segment_fill_colors.append(base_color)
            segment_line_colors.append("#072146")
            segment_line_widths.append(3)
        elif is_hovered:
            segment_fill_colors.append(base_color)
            segment_line_colors.append("white")
            segment_line_widths.append(3)
        else:
            segment_fill_colors.append(base_color)
            segment_line_colors.append("white")
            segment_line_widths.append(8)

    fig = go.Figure(
        data=[
            go.Pie(
                labels=cat_df["category_l2"],
                values=cat_df["total_amount"],
                hole=0.72,
                sort=False,
                direction="clockwise",
                textinfo="percent",  
                
                marker={
                    "colors": segment_fill_colors,
                    "line": {
                        "color": segment_line_colors,
                        "width": segment_line_widths,
                    },
                },
                customdata=[
                    [format_eur_es(v)]
                    for v in cat_df["total_amount"]
                ],

                hovertemplate=(
                    "<b>%{label}</b><br>"
                    "Amount: %{customdata[0]}<br>"
                    "Share: %{percent}<extra></extra>"
                ),
            )
        ]
    )

    fig.update_layout(
        paper_bgcolor="rgba(255,255,255,1)",
        plot_bgcolor="rgba(255,255,255,1)",
        margin={"l": 12, "r": 12, "t": 18, "b": 12},
        showlegend=True,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.18,
            "xanchor": "center",
            "x": 0.5,
            "font": {"size": 11, "color": "#4a5a6a"},
        },
        annotations=[
            {
                "text": (
                    f"<span style='font-size:12px;color:#7b8a9a'>Monthtly Total</span><br>"
                    f"<b>{format_eur_es(total)}</b><br>"
                    f"<span style='font-size:12px;color:#7b8a9a'>Avg Last 12 mo</span><br>"
                    f"<span style='font-size:11px;>{format_eur_es(avg_12m)}</span>  "
                    f"<span style='font-size:11px;color:{deviation_color}'><b>{format_pct_es(pct_vs_avg)}</b></span><br>"                    
                ),
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "align": "center",
            }
        ]
    )

    return fig


def build_category_trend_figure(
    trend_df: pd.DataFrame,
    category_l1: str,
    line_color: str,
):
    required_cols = {"month", "category_l1", "total_amount"}

    if trend_df is None or trend_df.empty or not required_cols.issubset(trend_df.columns):
        return empty_trend_figure()

    cat_df = trend_df[trend_df["category_l1"] == category_l1].copy()

    if cat_df.empty:
        return empty_trend_figure()

    cat_df["month"] = pd.to_datetime(cat_df["month"])
    cat_df["label"] = cat_df["month"].dt.strftime("%b %y")
    cat_df["total_amount"] = cat_df["total_amount"].astype(float)

    y_max = cat_df["total_amount"].max() if not cat_df.empty else 1

    return {
        "data": [
            {
                "x": cat_df["label"],
                "y": cat_df["total_amount"],
                "customdata": [format_eur_es(v) for v in cat_df["total_amount"]],
                "type": "scatter",
                "mode": "lines+markers",
                "fill": "tozeroy",
                "line": {
                    "color": line_color,
                    "width": 1.4,
                    "shape": "spline",
                    "smoothing": 0.8,
                },
                "marker": {
                    "size": 3,
                    "color": line_color,
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
                "range": [0, y_max * 1.35 if y_max > 0 else 1],
            },
            "showlegend": False,
            "hovermode": "closest",
            "hoverlabel": {
                "bgcolor": "rgba(255,255,255,0.96)",
                "bordercolor": line_color,
                "font": {"size": 12, "color": "#072146"},
            },
        },
    }


layout = html.Div(
    children=[
        dcc.Store(id="transactions-breakdown-data"),
        dcc.Store(id="transactions-trend-data"),
        dcc.Store(id="transactions-selected-segment"),
        html.Div(
            className="filters-row",
            children=[
                html.Div("Period", className="filter-group-label"),
                dcc.Dropdown(
                    id="transactions-year-filter",
                    options=year_options,
                    value=default_year,
                    clearable=False,
                    className="filter-year",
                ),
                dcc.Dropdown(
                    id="transactions-month-filter",
                    options=month_options,
                    value=default_month,
                    clearable=False,
                    className="filter-month",
                ),
            ],
        ),
        html.Div(
            className="panel-grid transactions-grid",
            children=[
                build_category_donut_card("groceries-donut", "groceries-trend", "Groceries"),
                build_category_donut_card("utilities-donut", "utilities-trend", "Utilities"),
                build_category_donut_card("transport-donut", "transport-trend", "Transport"),
                build_category_donut_card("shopping-donut", "shopping-trend", "Shopping"),
                build_category_donut_card("entertainment-donut", "entertainment-trend", "Entertainment"),
                build_category_donut_card("finance-donut", "finance-trend", "Finance"),
            ],
        ),
        html.Div(
            className="panel transactions-detail",
            children=[
                html.Div(id="transactions-detail-title"),
                dcc.Loading(
                    dash_table.DataTable(
                        id="transactions-table",
                        columns=[
                            {"name": "Date", "id": "txn_date"},
                            {"name": "Concept", "id": "merchant"},
                            {"name": "Amount", "id": "amount"},
                        ],
                        css=[
                            {
                                "selector": "table",
                                "rule": "border-collapse: separate; border-spacing: 0; min-width: 560px;"
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
                                "if": {"column_id": "merchant"},
                                "textAlign": "left",
                                "minWidth": "260px",
                                "width": "260px",
                                "maxWidth": "260px",
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
    Output("transactions-table", "data"),
    Output("transactions-detail-title", "children"),
    Input("transactions-selected-segment", "data"),
    Input("transactions-year-filter", "value"),
    Input("transactions-month-filter", "value"),
)
def update_transactions_table(selection, year, month):

    if not selection:
        return [], "Select a segment to view transactions"

    selected_month = f"{year}-{month}-01"

    df = get_transactions_by_category(
        selected_month,
        selection["category_l1"],
        selection["category_l2"],
    )

    df["amount"] = df["amount"].apply(format_eur_es)

    title = f"{selection['category_l1']} / {selection['category_l2']}"

    return df.to_dict("records"), title


@dash.callback(
    Output("transactions-breakdown-data", "data"),
    Output("transactions-trend-data", "data"),
    Input("transactions-year-filter", "value"),
    Input("transactions-month-filter", "value"),
)
def load_transactions_data(year, month):
    if not year or not month:
        return [], []

    selected_month = f"{year}-{month}-01"

    breakdown_df = get_monthly_expense_breakdown_by_category(selected_month)
    trend_df = get_category_12m_trend(selected_month)

    return (
        breakdown_df.to_dict("records"),
        trend_df.to_dict("records"),
    )


@dash.callback(
    Output("groceries-donut", "figure"),
    Output("utilities-donut", "figure"),
    Output("transport-donut", "figure"),
    Output("shopping-donut", "figure"),
    Output("entertainment-donut", "figure"),
    Output("finance-donut", "figure"),
    Output("groceries-trend", "figure"),
    Output("utilities-trend", "figure"),
    Output("transport-trend", "figure"),
    Output("shopping-trend", "figure"),
    Output("entertainment-trend", "figure"),
    Output("finance-trend", "figure"),
    Input("transactions-breakdown-data", "data"),
    Input("transactions-trend-data", "data"),
    Input("groceries-donut", "hoverData"),
    Input("utilities-donut", "hoverData"),
    Input("transport-donut", "hoverData"),
    Input("shopping-donut", "hoverData"),
    Input("entertainment-donut", "hoverData"),
    Input("finance-donut", "hoverData"),
)
def render_transaction_charts(
    breakdown_data,
    trend_data,
    groceries_hover,
    utilities_hover,
    transport_hover,
    shopping_hover,
    entertainment_hover,
    finance_hover,
):
    breakdown_df = pd.DataFrame(breakdown_data or [])
    trend_df = pd.DataFrame(trend_data or [])

    groceries_metrics = get_category_summary_metrics(trend_df, "groceries")
    utilities_metrics = get_category_summary_metrics(trend_df, "utilities")
    transport_metrics = get_category_summary_metrics(trend_df, "transport")
    shopping_metrics = get_category_summary_metrics(trend_df, "shopping")
    entertainment_metrics = get_category_summary_metrics(trend_df, "entertainment")
    finance_metrics = get_category_summary_metrics(trend_df, "finance")

    groceries_donut = build_category_donut_figure(
        breakdown_df,
        "groceries",
        "Groceries",
        hovered_label=get_hovered_label(groceries_hover),
        avg_12m=groceries_metrics["avg_12m"],
        pct_vs_avg=groceries_metrics["pct_vs_avg"],
        deviation_color=groceries_metrics["deviation_color"],
    )
    utilities_donut = build_category_donut_figure(
        breakdown_df,
        "utilities",
        "Utilities",
        hovered_label=get_hovered_label(utilities_hover),
        avg_12m=utilities_metrics["avg_12m"],
        pct_vs_avg=utilities_metrics["pct_vs_avg"],
        deviation_color=utilities_metrics["deviation_color"],
    )
    transport_donut = build_category_donut_figure(
        breakdown_df,
        "transport",
        "Transport",
        hovered_label=get_hovered_label(transport_hover),
        avg_12m=transport_metrics["avg_12m"],
        pct_vs_avg=transport_metrics["pct_vs_avg"],
        deviation_color=transport_metrics["deviation_color"],
    )
    shopping_donut = build_category_donut_figure(
        breakdown_df,
        "shopping",
        "Shopping",
        hovered_label=get_hovered_label(shopping_hover),
        avg_12m=shopping_metrics["avg_12m"],
        pct_vs_avg=shopping_metrics["pct_vs_avg"],
        deviation_color=shopping_metrics["deviation_color"],
    )
    entertainment_donut = build_category_donut_figure(
        breakdown_df,
        "entertainment",
        "Entertainment",
        hovered_label=get_hovered_label(entertainment_hover),
        avg_12m=entertainment_metrics["avg_12m"],
        pct_vs_avg=entertainment_metrics["pct_vs_avg"],
        deviation_color=entertainment_metrics["deviation_color"],
    )
    finance_donut = build_category_donut_figure(
        breakdown_df,
        "finance",
        "Finance",
        hovered_label=get_hovered_label(finance_hover),
        avg_12m=finance_metrics["avg_12m"],
        pct_vs_avg=finance_metrics["pct_vs_avg"],
        deviation_color=finance_metrics["deviation_color"],
    )

    groceries_trend = build_category_trend_figure(trend_df, "groceries", "#1973B8")
    utilities_trend = build_category_trend_figure(trend_df, "utilities", "#F8CD51")
    transport_trend = build_category_trend_figure(trend_df, "transport", "#6B5DD3")
    shopping_trend = build_category_trend_figure(trend_df, "shopping", "#00A3A3")
    entertainment_trend = build_category_trend_figure(trend_df, "entertainment", "#DA3851")
    finance_trend = build_category_trend_figure(trend_df, "finance", "#00A86B")

    return (
        groceries_donut,
        utilities_donut,
        transport_donut,
        shopping_donut,
        entertainment_donut,
        finance_donut,
        groceries_trend,
        utilities_trend,
        transport_trend,
        shopping_trend,
        entertainment_trend,
        finance_trend,
    )

@dash.callback(
    Output("transactions-selected-segment", "data"),
    Input("groceries-donut", "clickData"),
    Input("utilities-donut", "clickData"),
    Input("transport-donut", "clickData"),
    Input("shopping-donut", "clickData"),
    Input("entertainment-donut", "clickData"),
    Input("finance-donut", "clickData"),
    prevent_initial_call=True,
)
def update_selected_segment(*clicks):

    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    click_data = ctx.triggered[0]["value"]

    if not click_data or "points" not in click_data:
        return dash.no_update

    label = click_data["points"][0]["label"]

    category_map = {
        "groceries-donut": "groceries",
        "utilities-donut": "utilities",
        "transport-donut": "transport",
        "shopping-donut": "shopping",
        "entertainment-donut": "entertainment",
        "finance-donut": "finance",
    }

    return {
        "category_l1": category_map.get(trigger_id),
        "category_l2": label,
    }


def format_pct_es(value: float) -> str:
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.1f}%".replace(".", ",")


def get_category_summary_metrics(trend_df: pd.DataFrame, category_l1: str):
    required_cols = {"month", "category_l1", "total_amount"}

    if trend_df is None or trend_df.empty or not required_cols.issubset(trend_df.columns):
        return {
            "current_amount": 0.0,
            "avg_12m": 0.0,
            "pct_vs_avg": 0.0,
            "deviation_class": "metric-neutral",
            "deviation_color": "#7b8a9a",
        }

    cat_df = trend_df[trend_df["category_l1"] == category_l1].copy()

    if cat_df.empty:
        return {
            "current_amount": 0.0,
            "avg_12m": 0.0,
            "pct_vs_avg": 0.0,
            "deviation_class": "metric-neutral",
            "deviation_color": "#7b8a9a",
        }

    cat_df["month"] = pd.to_datetime(cat_df["month"])
    cat_df["total_amount"] = cat_df["total_amount"].astype(float)
    cat_df = cat_df.sort_values("month")

    current_amount = float(cat_df["total_amount"].iloc[-1] or 0.0)
    previous_12 = cat_df.iloc[:-1].tail(12)
    avg_12m = float(previous_12["total_amount"].mean()) if not previous_12.empty else 0.0

    if avg_12m > 0:
        pct_vs_avg = ((current_amount - avg_12m) / avg_12m) * 100.0
    else:
        pct_vs_avg = 0.0

    if pct_vs_avg > 0:
        deviation_color = "#DA3851"   # rojo, más gasto que la media
        deviation_class = "metric-negative"
    elif pct_vs_avg < 0:
        deviation_color = "#00A86B"   # verde, menos gasto que la media
        deviation_class = "metric-positive"
    else:
        deviation_color = "#7b8a9a"
        deviation_class = "metric-neutral"

    return {
        "current_amount": current_amount,
        "avg_12m": avg_12m,
        "pct_vs_avg": pct_vs_avg,
        "deviation_class": deviation_class,
        "deviation_color": deviation_color,
    }

@dash.callback(
    Output("transactions-year-filter", "value"),
    Output("transactions-month-filter", "value"),
    Input("global-period-store", "data"),
    prevent_initial_call=False,
)
def load_transactions_period_from_store(period_data):
    year = period_data.get("year") if period_data else None
    month = period_data.get("month") if period_data else None

    selected_year = year if year else default_year
    selected_month = month if month else default_month

    return selected_year, selected_month

@dash.callback(
    Output("global-period-store", "data", allow_duplicate=True),
    Input("transactions-year-filter", "value"),
    Input("transactions-month-filter", "value"),
    prevent_initial_call=True,
)
def sync_transactions_period_to_store(year, month):
    return {
        "year": year,
        "month": month,
    }