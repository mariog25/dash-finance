from dash import html, dcc

def build_mortgage_interest_card():
    return html.Div(
        className="insight-card mortgage-interest-card",
        children=[
            html.Div(
                className="insight-card-header",
                children=[
                    html.Div("Interest Paid", className="insight-card-title"),
                    html.Div("Year Tendency", className="insight-card-subtitle"),
                ],
            ),
            html.Div(
                className="insight-card-body",
                children=[
                    html.Div(id="mortgage-interest-current", className="insight-card-value number-mortgage"),
                    html.Div(
                        className="insight-card-metrics",
                        children=[
                            html.Div(
                                className="metric-line",
                                children=[
                                    html.Span("Average 10 years", className="metric-label"),
                                    html.Span(id="mortgage-interest-avg-10y", className="metric-value"),
                                ],
                            ),
                            html.Div(
                                className="metric-line",
                                children=[
                                    html.Span("Average deviation", className="metric-label"),
                                    html.Span(id="mortgage-interest-vs-avg", className="metric-value"),
                                ],
                            ),
                            html.Div(
                                className="metric-line",
                                children=[
                                    html.Span("Accumulated/Total", className="metric-label"),
                                    html.Span(id="mortgage-interest-accumulated-to-year", className="metric-value"),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="mortgage-interest-chart-wrap",
                children=[
                    dcc.Graph(
                        id="mortgage-interest-insight-chart",
                        config={"displayModeBar": False, "staticPlot": False, "responsive": True},
                        style={"height": "100%", "width": "100%"},
                    )
                ],
            ),
        ],
    )