from dash import html, dcc

def build_mortgage_payment_card():
    return html.Div(
        className="insight-card mortgage-payment-card",
        children=[
            html.Div(
                className="insight-card-header",
                children=[
                    html.Div("Mortgage Payment", className="insight-card-title"),
                    html.Div("Year Tendency", className="insight-card-subtitle"),
                ],
            ),
            html.Div(
                className="insight-card-body",
                children=[
                    html.Div(id="mortgage-payment-current", className="insight-card-value number-mortgage"),
                    html.Div(
                        className="insight-card-metrics",
                        children=[
                            html.Div(
                                className="metric-line",
                                children=[
                                    html.Span("Average 10 years", className="metric-label"),
                                    html.Span(id="mortgage-payment-avg-10y", className="metric-value"),
                                ],
                            ),
                            html.Div(
                                className="metric-line",
                                children=[
                                    html.Span("Average deviation", className="metric-label"),
                                    html.Span(id="mortgage-payment-vs-avg", className="metric-value"),
                                ],
                            ),
                            html.Div(
                                className="metric-line",
                                children=[
                                    html.Span("Accumulated/Total", className="metric-label"),
                                    html.Span(id="mortgage-payment-accumulated-to-year", className="metric-value"),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="mortgage-payment-chart-wrap",
                children=[
                    dcc.Graph(
                        id="mortgage-payment-insight-chart",
                        config={"displayModeBar": False, "staticPlot": False, "responsive": True},
                        style={"height": "100%", "width": "100%"},
                    )
                ],
            ),
        ],
    )