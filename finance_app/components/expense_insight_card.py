from dash import html, dcc

def build_expense_insight_card():
    return html.Div(
        className="expense-insight-card",
        children=[
            html.Div(
                className="expense-insight-content",
                children=[
                    html.Div(
                        className="expense-header-top",
                        children=[
                            html.Div(
                                children=[
                                    html.Div("Monthly spending", className="expense-insight-title"),
                                    html.Div("Year Tendency", className="expense-insight-subtitle"),
                                ]
                            ),
                            html.Div(
                                children=[
                                    html.Div("Burn rate", className="mini-kpi-label"),
                                    html.Div(id="expense-burn-rate", className="mini-kpi-value"),
                                ],
                                className="mini-kpi-chip",
                            ),
                        ],
                    ),
                    html.Div(
                        className="expense-insight-main",
                        children=[
                            html.Div(id="expense-current", className="expense-current-value number-expense"),
                            html.Div(
                                className="expense-secondary-metrics",
                                children=[
                                    html.Div(
                                        className="metric-line",
                                        children=[
                                            html.Span("Average 12 months", className="metric-label"),
                                            html.Span(id="expense-avg-12m", className="metric-value"),
                                        ],
                                    ),
                                    html.Div(
                                        className="metric-line",
                                        children=[
                                            html.Span("Average deviation", className="metric-label"),
                                            html.Span(id="expense-vs-avg", className="metric-value"),
                                        ],
                                    ),
                                    html.Div(
                                        className="metric-line",
                                        children=[
                                            html.Span("Accumulated YTD", className="metric-label"),
                                            html.Span(id="expense-ytd", className="metric-value"),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="expense-insight-chart-wrap",
                children=[
                    dcc.Graph(
                        id="expense-insight-chart",
                        config={"displayModeBar": False, "staticPlot": False, "responsive": True},
                        style={"height": "100%", "width": "100%"},
                       
                    )
                ],
            ),
        ],
    )