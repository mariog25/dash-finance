from dash import html

def build_header(title: str, subtitle: str):
    return html.Div(
        className="page-header",
        children=[
            html.Div(
                children=[
                    html.H1(title, className="page-title"),
                    html.P(subtitle, className="page-subtitle"),
                ]
            )
        ],
    )