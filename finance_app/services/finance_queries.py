import pandas as pd
from services.trino_client import get_engine


def get_available_months():
    engine = get_engine()

    query = """
    SELECT DISTINCT date_trunc('month', txn_date) AS month
    FROM iceberg.gold.fact_bank_transaction
    WHERE txn_date IS NOT NULL
    ORDER BY month DESC
    """

    return pd.read_sql(query, engine)


def get_kpis_by_month(month: str):
    engine = get_engine()

    query = f"""
    SELECT
        SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) AS total_income,
        SUM(CASE WHEN amount < 0 THEN abs(amount) ELSE 0 END) AS total_expense,
        COUNT(*) AS total_txn
    FROM iceberg.gold.fact_bank_transaction
    WHERE date_trunc('month', txn_date) = DATE '{month}'
    """

    df = pd.read_sql(query, engine)

    if df.empty:
        return {"income": 0, "expense": 0, "txn": 0, "savings": 0}

    income = float(df["total_income"].iloc[0] or 0)
    expense = float(df["total_expense"].iloc[0] or 0)
    txn = int(df["total_txn"].iloc[0] or 0)

    return {
        "income": income,
        "expense": expense,
        "txn": txn,
        "savings": income - expense,
    }


def get_daily_expense(month: str):
    engine = get_engine()

    query = f"""
    SELECT
        txn_date,
        SUM(CASE WHEN amount < 0 THEN abs(amount) ELSE 0 END) AS total
    FROM iceberg.gold.fact_bank_transaction
    WHERE date_trunc('month', txn_date) = DATE '{month}'
    GROUP BY txn_date
    ORDER BY txn_date
    """

    return pd.read_sql(query, engine)


def get_expense_insight(month: str):
    engine = get_engine()

    query = f"""
    WITH monthly_expense AS (
        SELECT
            date_trunc('month', txn_date) AS month,
            SUM(
                CASE
                    WHEN amount < 0 AND category_id != 'finance.savings'
                    THEN amount_abs
                    ELSE 0
                END
            ) AS total_expense
        FROM iceberg.gold.fact_bank_transaction
        WHERE txn_date IS NOT NULL
          AND date_trunc('month', txn_date) <= DATE '{month}'
          AND source_type_code = 'account'
        GROUP BY 1
    )
    SELECT
        month,
        total_expense
    FROM monthly_expense
    ORDER BY month
    """

    df = pd.read_sql(query, engine)

    if df.empty:
        return {
            "current_expense": 0.0,
            "avg_12m": 0.0,
            "pct_vs_avg": 0.0,
            "diff_vs_avg": 0.0,
            "ytd_expense": 0.0,
            "series_months": [],
            "series_values": [],
        }

    df["month"] = pd.to_datetime(df["month"])
    df["total_expense"] = df["total_expense"].fillna(0.0).astype(float)

    selected_month = pd.to_datetime(month)
    current_row = df[df["month"] == selected_month].copy()
    current_expense = float(current_row["total_expense"].iloc[0]) if not current_row.empty else 0.0

    previous_12 = df[df["month"] < selected_month].tail(12).copy()
    avg_12m = float(previous_12["total_expense"].mean()) if not previous_12.empty else 0.0

    if avg_12m > 0:
        pct_vs_avg = ((current_expense - avg_12m) / avg_12m) * 100.0
        diff_vs_avg = current_expense - avg_12m
    else:
        pct_vs_avg = 0.0
        diff_vs_avg = 0.0

    ytd_df = df[
        (df["month"].dt.year == selected_month.year) &
        (df["month"] <= selected_month)
    ].copy()
    ytd_expense = float(ytd_df["total_expense"].sum()) if not ytd_df.empty else 0.0

    spark_df = df[df["month"] <= selected_month].tail(13).copy()

    return {
        "current_expense": current_expense,
        "avg_12m": avg_12m,
        "pct_vs_avg": pct_vs_avg,
        "diff_vs_avg": diff_vs_avg,
        "ytd_expense": ytd_expense,
        "series_months": [d.strftime("%Y-%m") for d in spark_df["month"]],
        "series_values": [float(v) for v in spark_df["total_expense"]],
    }


def get_income_insight(month: str):
    engine = get_engine()

    query = f"""
    WITH monthly_income AS (
        SELECT
            date_trunc('month', txn_date) AS month,
            SUM(
                CASE
                    WHEN amount > 0 AND category_id != 'finance.savings'
                    THEN amount
                    ELSE 0
                END
            ) AS total_income
        FROM iceberg.gold.fact_bank_transaction
        WHERE txn_date IS NOT NULL
          AND date_trunc('month', txn_date) <= date_trunc('month', DATE '{month}')
          AND source_type_code = 'account'
        GROUP BY 1
    )
    SELECT
        month,
        total_income
    FROM monthly_income
    ORDER BY month
    """

    df = pd.read_sql(query, engine)

    if df.empty:
        return {
            "current_income": 0.0,
            "avg_12m": 0.0,
            "pct_vs_avg": 0.0,
            "diff_vs_avg": 0.0,
            "ytd_income": 0.0,
            "series_months": [],
            "series_values": [],
        }

    df["month"] = pd.to_datetime(df["month"])
    df["total_income"] = df["total_income"].fillna(0.0).astype(float)

    selected_month = pd.to_datetime(month)
    current_row = df[df["month"] == selected_month].copy()
    current_income = float(current_row["total_income"].iloc[0]) if not current_row.empty else 0.0

    previous_12 = df[df["month"] < selected_month].tail(12).copy()
    avg_12m = float(previous_12["total_income"].mean()) if not previous_12.empty else 0.0

    if avg_12m > 0:
        pct_vs_avg = ((current_income - avg_12m) / avg_12m) * 100.0
        diff_vs_avg = current_income - avg_12m
    else:
        pct_vs_avg = 0.0
        diff_vs_avg = 0.0

    ytd_df = df[
        (df["month"].dt.year == selected_month.year) &
        (df["month"] <= selected_month)
    ].copy()
    ytd_income = float(ytd_df["total_income"].sum()) if not ytd_df.empty else 0.0

    spark_df = df[df["month"] <= selected_month].tail(13).copy()

    return {
        "current_income": current_income,
        "avg_12m": avg_12m,
        "pct_vs_avg": pct_vs_avg,
        "diff_vs_avg": diff_vs_avg,
        "ytd_income": ytd_income,
        "series_months": [d.strftime("%Y-%m") for d in spark_df["month"]],
        "series_values": [float(v) for v in spark_df["total_income"]],
    }


def get_savings_insight(month: str):
    engine = get_engine()

    query = f"""
    WITH monthly_savings AS (
        SELECT
            date_trunc('month', txn_date) AS month,
            (SUM(
                CASE
                    WHEN category_id = 'finance.savings'
                    THEN amount
                    ELSE 0
                END
            )) * (-1) AS total_savings
        FROM iceberg.gold.fact_bank_transaction
        WHERE txn_date IS NOT NULL
          AND date_trunc('month', txn_date) <= date_trunc('month', DATE '{month}')
          AND source_type_code = 'account'
        GROUP BY 1
    )
    SELECT
        month,
        total_savings
    FROM monthly_savings
    ORDER BY month
    """

    df = pd.read_sql(query, engine)

    if df.empty:
        return {
            "current_savings": 0.0,
            "avg_12m": 0.0,
            "pct_vs_avg": 0.0,
            "diff_vs_avg": 0.0,
            "ytd_savings": 0.0,
            "series_months": [],
            "series_values": [],
        }

    df["month"] = pd.to_datetime(df["month"])
    df["total_savings"] = df["total_savings"].fillna(0.0).astype(float)

    selected_month = pd.to_datetime(month)
    current_row = df[df["month"] == selected_month].copy()
    current_savings = float(current_row["total_savings"].iloc[0]) if not current_row.empty else 0.0

    previous_12 = df[df["month"] < selected_month].tail(12).copy()
    avg_12m = float(previous_12["total_savings"].mean()) if not previous_12.empty else 0.0

    if avg_12m != 0:
        pct_vs_avg = ((current_savings - avg_12m) / abs(avg_12m)) * 100.0
        diff_vs_avg = current_savings - avg_12m
    else:
        pct_vs_avg = 0.0
        diff_vs_avg = 0.0

    ytd_df = df[
        (df["month"].dt.year == selected_month.year) &
        (df["month"] <= selected_month)
    ].copy()
    ytd_savings = float(ytd_df["total_savings"].sum()) if not ytd_df.empty else 0.0

    spark_df = df[df["month"] <= selected_month].tail(13).copy()

    return {
        "current_savings": current_savings,
        "avg_12m": avg_12m,
        "pct_vs_avg": pct_vs_avg,
        "diff_vs_avg": diff_vs_avg,
        "ytd_savings": ytd_savings,
        "series_months": [d.strftime("%Y-%m") for d in spark_df["month"]],
        "series_values": [float(v) for v in spark_df["total_savings"]],
    }


def get_monthly_overview_window(selected_month: str):
    engine = get_engine()

    query = f"""
    WITH monthly_base AS (
        SELECT
            date_trunc('month', txn_date) AS month,

            SUM(
                CASE
                    WHEN (amount > 0 AND category_id != 'finance.savings')
                    THEN amount
                    ELSE 0
                END
            ) AS income_total,

            SUM(
                CASE
                    WHEN (amount < 0 AND category_id != 'finance.savings')
                    THEN abs(amount)
                    ELSE 0
                END
            ) AS expense_total,

            (SUM(
                CASE
                    WHEN category_id = 'finance.savings'
                    THEN amount
                    ELSE 0
                END
            )) * (-1) AS savings_total

        FROM iceberg.gold.fact_bank_transaction
        WHERE txn_date >= date_add('month', -12, DATE '{selected_month}')
          AND txn_date <  date_add('month', 1, DATE '{selected_month}')
          AND source_type_code = 'account'
        GROUP BY 1
    )
    SELECT
        month,
        income_total,
        expense_total,
        income_total - expense_total AS net_total,
        savings_total,
        SUM(savings_total) OVER (
            ORDER BY month
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_savings
    FROM monthly_base
    ORDER BY month
    """

    return pd.read_sql(query, engine)


def get_monthly_expense_breakdown_by_category(month: str):
    engine = get_engine()

    query = f"""
    SELECT
        lower(coalesce(category_l1, 'other')) AS category_l1,
        lower(coalesce(category_l2, 'other')) AS category_l2,
        SUM(abs(amount)) AS total_amount
    FROM iceberg.gold.fact_bank_transaction
    WHERE date_trunc('month', txn_date) = DATE '{month}'
      AND amount < 0
      AND lower(category_l1) IN (
          'groceries',
          'utilities',
          'transport',
          'shopping',
          'entertainment',
          'finance'
      )
    GROUP BY 1, 2
    ORDER BY 1, 3 DESC
    """

    return pd.read_sql(query, engine)

def get_category_12m_trend(selected_month: str):
    engine = get_engine()

    query = f"""
    WITH monthly_category AS (
        SELECT
            date_trunc('month', txn_date) AS month,
            lower(coalesce(category_l1, 'other')) AS category_l1,
            SUM(abs(amount)) AS total_amount
        FROM iceberg.gold.fact_bank_transaction
        WHERE txn_date >= date_add('month', -12, DATE '{selected_month}')
          AND txn_date <  date_add('month',  1, DATE '{selected_month}')
          AND amount < 0
          AND lower(category_l1) IN (
              'groceries',
              'utilities',
              'transport',
              'shopping',
              'entertainment',
              'finance'
          )
        GROUP BY 1, 2
    )
    SELECT
        month,
        category_l1,
        total_amount
    FROM monthly_category
    ORDER BY month, category_l1
    """

    return pd.read_sql(query, engine)

def get_transactions_by_category(month, category_l1, category_l2=None):
    engine = get_engine()

    filter_l2 = ""
    if category_l2:
        filter_l2 = f"AND lower(category_l2) = '{category_l2.lower()}'"

    query = f"""
    SELECT
        txn_date,
        coalesce(merchant_norm, concept_norm, 'Unknown') AS merchant,
        abs(amount) AS amount
    FROM iceberg.gold.fact_bank_transaction
    WHERE date_trunc('month', txn_date) = DATE '{month}'
      AND amount < 0
      AND lower(category_l1) = '{category_l1}'
      {filter_l2}
    ORDER BY txn_date DESC
    """

    return pd.read_sql(query, engine)