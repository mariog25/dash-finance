from dash import html, dcc

def build_income_insight_card():
    return html.Div(
        className="insight-card income-insight-card",
        children=[
            html.Div(
                className="insight-card-header",
                children=[
                    html.Div("Monthly income", className="insight-card-title"),
                    html.Div("Year tendency", className="insight-card-subtitle"),
                ],
            ),
            html.Div(
                className="insight-card-body",
                children=[
                    html.Div(id="income-current", className="insight-card-value number-income"),
                    html.Div(
                        className="insight-card-metrics",
                        children=[
                            html.Div(
                                className="metric-line",
                                children=[
                                    html.Span("Average 12 months", className="metric-label"),
                                    html.Span(id="income-avg-12m", className="metric-value"),
                                ],
                            ),
                            html.Div(
                                className="metric-line",
                                children=[
                                    html.Span("Average deviation", className="metric-label"),
                                    html.Span(id="income-vs-avg", className="metric-value"),
                                ],
                            ),
                            html.Div(
                                className="metric-line",
                                children=[
                                    html.Span("Accumulated YTD", className="metric-label"),
                                    html.Span(id="income-ytd", className="metric-value"),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="income-insight-chart-wrap",
                children=[
                    dcc.Graph(
                        id="income-insight-chart",
                        config={"displayModeBar": False, "responsive": True},
                        style={"height": "100%", "width": "100%"},
                        
                    )
                ],
            ),
        ],
    )