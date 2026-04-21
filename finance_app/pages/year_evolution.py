import dash
from dash import html

dash.register_page(__name__, path="/year-evolution", name="Year Evolution")

layout = html.Div(
    className="panel-grid",
    children=[
        html.Div(
            className="panel panel-full-width",
            children=[
                html.H3("Year Evolution", className="panel-title"),
                html.P("This page will contain yearly trends and multi-year comparisons."),
            ],
        )
    ],
)