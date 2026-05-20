import pandas as pd
import dash
from dash import html, dcc, Input, Output, State, ctx

from components.bar_tax_chart import build_tax_breakdown_figure
from components.monthly_trend_panel import empty_bar_figure
from components.tax_company_card import build_tax_company_card, build_tax_company_trend_figure
from components.tax_employee_card import build_tax_employee_card, build_tax_employee_trend_figure
from components.tax_state_card import build_tax_state_card, build_tax_state_trend_figure
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
                build_tax_employee_card(),
                build_tax_state_card(),
                build_tax_company_card(),
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
    employee_figure = build_tax_employee_trend_figure(
        trend_years,
        trend_df["employee_total"].tolist(),
    )

    employer_current, employer_avg, employer_pct = metric_values("employer_burden_total", "Employer burden total")
    employer_class = deviation_class("expense", employer_pct)
    employer_irpf = format_eur_es(selected_row["employee_irpf_total"]) if selected_row is not None else "-"
    employer_employee_ss = format_eur_es(selected_row["employee_ss_total"]) if selected_row is not None else "-"
    employer_employer_ss = format_eur_es(selected_row["employer_ss_total"]) if selected_row is not None else "-"
    employer_figure = build_tax_state_trend_figure(
        trend_years,
        trend_df["employer_burden_total"].tolist(),
    )

    company_current, company_avg, company_pct = metric_values("company_cost_total", "Company cost total")
    company_class = deviation_class("expense", company_pct)
    company_salary = format_eur_es(selected_row["salary_net_total"]) if selected_row is not None else "-"
    company_employee_ss = format_eur_es(selected_row["employee_ss_total"]) if selected_row is not None else "-"
    company_employer_ss = format_eur_es(selected_row["employer_ss_total"]) if selected_row is not None else "-"
    company_irpf = format_eur_es(selected_row["employee_irpf_total"]) if selected_row is not None else "-"
    company_figure = build_tax_company_trend_figure(
        trend_years,
        trend_df["company_cost_total"].tolist(),
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
