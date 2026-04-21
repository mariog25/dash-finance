from dash import html, dcc
import pandas as pd
import plotly.graph_objects as go

from config.finance_theme import SEMANTIC
from config.finance_theme import hoverlabel
from utils.formatters import format_eur_es, format_k_es 

def empty_bar_figure(message: str = "No data available for the selected period"):
    return {
        "data": [],
        "layout": {
            "paper_bgcolor": "white",
            "plot_bgcolor": "white",
            "margin": {"l": 40, "r": 20, "t": 20, "b": 40},
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
                    "font": {"size": 14, "color": "#7b8a9a"},
                }
            ],
        },
    }

def build_monthly_trend_figure(df: pd.DataFrame):
    if df.empty:
        return empty_bar_figure()

    expense_cd = list(zip(
        [format_eur_es(v) for v in df["expense_total"]],
        [format_eur_es(v) for v in df["income_total"]],
        [format_eur_es(v) for v in df["net_total"]],
        [format_eur_es(v) for v in df["cumulative_savings"]],
    ))
    income_cd = expense_cd

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df["label"],
            y=df["expense_total"],
            name="Expenses",
            offsetgroup="expense",
            customdata=expense_cd,
            text=[format_k_es(v) if float(v or 0) != 0 else "" for v in df["expense_total"]],
            texttemplate="%{text}",
            textposition="outside",
            cliponaxis=False,
            textfont={
                "size": 12,
                "color": SEMANTIC["expense"]["line_soft"],
            },
            marker={
                "color": SEMANTIC["expense"]["fill"],
                "line": {
                    "color": SEMANTIC["expense"]["line"],
                    "width": 1.1
                },
                "pattern": {
                    "shape": "/",
                    "size": 8,
                    "solidity": 0.18,
                    "fgcolor": SEMANTIC["expense"]["pattern_fg"],
                    "bgcolor": SEMANTIC["expense"]["pattern_bg"],
                },
                "cornerradius": "32%",
            },
            hoverlabel={
                "bgcolor": "rgba(255,255,255,0.98)",
                "bordercolor": SEMANTIC["expense"]["line"],
            },
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Expenses: %{customdata[0]}<br>"
                "<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Bar(
            x=df["label"],
            y=df["income_total"],
            name="Income",
            offsetgroup="income",
            customdata=income_cd,
            text=[format_k_es(v) if float(v or 0) != 0 else "" for v in df["income_total"]],
            texttemplate="%{text}",
            textposition="outside",
            cliponaxis=False,
            textfont={
                "size": 12,
                "color": SEMANTIC["income"]["line_soft"],
            },
            marker={
                "color": SEMANTIC["income"]["fill"],
                "line": {"color": SEMANTIC["income"]["line"], "width": 1.1},
                "pattern": {
                    "shape": "\\",
                    "size": 8,
                    "solidity": 0.18,
                    "fgcolor": SEMANTIC["income"]["pattern_fg"],
                    "bgcolor": SEMANTIC["income"]["pattern_bg"],
                },
                "cornerradius": "32%",
            },
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Income: %{customdata[1]}<br>"
                "<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["label"],
            y=df["net_total"],
            mode="lines+markers",
            name="Net",
            yaxis="y",
            line={"color": SEMANTIC["net"]["line"], "width": 0.8, "shape": "spline", "smoothing": 0.55},
            marker={"size": 3, "color": SEMANTIC["net"]["line"]},
            customdata=[[format_eur_es(v)] for v in df["net_total"]],
            hovertemplate="<b>%{x}</b><br>Net: %{customdata[0]}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["label"],
            y=df["cumulative_savings"],
            mode="lines+markers",
            name="Accumulated savings",
            yaxis="y2",
            line={"color": SEMANTIC["savings"]["line"], "width": 1.3, "shape": "spline", "smoothing": 0.5},
            marker={
                "size": 4,
                "color": SEMANTIC["savings"]["line"],
                "line": {"color": "rgba(255,255,255,0.92)", "width": 1.2},
            },
            customdata=[[format_eur_es(v)] for v in df["cumulative_savings"]],
            hovertemplate="<b>%{x}</b><br>Accumulated savings: %{customdata[0]}<extra></extra>",
        )
    )

    selected_index = df.index[df["is_selected"]].tolist()
    selected_pos = selected_index[0] if selected_index else None

    fig.update_layout(
        paper_bgcolor="rgba(255,255,255,1)",
        plot_bgcolor="rgba(255,255,255,1)",
        margin={"l": 56, "r": 58, "t": 28, "b": 48},
        barmode="group",
        bargap=0.26,
        bargroupgap=0.14,
        barcornerradius="32%",
        hovermode="closest",
        hoverlabel={
            "bgcolor": "rgba(255,255,255,0.86)",
            "bordercolor": "rgba(7,33,70,0.08)",
            "font": {"family": "Math, sans-serif", "size": 12, "color": "#46586e"},
        },
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0.0,
            "font": {"size": 9, "color": "#4a5a6a"},
            "entrywidth": 0,
            "entrywidthmode": "pixels",
        },
        xaxis={
            "showgrid": False,
            "tickfont": {"size": 12, "color": "#4a5a6a"},
            "fixedrange": True,
        },
        yaxis={
            "title": {
                "text": "Income / Expense / Net",
                "font": {"size": 12, "color": "#7b8a9a"},
            },
            "tickfont": {"size": 12, "color": "#4a5a6a"},
            "gridcolor": "rgba(7,33,70,0.06)",
            "zerolinecolor": "rgba(7,33,70,0.14)",
            "fixedrange": True,
        },
        yaxis2={
            "title": {
                "text": "Accumulated savings",
                "font": {"size": 12, "color": "#a3722d"},
            },
            "tickfont": {"size": 12, "color": "#a3722d"},
            "overlaying": "y",
            "side": "right",
            "showgrid": False,
            "fixedrange": True,
        },
        shapes=(
            [
                {
                    "type": "rect",
                    "xref": "x",
                    "yref": "paper",
                    "x0": max(selected_pos - 0.46, -0.5),
                    "x1": min(selected_pos + 0.46, len(df) - 0.5),
                    "y0": 0,
                    "y1": 1,
                    "fillcolor": "rgba(25,115,184,0.04)",
                    "line": {"width": 0},
                    "layer": "below",
                }
            ] if selected_pos is not None else []
        ),
        transition={"duration": 350, "easing": "cubic-in-out"},
    )

    return fig


def build_monthly_trend_panel():
    return html.Div(
        className="panel panel-large panel-full-width",
        children=[
            html.H3("Income vs Expense and Savings Trend", className="panel-title"),

            html.Div(
                className="trend-graph-desktop",
                children=[
                    dcc.Graph(
                        id="monthly-trend-desktop",
                        figure=empty_bar_figure(),
                        config={"displayModeBar": False, "responsive": True},
                        style={"height": "420px", "width": "100%"},
                    ),
                ],
            ),

            html.Div(
                className="trend-graph-mobile",
                children=[
                    dcc.Graph(
                        id="monthly-trend-mobile",
                        figure=empty_bar_figure(),
                        config={"displayModeBar": False, "responsive": True},
                        style={"height": "420px", "width": "100%"},
                    ),
                ],
            ),
        ],
    )

