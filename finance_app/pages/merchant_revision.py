import dash
from dash import html

dash.register_page(__name__, path="/merchant-revision", name="Merchant Revision")

layout = html.Div(
    className="panel-grid",
    children=[
        html.Div(
            className="panel panel-full-width",
            children=[
                html.H3("Merchant Revision", className="panel-title"),
                html.P("This page will contain merchant normalization review and corrections."),
            ],
        )
    ],
)