from dash import dcc, html

from components.tax_employee_card import build_tax_card_trend_figure


def build_tax_company_card():
    return html.Div(
        className="insight-card tax-company-card",
        children=[
            html.Div(
                className="insight-card-header",
                children=[
                    html.Div("Company Cost", className="insight-card-title"),
                    html.Div("Salary + IRPF + SS Emp./Corp.", className="insight-card-subtitle"),
                ],
            ),
            html.Div(
                className="insight-card-body",
                children=[
                    html.Div(id="tax-company-current", className="insight-card-value number-tax-company"),
                    html.Div(
                        className="insight-card-metrics",
                        children=[
                            html.Div(
                                className="metric-line",
                                children=[
                                    html.Span("Average 10 years", className="metric-label"),
                                    html.Span(id="tax-company-avg-10y", className="metric-value"),
                                ],
                            ),
                            html.Div(
                                className="metric-line",
                                children=[
                                    html.Span("Average deviation", className="metric-label"),
                                    html.Span(id="tax-company-vs-avg", className="metric-value"),
                                ],
                            ),
                            html.Div(
                                className="metric-line",
                                children=[
                                    html.Span("Salary net total", className="metric-label"),
                                    html.Span(id="tax-company-salary", className="metric-value"),
                                ],
                            ),
                            html.Div(
                                className="metric-line",
                                children=[
                                    html.Span("SS Emp./Corp.", className="metric-label"),
                                    html.Span(id="tax-company-ss", className="metric-value"),
                                ],
                            ),
                            html.Div(
                                className="metric-line",
                                children=[
                                    html.Span("IRPF total", className="metric-label"),
                                    html.Span(id="tax-company-irpf", className="metric-value"),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="tax-company-card-chart-wrap",
                children=[
                    dcc.Graph(
                        id="tax-company-chart",
                        config={"displayModeBar": False, "staticPlot": False, "responsive": True},
                        style={"height": "100%", "width": "100%"},
                    )
                ],
            ),
        ],
    )


def build_tax_company_trend_figure(years, values):
    return build_tax_card_trend_figure(
        years,
        values,
        "rgba(214, 143, 34, 0.85)",
        "rgba(214, 143, 34, 0.16)",
        "|",
        "rgba(214, 143, 34, 0.18)",
        "rgba(214, 143, 34, 0.01)",
    )
