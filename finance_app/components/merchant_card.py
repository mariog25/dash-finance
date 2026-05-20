from dash import html, dcc

def build_merchant_summary_card():
    return html.Div(
        className="merchant-summary-card",
        children=[
            html.Div(
                className="merchant-summary-content",
                children=[
                    html.Div(
                        className="merchant-header",
                        children=[
                            html.Div(
                                children=[
                                    html.Div("Merchant Analysis", className="merchant-summary-title"),
                                    html.Div(id="merchant-summary-subtitle", className="merchant-summary-subtitle"),
                                ]
                            ),
                        ],
                    ),
                    html.Div(
                        className="merchant-summary-main",
                        children=[
                            html.Div(id="merchant-current-value", className="merchant-current-value number-expense"),
                            html.Div(
                                className="merchant-secondary-metrics",
                                children=[
                                    html.Div(
                                        className="metric-line",
                                        children=[
                                            html.Span("Average 12 months", className="metric-label"),
                                            html.Span(id="merchant-avg-12m", className="metric-value"),
                                        ],
                                    ),
                                    html.Div(
                                        className="metric-line",
                                        children=[
                                            html.Span("Average deviation", className="metric-label"),
                                            html.Span(id="merchant-vs-avg", className="metric-value"),
                                        ],
                                    ),
                                    html.Div(
                                        className="metric-line",
                                        children=[
                                            html.Span("Accumulated 12 months", className="metric-label"),
                                            html.Span(id="merchant-accumulated-12m", className="metric-value"),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="merchant-summary-chart-wrap",
                children=[
                    dcc.Graph(
                        id="merchant-trend-chart",
                        config={"displayModeBar": False, "staticPlot": False, "responsive": True},
                        style={"height": "100%", "width": "100%"},
                    )
                ],
            ),
        ],
    )
