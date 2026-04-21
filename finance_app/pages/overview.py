import pandas as pd
import dash
from dash import html, dcc, Input, Output

from components.expense_insight_card import build_expense_insight_card
from components.income_insight_card import build_income_insight_card
from components.savings_activity_card import build_savings_activity_card
from components.monthly_trend_panel import (
    build_monthly_trend_panel,
    empty_bar_figure,
    build_monthly_trend_figure,
)

from services.finance_queries import (
    get_available_months,
    get_expense_insight,
    get_income_insight,
    get_savings_insight,
    get_monthly_overview_window,
)

from utils.formatters import (
    format_eur_es,
    format_pct_es,
    deviation_class,
    format_daily_es,
)

dash.register_page(__name__, path="/", name="Monthly Overview")

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


def prepare_monthly_window(df: pd.DataFrame, selected_month: str, months_back: int = 12) -> pd.DataFrame:
    selected_ts = pd.Timestamp(selected_month)
    month_range = pd.date_range(end=selected_ts, periods=months_back + 1, freq="MS")

    if df is None or df.empty:
        base = pd.DataFrame({"month": month_range})
        base["income_total"] = 0.0
        base["expense_total"] = 0.0
        base["savings_total"] = 0.0
        base["net_total"] = 0.0
        base["cumulative_savings"] = 0.0
    else:
        base = df.copy()
        base["month"] = pd.to_datetime(base["month"]).dt.to_period("M").dt.to_timestamp()

        base = (
            pd.DataFrame({"month": month_range})
            .merge(base, on="month", how="left")
            .fillna({
                "income_total": 0.0,
                "expense_total": 0.0,
                "savings_total": 0.0,
                "net_total": 0.0,
                "cumulative_savings": 0.0,
            })
        )

    base["net_total"] = base.get("net_total", base["income_total"] - base["expense_total"])
    base["cumulative_savings"] = base.get("cumulative_savings", base["savings_total"].cumsum())
    base["label"] = base["month"].dt.strftime("%b %y")
    base["is_selected"] = base["month"] == selected_ts
    return base


def aggregate_to_four_month_periods(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(
            columns=[
                "period_start",
                "label",
                "income_total",
                "expense_total",
                "net_total",
                "savings_total",
                "cumulative_savings",
                "is_selected",
            ]
        )

    base = df.copy()
    base["month"] = pd.to_datetime(base["month"])
    base["period_num"] = ((base["month"].dt.month - 1) // 4) + 1
    base["period_start_month"] = ((base["period_num"] - 1) * 4) + 1
    base["period_start"] = pd.to_datetime(
        {
            "year": base["month"].dt.year,
            "month": base["period_start_month"],
            "day": 1,
        }
    )

    grouped = (
        base.groupby("period_start", as_index=False)
        .agg(
            income_total=("income_total", "sum"),
            expense_total=("expense_total", "sum"),
            net_total=("net_total", "sum"),
            savings_total=("savings_total", "sum"),
            is_selected=("is_selected", "max"),
        )
        .sort_values("period_start")
    )

    grouped["cumulative_savings"] = grouped["savings_total"].cumsum()

    month_labels = {1: "Jan-Apr", 5: "May-Aug", 9: "Sep-Dec"}
    grouped["label"] = grouped["period_start"].apply(
        lambda d: f"{month_labels[d.month]} {str(d.year)[2:]}"
    )
    return grouped


layout = html.Div(
    children=[
        html.Div(
            className="filters-row",
            children=[
                html.Div("Period", className="filter-group-label"),
                dcc.Dropdown(
                    id="year-filter",
                    options=year_options,
                    value=default_year,
                    clearable=False,
                    className="filter-year",
                ),
                dcc.Dropdown(
                    id="month-filter",
                    options=month_options,
                    value=default_month,
                    clearable=False,
                    className="filter-month",
                ),
            ],
        ),
        html.Div(
            className="top-summary-grid",
            children=[
                build_expense_insight_card(),
                build_income_insight_card(),
                build_savings_activity_card(),
            ],
        ),
        html.Div(
            className="panel-grid",
            children=[build_monthly_trend_panel()],
        ),
    ]
)


@dash.callback(
    [
        Output("monthly-trend-desktop", "figure"),
        Output("monthly-trend-mobile", "figure"),
        Output("expense-current", "children"),
        Output("expense-avg-12m", "children"),
        Output("expense-vs-avg", "children"),
        Output("expense-vs-avg", "className"),
        Output("expense-ytd", "children"),
        Output("expense-insight-chart", "figure"),
        Output("expense-burn-rate", "children"),

        Output("income-current", "children"),
        Output("income-avg-12m", "children"),
        Output("income-vs-avg", "children"),
        Output("income-vs-avg", "className"),
        Output("income-ytd", "children"),
        Output("income-insight-chart", "figure"),

        Output("savings-current", "children"),
        Output("savings-avg-12m", "children"),
        Output("savings-vs-avg", "children"),
        Output("savings-vs-avg", "className"),
        Output("savings-ytd", "children"),
        Output("savings-insight-chart", "figure"),
    ],
    [
        Input("year-filter", "value"),
        Input("month-filter", "value"),
    ]
)
def update_dashboard(year, month):
    if not year or not month:
        empty = empty_bar_figure()
        return (
            empty, empty,
            "-", "-", "-", "metric-value metric-neutral", "-", empty, "-",
            "-", "-", "-", "metric-value metric-neutral", "-", empty,
            "-", "-", "-", "metric-value metric-neutral", "-", empty,
        )

    selected_month = f"{year}-{month}-01"

    trend_df_raw = get_monthly_overview_window(selected_month)
    trend_df_monthly = prepare_monthly_window(trend_df_raw, selected_month=selected_month, months_back=12)
    trend_df_four_month = aggregate_to_four_month_periods(trend_df_monthly)

    expense = get_expense_insight(selected_month)
    income = get_income_insight(selected_month)
    savings = get_savings_insight(selected_month)

    desktop_figure = build_monthly_trend_figure(trend_df_monthly)
    mobile_figure = build_monthly_trend_figure(trend_df_four_month)

    expense_months = expense["series_months"]
    expense_values = expense["series_values"]

    expense_figure = build_insight_sparkline(
        months=expense_months,
        values=expense_values,
        line_color="rgba(190, 62, 70, 0.65)",
        fill_color="rgba(190, 62, 70, 0.04)",
        dot_color="rgba(190, 62, 70, 0.95)",
        border_color=["rgba(190,62,70,0)"] * (len(expense_values) - 1) + ["rgba(190,62,70,1)"] if expense_values else "rgba(190,62,70,1)",
        hover_label="<span style='color:#be3e46;'>●</span> Expense",
        fillpattern_shape="/",
        fillpattern_fg="rgba(190, 62, 70, 0.12)",
        fillpattern_bg="rgba(190, 62, 70, 0.01)",
    )

    income_months = income["series_months"]
    income_values = income["series_values"]

    income_figure = build_insight_sparkline(
        months=income_months,
        values=income_values,
        line_color="rgba(25, 115, 184, 0.65)",
        fill_color="rgba(25, 115, 184, 0.025)",
        dot_color="rgba(25, 115, 184, 0.95)",
        border_color=["rgba(255,255,255,0.95)"] * (len(income_values) - 1) + ["rgba(25,115,184,1)"] if income_values else "rgba(25,115,184,1)",
        hover_label="<span style='color:#1973b8;'>●</span> Income",
        fillpattern_shape="\\",
        fillpattern_fg="rgba(25, 115, 184, 0.12)",
        fillpattern_bg="rgba(25, 115, 184, 0.01)",
    )

    savings_months = savings["series_months"]
    savings_values = savings["series_values"]

    savings_figure = build_insight_sparkline(
        months=savings_months,
        values=savings_values,
        line_color="rgba(214, 143, 34, 0.65)",
        fill_color="rgba(214, 143, 34, 0.025)",
        dot_color="rgba(214, 143, 34, 0.95)",
        border_color="rgba(255, 255, 255, 0.95)",
        hover_label="<span style='color:#d68f22;'>●</span> Savings",
        fillpattern_shape="|",
        fillpattern_fg="rgba(214, 143, 34, 0.18)",
        fillpattern_bg="rgba(214, 143, 34, 0.01)",
    )

    expense_pct = expense["pct_vs_avg"]
    income_pct = income["pct_vs_avg"]
    savings_pct = savings["pct_vs_avg"]

    burn_rate = expense["current_expense"] / 30 if expense["current_expense"] else 0

    return (
        desktop_figure,
        mobile_figure,
        format_eur_es(expense["current_expense"]),
        format_eur_es(expense["avg_12m"]),
        format_pct_es(expense_pct),
        deviation_class("expense", expense_pct),
        format_eur_es(expense["ytd_expense"]),
        expense_figure,
        format_daily_es(burn_rate),

        format_eur_es(income["current_income"]),
        format_eur_es(income["avg_12m"]),
        format_pct_es(income_pct),
        deviation_class("income", income_pct),
        format_eur_es(income["ytd_income"]),
        income_figure,

        format_eur_es(savings["current_savings"]),
        format_eur_es(savings["avg_12m"]),
        format_pct_es(savings_pct),
        deviation_class("savings", savings_pct),
        format_eur_es(savings["ytd_savings"]),
        savings_figure,
    )

def build_insight_sparkline(
    months,
    values,
    line_color,
    fill_color,
    dot_color,
    border_color,
    hover_label,
    fillpattern_shape=None,
    fillpattern_fg=None,
    fillpattern_bg=None,
):
    y_min = min(values) if values else 0
    y_max = max(values) if values else 1

    if y_min < 0:
        lower = y_min * 1.25
    else:
        lower = 0

    upper = y_max * 1.5 if y_max != 0 else 1

    return {
        "data": [
            {
                "x": months,
                "y": values,
                "customdata": [format_eur_es(v) for v in values],
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
                        "color": border_color,
                    },
                },
                "fillcolor": fill_color,
                "hovertemplate": (
                    "<b>%{x}</b><br>"
                    f"{hover_label}: " + "%{customdata}"
                    "<extra></extra>"
                ),
                "fillpattern": {
                    "shape": fillpattern_shape,
                    "size": 6,
                    "solidity": 0.2,
                    "fgcolor": fillpattern_fg,
                    "bgcolor": fillpattern_bg,
                } if fillpattern_shape else None,
            }
        ],
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
            "hoverlabel": {
                "bgcolor": "rgba(255, 255, 255, 0.86)",
                "bordercolor": "rgba(7,33,70,0.10)",
                "font": {
                    "family": "Math, sans-serif",
                    "size": 12,
                    "color": "#46586e",
                },
                "align": "left",
                "namelength": -1,
            },
            "transition": {
                "duration": 400,
                "easing": "cubic-in-out",
            },
        },
    }

@dash.callback(
    Output("year-filter", "value"),
    Output("month-filter", "value"),
    Input("global-period-store", "data"),
    prevent_initial_call=False,
)
def load_period_from_store(period_data):
    year = period_data.get("year") if period_data else None
    month = period_data.get("month") if period_data else None

    selected_year = year if year else default_year
    selected_month = month if month else default_month

    return selected_year, selected_month

@dash.callback(
    Output("global-period-store", "data", allow_duplicate=True),
    Input("year-filter", "value"),
    Input("month-filter", "value"),
    prevent_initial_call=True,
)
def sync_overview_period_to_store(year, month):
    return {
        "year": year,
        "month": month,
    }