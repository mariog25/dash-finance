import uuid
import datetime
import pandas as pd
from sqlalchemy import text
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


def insert_tax_payment(
    fiscal_year: int,
    employee_irpf_amount: float,
    employee_social_security_amount: float,
    employer_social_security_amount: float,
    notes: str,
    source_system_code: str = "dash-app",
    source_form_id: str = "tax_review_form",
):
    engine = get_engine()
    tax_payment_id = str(uuid.uuid4())
    now = datetime.datetime.utcnow()

    query = text(
        """
        INSERT INTO iceberg.silver.finance_tax_payments_manual (
            tax_payment_id,
            fiscal_year,
            employee_irpf_amount,
            employee_social_security_amount,
            employer_social_security_amount,
            source_system_code,
            source_form_id,
            notes,
            created_at,
            updated_at,
            is_active
        ) VALUES (
            :tax_payment_id,
            :fiscal_year,
            :employee_irpf_amount,
            :employee_social_security_amount,
            :employer_social_security_amount,
            :source_system_code,
            :source_form_id,
            :notes,
            :created_at,
            :updated_at,
            :is_active
        )
        """
    )

    with engine.begin() as connection:
        connection.execute(
            query,
            {
                "tax_payment_id": tax_payment_id,
                "fiscal_year": fiscal_year,
                "employee_irpf_amount": employee_irpf_amount,
                "employee_social_security_amount": employee_social_security_amount,
                "employer_social_security_amount": employer_social_security_amount,
                "source_system_code": source_system_code,
                "source_form_id": source_form_id,
                "notes": notes,
                "created_at": now,
                "updated_at": now,
                "is_active": True,
            },
        )

    return tax_payment_id


def get_tax_payment_for_year(
    fiscal_year: int,
    source_system_code: str = "dash-app",
    source_form_id: str = "tax_review_form",
):
    engine = get_engine()

    query = f"""
    SELECT
        tax_payment_id,
        fiscal_year,
        employee_irpf_amount,
        employee_social_security_amount,
        employer_social_security_amount,
        notes
    FROM iceberg.silver.finance_tax_payments_manual
    WHERE fiscal_year = {int(fiscal_year)}
      AND source_system_code = '{source_system_code}'
      AND source_form_id = '{source_form_id}'
      AND is_active = true
    ORDER BY updated_at DESC, created_at DESC
    LIMIT 1
    """

    df = pd.read_sql(query, engine)
    if df.empty:
        return None

    row = df.iloc[0]

    def number_value(column: str) -> float:
        value = row[column]
        return 0.0 if pd.isna(value) else float(value)

    notes = row["notes"]

    return {
        "tax_payment_id": row["tax_payment_id"],
        "fiscal_year": int(row["fiscal_year"]),
        "employee_irpf_amount": number_value("employee_irpf_amount"),
        "employee_social_security_amount": number_value("employee_social_security_amount"),
        "employer_social_security_amount": number_value("employer_social_security_amount"),
        "notes": "" if pd.isna(notes) else notes,
    }


def merge_tax_payment(
    fiscal_year: int,
    employee_irpf_amount: float,
    employee_social_security_amount: float,
    employer_social_security_amount: float,
    notes: str,
    tax_payment_id: str | None = None,
    source_system_code: str = "dash-app",
    source_form_id: str = "tax_review_form",
):
    engine = get_engine()
    now = datetime.datetime.utcnow()
    payment_id = tax_payment_id or str(uuid.uuid4())

    query = text(
        """
        MERGE INTO iceberg.silver.finance_tax_payments_manual target
        USING (
            VALUES (
                :tax_payment_id,
                :fiscal_year,
                :employee_irpf_amount,
                :employee_social_security_amount,
                :employer_social_security_amount,
                :source_system_code,
                :source_form_id,
                :notes,
                :created_at,
                :updated_at,
                :is_active
            )
        ) AS source (
            tax_payment_id,
            fiscal_year,
            employee_irpf_amount,
            employee_social_security_amount,
            employer_social_security_amount,
            source_system_code,
            source_form_id,
            notes,
            created_at,
            updated_at,
            is_active
        )
        ON target.tax_payment_id = source.tax_payment_id
        WHEN MATCHED THEN UPDATE SET
            fiscal_year = source.fiscal_year,
            employee_irpf_amount = source.employee_irpf_amount,
            employee_social_security_amount = source.employee_social_security_amount,
            employer_social_security_amount = source.employer_social_security_amount,
            source_system_code = source.source_system_code,
            source_form_id = source.source_form_id,
            notes = source.notes,
            updated_at = source.updated_at,
            is_active = source.is_active
        WHEN NOT MATCHED THEN INSERT (
            tax_payment_id,
            fiscal_year,
            employee_irpf_amount,
            employee_social_security_amount,
            employer_social_security_amount,
            source_system_code,
            source_form_id,
            notes,
            created_at,
            updated_at,
            is_active
        ) VALUES (
            source.tax_payment_id,
            source.fiscal_year,
            source.employee_irpf_amount,
            source.employee_social_security_amount,
            source.employer_social_security_amount,
            source.source_system_code,
            source.source_form_id,
            source.notes,
            source.created_at,
            source.updated_at,
            source.is_active
        )
        """
    )

    with engine.begin() as connection:
        connection.execute(
            query,
            {
                "tax_payment_id": payment_id,
                "fiscal_year": fiscal_year,
                "employee_irpf_amount": employee_irpf_amount,
                "employee_social_security_amount": employee_social_security_amount,
                "employer_social_security_amount": employer_social_security_amount,
                "source_system_code": source_system_code,
                "source_form_id": source_form_id,
                "notes": notes,
                "created_at": now,
                "updated_at": now,
                "is_active": True,
            },
        )

    return payment_id


def get_tax_available_years():
    engine = get_engine()

    query = """
    SELECT DISTINCT fiscal_year
    FROM iceberg.gold.fact_tax_year_summary
    ORDER BY fiscal_year DESC
    """

    df = pd.read_sql(query, engine)
    if df.empty:
        return [str(pd.Timestamp.now().year)]

    return df["fiscal_year"].astype(int).astype(str).tolist()


def get_tax_payments_trend(selected_year: int, years_back: int = 10):
    engine = get_engine()
    year_start = selected_year - years_back

    tax_query = f"""
    SELECT
        fiscal_year,
        SUM(employee_irpf_amount) AS employee_irpf_total,
        SUM(employee_social_security_amount) AS employee_ss_total,
        SUM(employer_social_security_amount) AS employer_ss_total,
        SUM(net_salary_amount) AS salary_net_total,
        SUM(indirect_tax_amount) AS indirect_tax_total
    FROM iceberg.gold.fact_tax_year_summary
    WHERE fiscal_year BETWEEN {year_start} AND {selected_year}
    GROUP BY fiscal_year
    ORDER BY fiscal_year
    """

    tax_df = pd.read_sql(tax_query, engine)

    range_df = pd.DataFrame({"fiscal_year": list(range(year_start, selected_year + 1))})
    df = (
        range_df
        .merge(tax_df, on="fiscal_year", how="left")
    )

    df = df.fillna(
        {
            "employee_irpf_total": 0.0,
            "employee_ss_total": 0.0,
            "employer_ss_total": 0.0,
            "salary_net_total": 0.0,
            "indirect_tax_total": 0.0,
        }
    )

    df["employee_irpf_total"] = df["employee_irpf_total"].astype(float)
    df["employee_ss_total"] = df["employee_ss_total"].astype(float)
    df["employer_ss_total"] = df["employer_ss_total"].astype(float)
    df["salary_net_total"] = df["salary_net_total"].astype(float)
    df["indirect_tax_total"] = df["indirect_tax_total"].astype(float)
    df["employee_total"] = df["employee_irpf_total"] + df["employee_ss_total"]
    df["employer_burden_total"] = (
        df["employer_ss_total"]
        + df["employee_ss_total"]
        + df["employee_irpf_total"]
    )
    df["company_cost_total"] = (
        df["salary_net_total"]
        + df["employee_ss_total"]
        + df["employer_ss_total"]
        + df["employee_irpf_total"]
    )

    return df


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


def get_same_month_last_years(selected_month: str, years_back: int = 10):
    engine = get_engine()

    selected_ts = pd.to_datetime(selected_month)
    month_num = selected_ts.month
    year_end = selected_ts.year
    year_start = year_end - years_back + 1

    query = f"""
    SELECT
        year(txn_date) AS year,
        SUM(
            CASE
                WHEN amount < 0 AND category_id != 'finance.savings'
                THEN abs(amount)
                ELSE 0
            END
        ) AS expense_total,
        SUM(
            CASE
                WHEN amount > 0 AND category_id != 'finance.savings'
                THEN amount
                ELSE 0
            END
        ) AS income_total,
        (SUM(
            CASE
                WHEN category_id = 'finance.savings'
                THEN amount
                ELSE 0
            END
        ))*(-1) AS savings_total
    FROM iceberg.gold.fact_bank_transaction
    WHERE txn_date IS NOT NULL
      AND month(txn_date) = {month_num}
      AND year(txn_date) BETWEEN {year_start} AND {year_end}
      AND source_type_code = 'account'
    GROUP BY 1
    ORDER BY 1
    """

    df = pd.read_sql(query, engine)
    year_index = pd.DataFrame({'year': list(range(year_start, year_end + 1))})
    df = year_index.merge(df, on='year', how='left').fillna(0.0)
    df[['expense_total', 'income_total', 'savings_total']] = df[['expense_total', 'income_total', 'savings_total']].astype(float)
    df['net_total'] = df['income_total'] - df['expense_total']
    df['cumulative_savings'] = df['savings_total'].cumsum()
    return df


def get_yearly_totals_last_years(selected_month: str, years_back: int = 10):
    engine = get_engine()

    selected_ts = pd.to_datetime(selected_month)
    year_end = selected_ts.year
    year_start = year_end - years_back + 1

    query = f"""
    SELECT
        year(txn_date) AS year,
        SUM(
            CASE
                WHEN amount < 0 AND category_id != 'finance.savings'
                THEN abs(amount)
                ELSE 0
            END
        ) AS expense_total,
        SUM(
            CASE
                WHEN amount > 0 AND category_id != 'finance.savings'
                THEN amount
                ELSE 0
            END
        ) AS income_total,
        (SUM(
            CASE
                WHEN category_id = 'finance.savings'
                THEN amount
                ELSE 0
            END
        ))* (-1) AS savings_total
    FROM iceberg.gold.fact_bank_transaction
    WHERE txn_date IS NOT NULL
      AND txn_date >= DATE '{year_start}-01-01'
      AND txn_date < DATE '{year_end + 1}-01-01'
      AND source_type_code = 'account'
    GROUP BY 1
    ORDER BY 1
    """

    df = pd.read_sql(query, engine)
    year_index = pd.DataFrame({'year': list(range(year_start, year_end + 1))})
    df = year_index.merge(df, on='year', how='left').fillna(0.0)
    df[['expense_total', 'income_total', 'savings_total']] = df[['expense_total', 'income_total', 'savings_total']].astype(float)
    df['net_total'] = df['income_total'] - df['expense_total']
    df['cumulative_savings'] = df['savings_total'].cumsum()
    return df


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


def get_merchant_monthly_total(merchant_name: str, selected_month: str):
    """Get merchant total for current month and 12-month trend."""
    engine = get_engine()
    merchant_name = merchant_name.replace("'", "''")

    query = f"""
    WITH monthly_merchant AS (
        SELECT
            date_trunc('month', txn_date) AS month,
            SUM(
                CASE
                    WHEN amount < 0
                    THEN amount_abs
                    ELSE 0
                END
            ) AS total_amount
        FROM iceberg.gold.fact_bank_transaction
        WHERE txn_date IS NOT NULL
          AND date_trunc('month', txn_date) <= DATE '{selected_month}'
          AND (
              concept_norm LIKE '%{merchant_name}%'
              OR merchant_norm LIKE '%{merchant_name}%'
          )
        GROUP BY 1
    )
    SELECT
        month,
        total_amount
    FROM monthly_merchant
    ORDER BY month
    """

    df = pd.read_sql(query, engine)

    if df.empty:
        return {
            "current_total": 0.0,
            "avg_12m": 0.0,
            "pct_vs_avg": 0.0,
            "accumulated_12m": 0.0,
            "series_months": [],
            "series_values": [],
        }

    df["month"] = pd.to_datetime(df["month"])
    df["total_amount"] = df["total_amount"].fillna(0.0).astype(float)

    selected_ts = pd.to_datetime(selected_month)
    current_row = df[df["month"] == selected_ts].copy()
    current_total = float(current_row["total_amount"].iloc[0]) if not current_row.empty else 0.0

    previous_12 = df[df["month"] < selected_ts].tail(12).copy()
    avg_12m = float(previous_12["total_amount"].mean()) if not previous_12.empty else 0.0

    if avg_12m > 0:
        pct_vs_avg = ((current_total - avg_12m) / avg_12m) * 100.0
    else:
        pct_vs_avg = 0.0

    # Accumulated total for 12 months before selected month
    acc_12_months = df[(df["month"] >= selected_ts - pd.DateOffset(months=12)) & 
                       (df["month"] < selected_ts)].copy()
    accumulated_12m = float(acc_12_months["total_amount"].sum()) if not acc_12_months.empty else 0.0

    trend_df = df[df["month"] <= selected_ts].tail(13).copy()

    return {
        "current_total": current_total,
        "avg_12m": avg_12m,
        "pct_vs_avg": pct_vs_avg,
        "accumulated_12m": accumulated_12m,
        "series_months": [d.strftime("%Y-%m") for d in trend_df["month"]],
        "series_values": [float(v) for v in trend_df["total_amount"]],
    }


def get_merchant_transactions(merchant_name: str, selected_month: str):
    """Get detailed transactions for a merchant in a specific month."""
    engine = get_engine()
    merchant_name = merchant_name.replace("'", "''")

    query = f"""
    SELECT
        txn_date,
        merchant_norm,
        concept_norm,
        abs(amount) AS amount
    FROM iceberg.gold.fact_bank_transaction
    WHERE txn_date IS NOT NULL
          AND date_trunc('month', txn_date) <= DATE '{selected_month}'
      AND (
          concept_norm LIKE '%{merchant_name}%'
          OR merchant_norm LIKE '%{merchant_name}%'
      )
    ORDER BY txn_date DESC
    """

    return pd.read_sql(query, engine)


def get_mortgage_payment_insight(year: str):
    engine = get_engine()

    query = f"""
    SELECT
        CAST(charge_date_sk / 10000 AS INTEGER) AS year,
        SUM(installment_total_amt) AS total_payment
    FROM iceberg.gold.fact_mortgage_payment
    WHERE charge_date_sk IS NOT NULL
    GROUP BY 1
    ORDER BY 1
    """

    df = pd.read_sql(query, engine)

    if df.empty:
        return {
            "current": 0.0,
            "avg_10y": 0.0,
            "pct_vs_avg": 0.0,
            "series_years": [],
            "series_values": [],
        }

    df["year"] = df["year"].astype(int)
    df["total_payment"] = df["total_payment"].fillna(0.0).astype(float)

    selected_year = int(year)
    current_row = df[df["year"] == selected_year]
    current = float(current_row["total_payment"].iloc[0]) if not current_row.empty else 0.0

    last_10_years = df[df["year"] <= selected_year].tail(10)
    avg_10y = float(last_10_years["total_payment"].mean()) if not last_10_years.empty else 0.0

    if avg_10y > 0:
        pct_vs_avg = ((current - avg_10y) / avg_10y) * 100.0
    else:
        pct_vs_avg = 0.0

    series_df = df[df["year"] <= selected_year].tail(10)

    return {
        "current": current,
        "avg_10y": avg_10y,
        "pct_vs_avg": pct_vs_avg,
        "series_years": [int(y) for y in series_df["year"]],
        "series_values": [float(v) for v in series_df["total_payment"]],
    }


def get_mortgage_interest_insight(year: str):
    engine = get_engine()

    query = f"""
    SELECT
        CAST(charge_date_sk / 10000 AS INTEGER) AS year,
        SUM(interest_amt) AS total_interest
    FROM iceberg.gold.fact_mortgage_payment
    WHERE charge_date_sk IS NOT NULL
    GROUP BY 1
    ORDER BY 1
    """

    df = pd.read_sql(query, engine)

    if df.empty:
        return {
            "current": 0.0,
            "avg_10y": 0.0,
            "pct_vs_avg": 0.0,
            "series_years": [],
            "series_values": [],
        }

    df["year"] = df["year"].astype(int)
    df["total_interest"] = df["total_interest"].fillna(0.0).astype(float)

    selected_year = int(year)
    current_row = df[df["year"] == selected_year]
    current = float(current_row["total_interest"].iloc[0]) if not current_row.empty else 0.0

    last_10_years = df[df["year"] <= selected_year].tail(10)
    avg_10y = float(last_10_years["total_interest"].mean()) if not last_10_years.empty else 0.0

    if avg_10y > 0:
        pct_vs_avg = ((current - avg_10y) / avg_10y) * 100.0
    else:
        pct_vs_avg = 0.0

    series_df = df[df["year"] <= selected_year].tail(10)

    return {
        "current": current,
        "avg_10y": avg_10y,
        "pct_vs_avg": pct_vs_avg,
        "series_years": [int(y) for y in series_df["year"]],
        "series_values": [float(v) for v in series_df["total_interest"]],
    }


def get_mortgage_amortization_insight(year: str):
    engine = get_engine()

    query = f"""
    SELECT
        CAST(charge_date_sk / 10000 AS INTEGER) AS year,
        SUM(capital_amortized_amt) AS total_amortization
    FROM iceberg.gold.fact_mortgage_payment
    WHERE charge_date_sk IS NOT NULL
    GROUP BY 1
    ORDER BY 1
    """

    df = pd.read_sql(query, engine)

    if df.empty:
        return {
            "current": 0.0,
            "avg_10y": 0.0,
            "pct_vs_avg": 0.0,
            "series_years": [],
            "series_values": [],
        }

    df["year"] = df["year"].astype(int)
    df["total_amortization"] = df["total_amortization"].fillna(0.0).astype(float)

    selected_year = int(year)
    current_row = df[df["year"] == selected_year]
    current = float(current_row["total_amortization"].iloc[0]) if not current_row.empty else 0.0

    last_10_years = df[df["year"] <= selected_year].tail(10)
    avg_10y = float(last_10_years["total_amortization"].mean()) if not last_10_years.empty else 0.0

    if avg_10y > 0:
        pct_vs_avg = ((current - avg_10y) / avg_10y) * 100.0
    else:
        pct_vs_avg = 0.0

    series_df = df[df["year"] <= selected_year].tail(10)

    return {
        "current": current,
        "avg_10y": avg_10y,
        "pct_vs_avg": pct_vs_avg,
        "series_years": [int(y) for y in series_df["year"]],
        "series_values": [float(v) for v in series_df["total_amortization"]],
    }


def get_mortgage_trend_last_10_years(year: str):
    engine = get_engine()

    selected_year = int(year)
    start_year = selected_year - 9

    query = f"""
    SELECT
        CAST(charge_date_sk / 10000 AS INTEGER) AS year,
        SUM(installment_total_amt) AS total_payment,
        SUM(interest_amt) AS total_interest,
        SUM(capital_amortized_amt) AS total_amortization
    FROM iceberg.gold.fact_mortgage_payment
    WHERE charge_date_sk IS NOT NULL
      AND CAST(charge_date_sk / 10000 AS INTEGER) BETWEEN {start_year} AND {selected_year}
    GROUP BY 1
    ORDER BY 1
    """

    df = pd.read_sql(query, engine)

    if df.empty:
        return pd.DataFrame(columns=["year", "total_payment", "total_interest", "total_amortization"])

    df["year"] = df["year"].astype(int)
    df["total_payment"] = df["total_payment"].fillna(0.0).astype(float)
    df["total_interest"] = df["total_interest"].fillna(0.0).astype(float)
    df["total_amortization"] = df["total_amortization"].fillna(0.0).astype(float)

    year_index = pd.DataFrame({"year": list(range(start_year, selected_year + 1))})
    df = year_index.merge(df, on="year", how="left").fillna(0.0)

    return df


def get_mortgage_amortization_schedule():
    engine = get_engine()
    query = """
    SELECT
        charge_date_sk,
        installment_total_amt,
        interest_amt,
        capital_amortized_amt,
        outstanding_principal_amt,
        calculation_base_amt,
        applied_interest_rate_pct
    FROM iceberg.gold.fact_mortgage_payment
    WHERE charge_date_sk IS NOT NULL
    ORDER BY charge_date_sk
    """
    return build_mortgage_amortization_schedule(pd.read_sql(query, engine))


def build_mortgage_amortization_schedule(df, as_of=None):
    """Keep recorded payments separate from estimates at the last known rate."""
    metrics = ["total_payment", "total_interest", "total_amortization"]
    actual_metrics = [f"actual_{metric}" for metric in metrics]
    columns = ["year", *metrics, "ending_principal", "projected", *actual_metrics]
    if df.empty:
        return pd.DataFrame(columns=columns)

    df = df.copy()
    df["charge_date"] = pd.to_datetime(
        df["charge_date_sk"].astype(str), format="%Y%m%d", errors="coerce"
    )
    cutoff = pd.Timestamp(as_of) if as_of is not None else pd.Timestamp.now(tz="Europe/Madrid").tz_localize(None)
    df = df[df["charge_date"].notna() & (df["charge_date"] <= cutoff)].copy()
    df = df.sort_values("charge_date").reset_index(drop=True)
    if df.empty:
        return pd.DataFrame(columns=columns)

    amounts = {
        "installment_total_amt": "total_payment",
        "interest_amt": "total_interest",
        "capital_amortized_amt": "total_amortization",
    }
    for column in [*amounts, "outstanding_principal_amt", "calculation_base_amt", "applied_interest_rate_pct"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df[list(amounts)] = df[list(amounts)].fillna(0.0)

    # A missing balance is unknown, not a repaid loan. The calculation base
    # is the balance BEFORE this receipt's principal repayment.
    balance = df["outstanding_principal_amt"].combine_first(
        df["calculation_base_amt"] - df["capital_amortized_amt"]
    )
    cumulative_capital = df["capital_amortized_amt"].cumsum()
    # Carry earlier known balances forward, subtracting subsequent repayments.
    balance = balance.combine_first(
        (balance + cumulative_capital).ffill() - cumulative_capital
    )
    df["ending_principal"] = balance
    if pd.isna(balance.iloc[-1]):
        raise ValueError("Cannot project mortgage: no outstanding principal or calculation base available.")

    df["year"] = df["charge_date"].dt.year
    yearly = df.groupby("year")[list(amounts)].sum().rename(columns=amounts)
    # Preserve missing historical balances rather than filling them with zero.
    yearly["ending_principal"] = df.groupby("year")["ending_principal"].agg(lambda values: values.iloc[-1])
    yearly["projected"] = False
    for metric in metrics:
        yearly[f"actual_{metric}"] = yearly[metric]
    rows = yearly.to_dict("index")

    current_balance = max(float(balance.iloc[-1]), 0.0)
    if current_balance > 0:
        monthly_payment = float(df["installment_total_amt"].iloc[-1])
        rates = df["applied_interest_rate_pct"].dropna()
        if rates.empty or monthly_payment <= 0:
            raise ValueError("Cannot project mortgage: missing interest rate or positive monthly payment.")
        monthly_rate = float(rates.iloc[-1]) / 100.0 / 12.0
        last_month = df["charge_date"].iloc[-1].to_period("M")
        # Start after the last receipt, including missing months in its year.
        for offset in range(1, 40 * 12 + 1):
            projection_year = (last_month + offset).year
            interest = current_balance * monthly_rate
            amortization = min(monthly_payment - interest, current_balance)
            if amortization <= 0:
                raise ValueError("Cannot project mortgage: payment does not cover monthly interest.")
            payment = amortization + interest
            current_balance = max(current_balance - amortization, 0.0)
            row = rows.setdefault(projection_year, {
                **dict.fromkeys(metrics + actual_metrics, 0.0),
                "ending_principal": 0.0,
                "projected": True,
            })
            row["total_payment"] += payment
            row["total_interest"] += interest
            row["total_amortization"] += amortization
            row["ending_principal"] = current_balance
            row["projected"] = True
            if current_balance <= 0:
                break
        else:
            raise ValueError("Mortgage projection exceeds 40 years; check payment and rate.")

    result = pd.DataFrame.from_dict(rows, orient="index").rename_axis("year").reset_index()
    return result[columns].sort_values("year").reset_index(drop=True)
