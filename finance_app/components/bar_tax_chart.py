import pandas as pd
import plotly.graph_objects as go

from config.finance_theme import SEMANTIC
from components.monthly_trend_panel import empty_bar_figure
from utils.formatters import format_eur_es, format_pct_es


def build_tax_breakdown_figure(df: pd.DataFrame, selected_year: int, hidden: bool = False):
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
        [format_eur_es(t, masked=hidden), format_pct_es(p, masked=hidden)]
        for t, p in zip(total_taxes, percent_of_gross)
    ]

    fig = go.Figure()

    def bar_trace(name, values, fill_color, line_color, hover_label=None):
        return go.Bar(
            x=labels,
            y=values,
            name=name,
            customdata=[[format_eur_es(v, masked=hidden)] for v in values],
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

    total_taxes_line_color = "rgba(190, 62, 70, 0.28)"
    total_taxes_marker_color = "rgba(190, 62, 70, 0.38)"
    total_taxes_accent_color = "rgba(190, 62, 70, 1)"

    fig.add_trace(bar_trace("Salary Net", salary_net, salary_fill, salary_line, "Salary net"))
    fig.add_trace(bar_trace("SS Employee", employee_ss, employee_ss_fill, employee_ss_line, "SS Employee"))
    fig.add_trace(bar_trace("IRPF", irpf, irpf_fill, irpf_line, "IRPF"))
    fig.add_trace(bar_trace("IVA Total", iva_total, iva_fill, iva_line, "IVA total"))
    fig.add_trace(bar_trace("Employer SS", employer_ss, employer_ss_fill, employer_ss_line, "Employer SS"))

    selected_index = df.index[df["fiscal_year"] == selected_year].tolist()
    selected_pos = selected_index[0] if selected_index else None

    fig.add_trace(
        go.Scatter(
            x=labels,
            y=total_taxes,
            mode="lines+markers",
            name="Total Taxes",
            yaxis="y2",
            line={"color": total_taxes_line_color, "width": 2.6, "shape": "spline", "smoothing": 0.6},
            marker={
                "size": 8,
                "color": total_taxes_marker_color,
                "line": {"color": "rgba(255,255,255,0.9)", "width": 1.4},
            },
            customdata=customdata_total,
            hoverlabel={
                "bgcolor": "rgba(255,255,255,0.98)",
                "bordercolor": total_taxes_accent_color,
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
            "title": {"text": "Total taxes", "font": {"size": 12, "color": total_taxes_accent_color}},
            "tickfont": {"size": 12, "color": total_taxes_accent_color},
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
