import os
from dash import Dash, html, dcc, Input, Output, State, ctx, page_container

from components.header import build_header
from components.sidebar import build_sidebar

app = Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server
app.title = "Finance Dashboard"

app.layout = html.Div(
    className="app-shell",
    children=[
        dcc.Location(id="url"),
        dcc.Store(id="sidebar-open", data={"mobile_open": False, "desktop_expanded": False}),
        dcc.Store(id="global-period-store", storage_type="session", data={}),
        html.Div(
            id="sidebar-wrapper",
            className="sidebar-wrapper",
             children=[
                html.Button(
                    "⟷",
                    id="sidebar-desktop-toggle",
                    className="sidebar-desktop-toggle",
                    n_clicks=0,
                ),
        build_sidebar(),
    ],
        ),
        html.Div(
            className="main-content",
            children=[
                html.Div(
                    className="mobile-topbar",
                    children=[
                        html.Button(
                            "☰",
                            id="sidebar-toggle",
                            className="hamburger-btn",
                            n_clicks=0,
                        ),
                    ],
                ),
                build_header(
                    "Personal Finance Dashboard",
                    "Finance Analytics",
                ),
                page_container,
            ],
        ),
    ],
)

@app.callback(
    Output("sidebar-wrapper", "className"),
    Output("sidebar-open", "data"),
    Input("sidebar-toggle", "n_clicks"),
    Input("sidebar-desktop-toggle", "n_clicks"),
    Input("url", "pathname"),
    State("sidebar-open", "data"),
    prevent_initial_call=False,
)
def toggle_sidebar(mobile_clicks, desktop_clicks, pathname, sidebar_state):
    sidebar_state = sidebar_state or {"mobile_open": False, "desktop_expanded": False}
    trigger = ctx.triggered_id

    mobile_open = bool(sidebar_state.get("mobile_open", False))
    desktop_expanded = bool(sidebar_state.get("desktop_expanded", False))

    if trigger == "sidebar-toggle":
        mobile_open = not mobile_open

    elif trigger == "sidebar-desktop-toggle":
        desktop_expanded = not desktop_expanded

    elif trigger == "url":
        # al navegar, cerramos el menú móvil, pero mantenemos el estado desktop
        mobile_open = False

    class_name = "sidebar-wrapper"
    if mobile_open:
        class_name += " mobile-open"
    if desktop_expanded:
        class_name += " desktop-expanded"

    return class_name, {
        "mobile_open": mobile_open,
        "desktop_expanded": desktop_expanded,
    }


if __name__ == "__main__":
    app.run(
        host=os.getenv("DASH_HOST", "0.0.0.0"),
        port=int(os.getenv("DASH_PORT", "8050")),
        debug=os.getenv("DASH_DEBUG", "true").lower() == "true",
    )