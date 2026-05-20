import pandas as pd
import dash
from dash import html, dcc, Input, Output, State, ctx
import plotly.graph_objects as go

from config.finance_theme import SEMANTIC
from components.monthly_trend_panel import empty_bar_figure
from services.finance_queries import (
    get_tax_available_years,
    get_tax_payments_trend,
    insert_tax_payment,
)
from utils.formatters import format_eur_es, format_pct_es, deviation_class


dash.register_page(__name__, path="/tax-review", name="Tax Review")

years = get_tax_available_years()
year_options = [
    {"label": str(y), "value": str(y)}
    for y in sorted(years, reverse=True)
]
default_year = year_options[0]["value"] if year_options else str(pd.Timestamp.now().year)

def build_filter_row():
    return html.Div(
        className="filters-row",
        children=[
            html.Div("Fiscal Year", className="filter-group-label"),
            dcc.Dropdown(
                id="tax-filter-year",
                options=year_options,
                value=year_options[0]["value"] if year_options else None,
                clearable=False,
                className="filter-year",
            ),
            html.Button(
                "+",
                id="tax-add-button",
                className="primary-button",
                n_clicks=0,
                style={"minWidth": "48px", "minHeight": "48px", "fontSize": "22px"},
            ),
        ],
    )


def build_tax_summary_card(
    card_class: str,
    title: str,
    subtitle: str,
    current_id: str,
    avg_id: str,
    vs_id: str,
    metric_lines: list[tuple[str, str]],
    chart_id: str,
    number_class: str,
):
    return html.Div(
        className=f"insight-card {card_class}",
        children=[
            html.Div(
                className="insight-card-header",
                children=[
                    html.Div(title, className="insight-card-title"),
                    html.Div(subtitle, className="insight-card-subtitle"),
                ],
            ),
            html.Div(
                className="insight-card-body",
                children=[
                    html.Div(id=current_id, className=f"insight-card-value {number_class}"),
                    html.Div(
                        className="insight-card-metrics",
                        children=[
                            html.Div(
                                className="metric-line",
                                children=[
                                    html.Span("Average 10 years", className="metric-label"),
                                    html.Span(id=avg_id, className="metric-value"),
                                ],
                            ),
                            html.Div(
                                className="metric-line",
                                children=[
                                    html.Span("Average deviation", className="metric-label"),
                                    html.Span(id=vs_id, className="metric-value"),
                                ],
                            ),
                        ]
                        + [
                            html.Div(
                                className="metric-line",
                                children=[
                                    html.Span(label, className="metric-label"),
                                    html.Span(id=value_id, className="metric-value"),
                                ],
                            )
                            for label, value_id in metric_lines
                        ],
                    ),
                ],
            ),
            html.Div(
                className=f"{card_class}-chart-wrap",
                children=[
                    dcc.Graph(
                        id=chart_id,
                        config={"displayModeBar": False, "staticPlot": False, "responsive": True},
                        style={"height": "100%", "width": "100%"},
                    )
                ],
            ),
        ],
    )


def build_tax_breakdown_figure(df: pd.DataFrame, selected_year: int):
    if df.empty:
        return empty_bar_figure("No tax breakdown data available")

    labels = df["fiscal_year"].astype(str).tolist()
    salary_net = df["salary_net_total"].tolist()
    employee_ss = df["employee_ss_total"].tolist()
    irpf = df["employee_irpf_total"].tolist()
    iva_total = df["indirect_tax_total"].tolist()
    employer_ss = df["employer_ss_total"].tolist()

    total_taxes = [
        e + i + v + s
        for e, i, v, s in zip(employee_ss, irpf, iva_total, employer_ss)
    ]
    gross_salary = [
        s + e + i
        for s, e, i in zip(salary_net, employee_ss, irpf)
    ]
    percent_of_gross = [
        (t / g * 100.0) if g else 0.0
        for t, g in zip(total_taxes, gross_salary)
    ]
    customdata_total = [
        [format_eur_es(t), format_pct_es(p)]
        for t, p in zip(total_taxes, percent_of_gross)
    ]

    fig = go.Figure()

    def bar_trace(name, values, fill_color, line_color, pattern_shape=None, hover_label=None):
        return go.Bar(
            x=labels,
            y=values,
            name=name,
            customdata=[[format_eur_es(v)] for v in values],
            cliponaxis=False,
            width=0.5,
            marker={
                "color": fill_color,
                "line": {"color": fill_color, "width": 0},
                "cornerradius": "12%",
            },
            hoverlabel={
                "bgcolor": "rgba(255,255,255,0.98)",
                "bordercolor": line_color,
            },
            hovertemplate=(
                "<b>%{x}</b><br>"
                f"{hover_label}: %{{customdata[0]}}<extra></extra>"
            ) if hover_label else None,
        )

    # Define a clear, flat color palette with enough opacity to keep stacked bars legible.
    salary_fill = "rgba(25, 115, 184, 0.28)"
    salary_line = SEMANTIC["income"]["line"]

    employee_ss_fill = "rgba(190, 62, 70, 0.28)"
    employee_ss_line = SEMANTIC["expense"]["line"]

    irpf_fill = "rgba(214, 143, 34, 0.26)"
    irpf_line = SEMANTIC["savings"]["line"]

    iva_fill = "rgba(123, 136, 160, 0.24)"
    iva_line = "rgba(123, 136, 160, 0.7)"

    employer_ss_fill = "rgba(7, 33, 70, 0.28)"
    employer_ss_line = SEMANTIC["net"]["line"]

    total_taxes_color = "rgba(190, 62, 70, 0.28)"

    fig.add_trace(bar_trace("Salary Net", salary_net, salary_fill, salary_line, None, "Salary net"))
    fig.add_trace(bar_trace("SS Employee", employee_ss, employee_ss_fill, employee_ss_line, None, "SS Employee"))
    fig.add_trace(bar_trace("IRPF", irpf, irpf_fill, irpf_line, None, "IRPF"))
    fig.add_trace(bar_trace("IVA Total", iva_total, iva_fill, iva_line, None, "IVA total"))
    fig.add_trace(bar_trace("Employer SS", employer_ss, employer_ss_fill, employer_ss_line, None, "Employer SS"))

    selected_index = df.index[df["fiscal_year"] == selected_year].tolist()
    selected_pos = selected_index[0] if selected_index else None

    fig.add_trace(
        go.Scatter(
            x=labels,
            y=total_taxes,
            mode="lines+markers",
            name="Total Taxes",
            yaxis="y2",
            line={"color": total_taxes_color, "width": 2.6, "shape": "spline", "smoothing": 0.6},
            marker={
                "size": 8,
                "color": total_taxes_color,
                "line": {"color": "rgba(255,255,255,0.9)", "width": 1.4},
            },
            customdata=customdata_total,
            hoverlabel={
                "bgcolor": "rgba(255,255,255,0.98)",
                "bordercolor": total_taxes_color,
            },
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Total taxes: %{customdata[0]}<br>"
                "%{customdata[1]} of gross salary<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        paper_bgcolor="rgba(255,255,255,1)",
        plot_bgcolor="rgba(255,255,255,1)",
        margin={"l": 56, "r": 60, "t": 28, "b": 50},
        hovermode="closest",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0.0,
            "font": {"size": 9, "color": "#4a5a6a"},
        },
        xaxis={
            "showgrid": False,
            "tickfont": {"size": 12, "color": "#4a5a6a"},
            "fixedrange": True,
        },
        yaxis={
            "title": {"text": "Amounts", "font": {"size": 12, "color": "#7b8a9a"}},
            "tickfont": {"size": 12, "color": "#4a5a6a"},
            "gridcolor": "rgba(7,33,70,0.06)",
            "zerolinecolor": "rgba(7,33,70,0.14)",
            "fixedrange": True,
        },
        yaxis2={
            "title": {"text": "Total taxes", "font": {"size": 12, "color": total_taxes_color}},
            "tickfont": {"size": 12, "color": total_taxes_color},
            "overlaying": "y",
            "side": "right",
            "showgrid": False,
            "fixedrange": True,
        },
        barmode="stack",
        bargap=0.26,
        bargroupgap=0.14,
        barcornerradius="24%",
        transition={"duration": 350, "easing": "cubic-in-out"},
        shapes=(
            [
                {
                    "type": "rect",
                    "xref": "x",
                    "yref": "paper",
                    "x0": max(selected_pos - 0.46, -0.5),
                    "x1": min(selected_pos + 0.46, len(df) - 0.5),
                    "y0": 0,
                    "y1": 1,
                    "fillcolor": "rgba(25,115,184,0.04)",
                    "line": {"width": 0},
                    "layer": "below",
                }
            ] if selected_pos is not None else []
        ),
    )

    return fig


layout = html.Div(
    children=[
        html.Div(
            className="page-header",
            children=[
                html.H1("Tax Review", className="page-title"),
                html.P(
                    "Register manual tax payment entries and review long-term fiscal trends.",
                    className="page-subtitle",
                ),
            ],
        ),
        build_filter_row(),
        html.Div(id="tax-review-status", className="form-status"),
        html.Div(
            className="top-summary-grid",
            children=[
                build_tax_summary_card(
                    card_class="tax-employee-card",
                    title="Employee Tax Burden",
                    subtitle="IRPF + Employee SS total",
                    current_id="tax-employee-current",
                    avg_id="tax-employee-avg-10y",
                    vs_id="tax-employee-vs-avg",
                    metric_lines=[
                        ("IRPF total", "tax-employee-irpf"),
                        ("Employee SS total", "tax-employee-ss"),
                    ],
                    chart_id="tax-employee-chart",
                    number_class="number-tax-employee",
                ),
                build_tax_summary_card(
                    card_class="tax-employer-card",
                    title="State Benefit",
                    subtitle="SS Emp./Corp. + IRPF",
                    current_id="tax-employer-current",
                    avg_id="tax-employer-avg-10y",
                    vs_id="tax-employer-vs-avg",
                    metric_lines=[
                        ("IRPF total", "tax-employer-irpf"),
                        ("SS Emp./Corp.", "tax-employer-ss"),
                    ],
                    chart_id="tax-employer-chart",
                    number_class="number-tax-employer",
                ),
                build_tax_summary_card(
                    card_class="tax-company-card",
                    title="Company Cost",
                    subtitle="Salary + IRPF + SS Emp./Corp.",
                    current_id="tax-company-current",
                    avg_id="tax-company-avg-10y",
                    vs_id="tax-company-vs-avg",
                    metric_lines=[
                        ("Salary net total", "tax-company-salary"),
                        ("SS Emp./Corp.", "tax-company-ss"),
                        ("IRPF total", "tax-company-irpf"),
                    ],
                    chart_id="tax-company-chart",
                    number_class="number-tax-company",
                ),
            ],
        ),
        html.Div(
            className="panel panel-large panel-full-width",
            children=[
                html.H3("Tax Component Breakdown (Last 10 Years)", className="panel-title"),
                dcc.Graph(
                    id="tax-yearly-breakdown-chart",
                    figure=empty_bar_figure(),
                    config={"displayModeBar": False, "responsive": True},
                    style={"height": "420px", "width": "100%"},
                ),
            ],
        ),
        html.Div(
            id="tax-modal-overlay",
            className="modal-overlay",
            style={"display": "none"},
            children=[
                html.Div(
                    className="modal-card",
                    children=[
                        html.Div("Add Tax Payment", className="modal-title"),
                        html.Div(
                            className="modal-fields",
                            children=[
                                html.Div(
                                    className="modal-field",
                                    children=[
                                        html.Label("Fiscal Year", htmlFor="tax-year-input"),
                                        dcc.Input(
                                            id="tax-year-input",
                                            type="number",
                                            min=1900,
                                            max=2100,
                                            value=int(default_year) if default_year else None,
                                            className="form-input",
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="modal-field",
                                    children=[
                                        html.Label("Total IRPF Declared", htmlFor="tax-irpf-input"),
                                        dcc.Input(
                                            id="tax-irpf-input",
                                            type="number",
                                            min=0,
                                            step=0.01,
                                            placeholder="0.00",
                                            className="form-input",
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="modal-field",
                                    children=[
                                        html.Label("Employee Social Security", htmlFor="tax-employee-ss-input"),
                                        dcc.Input(
                                            id="tax-employee-ss-input",
                                            type="number",
                                            min=0,
                                            step=0.01,
                                            placeholder="0.00",
                                            className="form-input",
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="modal-field",
                                    children=[
                                        html.Label("Employer Social Security", htmlFor="tax-employer-ss-input"),
                                        dcc.Input(
                                            id="tax-employer-ss-input",
                                            type="number",
                                            min=0,
                                            step=0.01,
                                            placeholder="0.00",
                                            className="form-input",
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="modal-field",
                                    children=[
                                        html.Label("Notes", htmlFor="tax-notes-textarea"),
                                        dcc.Textarea(
                                            id="tax-notes-textarea",
                                            placeholder="Add notes or context for this payment...",
                                            className="form-textarea",
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        html.Div(
                            className="modal-actions",
                            children=[
                                html.Button(
                                    "Cancel",
                                    id="tax-cancel-button",
                                    className="secondary-button",
                                    n_clicks=0,
                                ),
                                html.Button(
                                    "Save",
                                    id="tax-save-button",
                                    className="primary-button",
                                    n_clicks=0,
                                ),
                            ],
                        ),
                    ],
                )
            ],
        ),
    ]
)




@dash.callback(
    Output("tax-review-status", "children"),
    Output("tax-modal-overlay", "style"),
    Output("tax-year-input", "value"),
    Output("tax-irpf-input", "value"),
    Output("tax-employee-ss-input", "value"),
    Output("tax-employer-ss-input", "value"),
    Output("tax-notes-textarea", "value"),
    Input("tax-add-button", "n_clicks"),
    Input("tax-cancel-button", "n_clicks"),
    Input("tax-save-button", "n_clicks"),
    State("tax-filter-year", "value"),
    State("tax-year-input", "value"),
    State("tax-irpf-input", "value"),
    State("tax-employee-ss-input", "value"),
    State("tax-employer-ss-input", "value"),
    State("tax-notes-textarea", "value"),
    prevent_initial_call=True,
)
def handle_tax_modal(add_clicks, cancel_clicks, save_clicks, filter_year, year_value, irpf, employee_ss, employer_ss, notes):
    triggered = ctx.triggered_id

    if triggered == "tax-add-button":
        return (
            None,
            {"display": "flex"},
            filter_year,
            irpf,
            employee_ss,
            employer_ss,
            notes,
        )

    if triggered == "tax-cancel-button":
        return (
            None,
            {"display": "none"},
            year_value,
            irpf,
            employee_ss,
            employer_ss,
            notes,
        )

    if triggered == "tax-save-button":
        if year_value is None or irpf is None or employee_ss is None or employer_ss is None:
            return (
                html.Div(
                    "Please complete all required fields before saving.",
                    className="form-status-error",
                ),
                {"display": "flex"},
                year_value,
                irpf,
                employee_ss,
                employer_ss,
                notes,
            )

        try:
            insert_tax_payment(
                fiscal_year=int(year_value),
                employee_irpf_amount=float(irpf),
                employee_social_security_amount=float(employee_ss),
                employer_social_security_amount=float(employer_ss),
                notes=notes or "",
            )
            return (
                html.Div(
                    "Tax payment record saved successfully.",
                    className="form-status-success",
                ),
                {"display": "none"},
                year_value,
                None,
                None,
                None,
                "",
            )
        except Exception as exc:
            return (
                html.Div(
                    f"Error saving tax payment: {exc}",
                    className="form-status-error",
                ),
                {"display": "flex"},
                year_value,
                irpf,
                employee_ss,
                employer_ss,
                notes,
            )

    return (None, {"display": "none"}, year_value, irpf, employee_ss, employer_ss, notes)


@dash.callback(
    Output("tax-employee-current", "children"),
    Output("tax-employee-avg-10y", "children"),
    Output("tax-employee-vs-avg", "children"),
    Output("tax-employee-vs-avg", "className"),
    Output("tax-employee-irpf", "children"),
    Output("tax-employee-ss", "children"),
    Output("tax-employee-chart", "figure"),

    Output("tax-employer-current", "children"),
    Output("tax-employer-avg-10y", "children"),
    Output("tax-employer-vs-avg", "children"),
    Output("tax-employer-vs-avg", "className"),
    Output("tax-employer-irpf", "children"),
    Output("tax-employer-ss", "children"),
    Output("tax-employer-chart", "figure"),

    Output("tax-company-current", "children"),
    Output("tax-company-avg-10y", "children"),
    Output("tax-company-vs-avg", "children"),
    Output("tax-company-vs-avg", "className"),
    Output("tax-company-salary", "children"),
    Output("tax-company-ss", "children"),
    Output("tax-company-irpf", "children"),
    Output("tax-company-chart", "figure"),
    Output("tax-yearly-breakdown-chart", "figure"),
    Input("tax-filter-year", "value"),
)
def update_tax_dashboard(selected_year):
    def empty_figure():
        return {"data": [], "layout": {}}

    if not selected_year:
        empty = empty_figure()
        return (
            "-", "-", "-", "metric-value metric-neutral", "-", "-", empty,
            "-", "-", "-", "metric-value metric-neutral", "-", "-", "-", empty,
            "-", "-", "-", "metric-value metric-neutral", "-", "-", "-", "-", empty,
            empty,
        )

    year_int = int(selected_year)
    trend_df = get_tax_payments_trend(year_int, years_back=10)
    selected = trend_df[trend_df["fiscal_year"] == year_int]
    selected_row = selected.iloc[0] if not selected.empty else None
    previous_years = trend_df[trend_df["fiscal_year"] < year_int]

    def build_trend_figure(
        years,
        values,
        line_color,
        fill_color,
        fillpattern_shape=None,
        fillpattern_fg=None,
        fillpattern_bg=None,
    ):
        if not years or not values:
            return empty_figure()

        return {
            "data": [
                {
                    "x": years,
                    "y": values,
                    "customdata": [format_eur_es(v) for v in values],
                    "type": "scatter",
                    "mode": "lines",
                    "fill": "tozeroy",
                    "line": {
                        "color": line_color,
                        "width": 1.6,
                        "shape": "spline",
                        "smoothing": 0.8,
                    },
                    "fillcolor": fill_color,
                    "hovertemplate": (
                        "<b>%{x}</b><br>"
                        "%{customdata} €"
                        "<extra></extra>"
                    ),
                    "fillpattern": {
                        "shape": fillpattern_shape,
                        "size": 6,
                        "solidity": 0.2,
                        "fgcolor": fillpattern_fg,
                        "bgcolor": fillpattern_bg,
                    } if fillpattern_shape else None,
                }
            ],
            "layout": {
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "margin": {"l": 20, "r": 20, "t": 20, "b": 26},
                "xaxis": {
                    "showgrid": False,
                    "showticklabels": False,
                    "zeroline": False,
                    "showline": False,
                    "fixedrange": True,
                },
                "yaxis": {
                    "showgrid": False,
                    "showticklabels": False,
                    "zeroline": False,
                    "showline": False,
                    "fixedrange": True,
                    "tickformat": ",.0f",
                },
                "showlegend": False,
                "hovermode": "closest",
            },
        }

    trend_years = trend_df["fiscal_year"].tolist()

    def metric_values(metric_key, label):
        if selected_row is None:
            return "-", 0.0, 0.0
        current = float(selected_row.get(metric_key, 0.0) or 0.0)
        prev_avg = float(previous_years[metric_key].mean()) if not previous_years.empty else 0.0
        pct = ((current - prev_avg) / prev_avg) * 100.0 if prev_avg else 0.0
        return format_eur_es(current), prev_avg, pct

    employee_current, employee_avg, employee_pct = metric_values("employee_total", "Employee total")
    employee_class = deviation_class("expense", employee_pct)
    employee_irpf = format_eur_es(selected_row["employee_irpf_total"]) if selected_row is not None else "-"
    employee_ss = format_eur_es(selected_row["employee_ss_total"]) if selected_row is not None else "-"
    employee_figure = build_trend_figure(
        trend_years,
        trend_df["employee_total"].tolist(),
        "rgba(190, 62, 70, 0.85)",
        "rgba(190, 62, 70, 0.16)",
        "/",
        "rgba(190, 62, 70, 0.12)",
        "rgba(190, 62, 70, 0.01)",
    )

    employer_current, employer_avg, employer_pct = metric_values("employer_burden_total", "Employer burden total")
    employer_class = deviation_class("expense", employer_pct)
    employer_irpf = format_eur_es(selected_row["employee_irpf_total"]) if selected_row is not None else "-"
    employer_employee_ss = format_eur_es(selected_row["employee_ss_total"]) if selected_row is not None else "-"
    employer_employer_ss = format_eur_es(selected_row["employer_ss_total"]) if selected_row is not None else "-"
    employer_figure = build_trend_figure(
        trend_years,
        trend_df["employer_burden_total"].tolist(),
        "rgba(25, 115, 184, 0.85)",
        "rgba(25, 115, 184, 0.16)",
        "\\",
        "rgba(25, 115, 184, 0.12)",
        "rgba(25, 115, 184, 0.01)",
    )

    company_current, company_avg, company_pct = metric_values("company_cost_total", "Company cost total")
    company_class = deviation_class("expense", company_pct)
    company_salary = format_eur_es(selected_row["salary_net_total"]) if selected_row is not None else "-"
    company_employee_ss = format_eur_es(selected_row["employee_ss_total"]) if selected_row is not None else "-"
    company_employer_ss = format_eur_es(selected_row["employer_ss_total"]) if selected_row is not None else "-"
    company_irpf = format_eur_es(selected_row["employee_irpf_total"]) if selected_row is not None else "-"
    company_figure = build_trend_figure(
        trend_years,
        trend_df["company_cost_total"].tolist(),
        "rgba(214, 143, 34, 0.85)",
        "rgba(214, 143, 34, 0.16)",
        "|",
        "rgba(214, 143, 34, 0.18)",
        "rgba(214, 143, 34, 0.01)",
    )

    breakdown_figure = build_tax_breakdown_figure(trend_df, year_int)

    return (
        employee_current,
        format_eur_es(employee_avg),
        format_pct_es(employee_pct),
        employee_class,
        employee_irpf,
        employee_ss,
        employee_figure,

        employer_current,
        format_eur_es(employer_avg),
        format_pct_es(employer_pct),
        employer_class,
        employer_irpf,
        f"{employer_employee_ss} / {employer_employer_ss}",
        employer_figure,

        company_current,
        format_eur_es(company_avg),
        format_pct_es(company_pct),
        company_class,
        company_salary,
        f"{company_employee_ss} / {company_employer_ss}",
        company_irpf,
        company_figure,
        breakdown_figure,
    )
