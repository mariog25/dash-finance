from dash import html, dcc

def build_category_donut_card(donut_id: str, trend_id: str, title: str):
    return html.Div(
        className="panel category-donut-card",
        children=[
            html.Div(
                className="category-donut-header",
                children=[
                    html.H3(title, className="panel-title"),
                ],
            ),
            dcc.Graph(
                id=donut_id,
                clear_on_unhover=True,
                config={"displayModeBar": False, "responsive": True},
                style={"height": "300px", "width": "100%"},
            ),
            html.Div(
                className="category-trend-wrap",
                children=[
                    dcc.Graph(
                        id=trend_id,
                        clear_on_unhover=True,
                        config={"displayModeBar": False, "responsive": True},
                        style={"height": "90px", "width": "100%"},
                    )
                ],
            ),
        ],
    )