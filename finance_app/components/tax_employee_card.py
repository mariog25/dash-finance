from dash import dcc, html

from utils.formatters import format_eur_es


def build_tax_employee_card():
    return html.Div(
        className="insight-card tax-employee-card",
        children=[
            html.Div(
                className="insight-card-header",
                children=[
                    html.Div("Employee Tax Burden", className="insight-card-title"),
                    html.Div("IRPF + Employee SS total", className="insight-card-subtitle"),
                ],
            ),
            html.Div(
                className="insight-card-body",
                children=[
                    html.Div(id="tax-employee-current", className="insight-card-value number-tax-employee"),
                    html.Div(
                        className="insight-card-metrics",
                        children=[
                            html.Div(
                                className="metric-line",
                                children=[
                                    html.Span("Average 10 years", className="metric-label"),
                                    html.Span(id="tax-employee-avg-10y", className="metric-value"),
                                ],
                            ),
                            html.Div(
                                className="metric-line",
                                children=[
                                    html.Span("Average deviation", className="metric-label"),
                                    html.Span(id="tax-employee-vs-avg", className="metric-value"),
                                ],
                            ),
                            html.Div(
                                className="metric-line",
                                children=[
                                    html.Span("IRPF total", className="metric-label"),
                                    html.Span(id="tax-employee-irpf", className="metric-value"),
                                ],
                            ),
                            html.Div(
                                className="metric-line",
                                children=[
                                    html.Span("Employee SS total", className="metric-label"),
                                    html.Span(id="tax-employee-ss", className="metric-value"),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="tax-employee-card-chart-wrap",
                children=[
                    dcc.Graph(
                        id="tax-employee-chart",
                        config={"displayModeBar": False, "staticPlot": False, "responsive": True},
                        style={"height": "100%", "width": "100%"},
                    )
                ],
            ),
        ],
    )


def build_tax_employee_trend_figure(years, values):
    return build_tax_card_trend_figure(
        years,
        values,
        "rgba(190, 62, 70, 0.85)",
        "rgba(190, 62, 70, 0.16)",
        "/",
        "rgba(190, 62, 70, 0.12)",
        "rgba(190, 62, 70, 0.01)",
    )


def build_tax_card_trend_figure(
    years,
    values,
    line_color,
    fill_color,
    fillpattern_shape=None,
    fillpattern_fg=None,
    fillpattern_bg=None,
):
    if not years or not values:
        return {"data": [], "layout": {}}

    return {
        "data": [
            {
                "x": years,
                "y": values,
                "customdata": [format_eur_es(v) for v in values],
                "type": "scatter",
                "mode": "lines",
                "fill": "tozeroy",
                "line": {
                    "color": line_color,
                    "width": 1.6,
                    "shape": "spline",
                    "smoothing": 0.8,
                },
                "fillcolor": fill_color,
                "hovertemplate": (
                    "<b>%{x}</b><br>"
                    "%{customdata} €"
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
            "margin": {"l": 20, "r": 20, "t": 20, "b": 26},
            "xaxis": {
                "showgrid": False,
                "showticklabels": False,
                "zeroline": False,
                "showline": False,
                "fixedrange": True,
            },
            "yaxis": {
                "showgrid": False,
                "showticklabels": False,
                "zeroline": False,
                "showline": False,
                "fixedrange": True,
                "tickformat": ",.0f",
            },
            "showlegend": False,
            "hovermode": "closest",
        },
    }
