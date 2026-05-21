from dash import dcc, html

from components.tax_employee_card import build_tax_card_trend_figure


def build_tax_state_card():
    return html.Div(
        className="insight-card tax-employer-card",
        children=[
            html.Div(
                className="insight-card-header",
                children=[
                    html.Div("State Benefit", className="insight-card-title"),
                    html.Div("SS Emp./Corp. + IRPF", className="insight-card-subtitle"),
                ],
            ),
            html.Div(
                className="insight-card-body",
                children=[
                    html.Div(id="tax-employer-current", className="insight-card-value number-tax-employer"),
                    html.Div(
                        className="insight-card-metrics",
                        children=[
                            html.Div(
                                className="metric-line",
                                children=[
                                    html.Span("Average 10 years", className="metric-label"),
                                    html.Span(id="tax-employer-avg-10y", className="metric-value"),
                                ],
                            ),
                            html.Div(
                                className="metric-line",
                                children=[
                                    html.Span("Average deviation", className="metric-label"),
                                    html.Span(id="tax-employer-vs-avg", className="metric-value"),
                                ],
                            ),
                            html.Div(
                                className="metric-line",
                                children=[
                                    html.Span("IRPF total", className="metric-label"),
                                    html.Span(id="tax-employer-irpf", className="metric-value"),
                                ],
                            ),
                            html.Div(
                                className="metric-line",
                                children=[
                                    html.Span("SS Emp./Corp.", className="metric-label"),
                                    html.Span(id="tax-employer-ss", className="metric-value"),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="tax-employer-card-chart-wrap",
                children=[
                    dcc.Graph(
                        id="tax-employer-chart",
                        config={"displayModeBar": False, "staticPlot": False, "responsive": True},
                        style={"height": "100%", "width": "100%"},
                    )
                ],
            ),
        ],
    )


def build_tax_state_trend_figure(years, values, hidden: bool = False):
    return build_tax_card_trend_figure(
        years,
        values,
        "rgba(25, 115, 184, 0.85)",
        "rgba(25, 115, 184, 0.16)",
        "\\",
        "rgba(25, 115, 184, 0.12)",
        "rgba(25, 115, 184, 0.01)",
        hidden=hidden,
    )
