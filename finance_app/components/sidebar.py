from dash import html, dcc


def nav_item(label: str, icon: str, href: str):
    return dcc.Link(
        href=href,
        className="sidebar-link",
        children=[
            html.Div(
                className="sidebar-item",
                **{"data-label": label},
                children=[
                    html.Span(icon, className="sidebar-item-icon"),
                    html.Span(label, className="sidebar-item-text"),
                ],
            )
        ],
    )

def build_sidebar():
    return html.Div(
        className="sidebar",
        children=[
            html.Div("DL", className="sidebar-logo"),
            html.H2("Finance", className="sidebar-title"),
            html.Div(
                className="sidebar-menu",
                children=[
                    nav_item("Monthly Overview", "⌂", "/"),
                    nav_item("Detailed Operations", "↔", "/transactions"),
                    nav_item("Merchant Revision", "◫", "/merchant-revision"),
                    nav_item("Year Evolution", "⊕", "/year-evolution"),
                    nav_item("Mortgage Revision", "↻", "/mortgage-revision"),
                ],
            ),
        ],
    )