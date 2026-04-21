import dash
from dash import html

dash.register_page(__name__, path="/mortgage-revision", name="Mortgage Revision")

layout = html.Div(
    className="panel-grid",
    children=[
        html.Div(
            className="panel panel-full-width",
            children=[
                html.H3("Mortgage Revision", className="panel-title"),
                html.P("This page will contain mortgage review and payment evolution."),
            ],
        )
    ],
)