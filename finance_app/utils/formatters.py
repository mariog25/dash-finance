def format_eur_es(value):
    try:
        n = float(value or 0)
    except (TypeError, ValueError):
        n = 0.0

    s = f"{n:,.2f}"
    s = s.replace(",", "§").replace(".", ",").replace("§", ".")
    return f"{s} €"

def format_k_es(value):
    try:
        n = float(value or 0)
    except (TypeError, ValueError):
        n = 0.0

    s = f"{n/1000:.2f}".replace(".", ",")
    return f"{s}k"


def format_pct_es(value):
    try:
        n = float(value or 0)
    except (TypeError, ValueError):
        n = 0.0

    s = f"{abs(n):.1f}"
    s = s.replace(".", ",")

    if n > 0:
        return f"▲{s}%"
    elif n < 0:
        return f"▼{s}%"
         
    return f"{s}%"

def deviation_class(metric_type: str, value: float) -> str:
    try:
        v = float(value or 0)
    except (TypeError, ValueError):
        v = 0.0

    if metric_type == "expense":
        return "metric-value metric-good" if v < 0 else "metric-value metric-bad" if v > 0 else "metric-value metric-neutral"

    if metric_type in ("income", "savings"):
        return "metric-value metric-good" if v > 0 else "metric-value metric-bad" if v < 0 else "metric-value metric-neutral"

    return "metric-value metric-neutral"


def format_daily_es(value):
    try:
        n = float(value or 0)
    except (TypeError, ValueError):
        n = 0.0

    s = f"{n:,.1f}"
    s = s.replace(",", "§").replace(".", ",").replace("§", ".")
   
    return f"{s} €/day"


