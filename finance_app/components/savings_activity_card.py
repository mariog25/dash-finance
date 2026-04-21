from dash import html, dcc

def build_savings_activity_card():
    return html.Div(
        className="insight-card savings-activity-card",
        children=[
            html.Div(
                className="insight-card-header",
                children=[
                    html.Div("Monthly savings", className="insight-card-title"),
                    html.Div("Year tendency", className="insight-card-subtitle"),
                ],
            ),
            html.Div(
                className="insight-card-body",
                children=[
                    html.Div(id="savings-current", className="insight-card-value number-savings"),
                    html.Div(
                        className="insight-card-metrics",
                        children=[
                            html.Div(
                                className="metric-line",
                                children=[
                                    html.Span("Average 12 months", className="metric-label"),
                                    html.Span(id="savings-avg-12m", className="metric-value"),
                                ],
                            ),
                            html.Div(
                                className="metric-line",
                                children=[
                                    html.Span("Average deviation", className="metric-label"),
                                    html.Span(id="savings-vs-avg", className="metric-value"),
                                ],
                            ),
                            html.Div(
                                className="metric-line",
                                children=[
                                    html.Span("Accumulated YTD", className="metric-label"),
                                    html.Span(id="savings-ytd", className="metric-value"),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="savings-insight-chart-wrap",
                children=[
                    dcc.Graph(
                        id="savings-insight-chart",
                        config={"displayModeBar": False, "responsive": True},
                        style={"height": "100%", "width": "100%"},
                       
                    )
                ],
            ),
        ],
    )