from dash import html

def build_kpi_card(title: str, value_id: str, delta_id: str):
    return html.Div(
        className="kpi-card",
        children=[
            html.Div(title, className="kpi-title"),
            html.Div(id=value_id, className="kpi-value"),
            html.Div(id=delta_id, className="kpi-delta"),
        ],
    )