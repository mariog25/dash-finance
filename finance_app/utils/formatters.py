def mask_digits(text):
    return "".join("*" if ch.isdigit() else ch for ch in str(text))


def format_eur_es(value, masked=False):
    try:
        n = float(value or 0)
    except (TypeError, ValueError):
        n = 0.0

    s = f"{n:,.2f}"
    s = s.replace(",", "§").replace(".", ",").replace("§", ".")
    formatted = f"{s} €"
    return mask_digits(formatted) if masked else formatted


def format_k_es(value, masked=False):
    try:
        n = float(value or 0)
    except (TypeError, ValueError):
        n = 0.0

    s = f"{n/1000:.2f}".replace(".", ",")
    formatted = f"{s}k"
    return mask_digits(formatted) if masked else formatted


def format_pct_es(value, masked=False):
    try:
        n = float(value or 0)
    except (TypeError, ValueError):
        n = 0.0

    s = f"{abs(n):.1f}"
    s = s.replace(".", ",")

    formatted = (
        f"▲{s}%" if n > 0 else
        f"▼{s}%" if n < 0 else
        f"{s}%"
    )

    return mask_digits(formatted) if masked else formatted

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


def format_daily_es(value, masked=False):
    try:
        n = float(value or 0)
    except (TypeError, ValueError):
        n = 0.0

    s = f"{n:,.1f}"
    s = s.replace(",", "§").replace(".", ",").replace("§", ".")
    formatted = f"{s} €/day"
    return mask_digits(formatted) if masked else formatted


