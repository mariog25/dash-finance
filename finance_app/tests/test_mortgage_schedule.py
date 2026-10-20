import ast
from pathlib import Path
import unittest

import pandas as pd

from services.finance_queries import build_mortgage_amortization_schedule
from utils.formatters import format_eur_es, format_pct_es, deviation_class


class MortgageScheduleTests(unittest.TestCase):
    def receipt(self, **overrides):
        return {
            "charge_date_sk": 20260919,
            "installment_total_amt": 444.53,
            "interest_amt": 65.75,
            "capital_amortized_amt": 378.78,
            "outstanding_principal_amt": None,
            "calculation_base_amt": 31185.98,
            "applied_interest_rate_pct": 2.53,
            **overrides,
        }

    def build(self, receipts):
        return build_mortgage_amortization_schedule(
            pd.DataFrame(receipts), as_of="2026-10-20"
        )

    def test_missing_balance_projects_remaining_principal(self):
        schedule = self.build([self.receipt()])
        self.assertAlmostEqual(schedule.total_amortization.sum(), 31185.98)
        self.assertAlmostEqual(schedule.actual_total_amortization.sum(), 378.78)
        self.assertAlmostEqual(schedule.actual_total_interest.sum(), 65.75)
        self.assertGreater(schedule.total_interest.sum(), 65.75)
        self.assertAlmostEqual(schedule.ending_principal.iloc[-1], 0)
        self.assertTrue((schedule.total_payment - schedule.total_interest
                         - schedule.total_amortization).abs().max() < 1e-8)

    def test_projection_starts_after_last_receipt_not_current_month(self):
        schedule = self.build([self.receipt()])
        self.assertAlmostEqual(schedule.iloc[0].total_payment, 444.53 * 4)
        self.assertAlmostEqual(schedule.iloc[0].actual_total_payment, 444.53)

    def test_paid_off_balance_is_preserved(self):
        schedule = self.build([self.receipt(outstanding_principal_amt=0)])
        self.assertEqual(len(schedule), 1)
        self.assertFalse(schedule.projected.any())
        self.assertAlmostEqual(schedule.total_amortization.sum(), 378.78)

    def test_previous_balance_is_reduced_by_subsequent_repayments(self):
        schedule = self.build([
            self.receipt(charge_date_sk=20260819, outstanding_principal_amt=31185.98),
            self.receipt(calculation_base_amt=None),
        ])
        self.assertAlmostEqual(schedule.total_amortization.sum(), 31185.98 + 378.78)

    def test_future_receipts_do_not_count_as_paid(self):
        schedule = self.build([
            self.receipt(), self.receipt(charge_date_sk=20261119),
        ])
        self.assertAlmostEqual(schedule.actual_total_payment.sum(), 444.53)

    def test_unknown_balance_does_not_silently_mean_paid_off(self):
        with self.assertRaisesRegex(ValueError, "no outstanding principal"):
            self.build([self.receipt(calculation_base_amt=None)])

    def test_invalid_dates_and_empty_input(self):
        self.assertTrue(self.build([]).empty)
        self.assertTrue(self.build([self.receipt(charge_date_sk=20261399)]).empty)

    def test_stale_history_projects_remaining_months_of_last_year(self):
        schedule = self.build([self.receipt(charge_date_sk=20250919)])
        self.assertAlmostEqual(schedule.iloc[0].total_payment, 444.53 * 4)

    def test_dashboard_accumulates_actuals_even_in_a_projected_year(self):
        # Load the callback without page registration or database access.
        source = Path(__file__).resolve().parents[1] / "pages" / "mortgage_revision.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        callback = next(node for node in tree.body
                        if isinstance(node, ast.FunctionDef)
                        and node.name == "update_mortgage_dashboard")
        callback.decorator_list = []
        insight = {"current": 0, "avg_10y": 0, "pct_vs_avg": 0,
                   "series_years": [], "series_values": []}
        schedule = self.build([self.receipt()])
        namespace = {
            "get_mortgage_payment_insight": lambda year: insight,
            "get_mortgage_interest_insight": lambda year: insight,
            "get_mortgage_amortization_insight": lambda year: insight,
            "get_mortgage_amortization_schedule": lambda: schedule,
            "format_eur_es": format_eur_es,
            "format_pct_es": format_pct_es,
            "deviation_class": deviation_class,
        }
        exec(compile(ast.Module(body=[callback], type_ignores=[]), str(source), "exec"), namespace)
        result = namespace["update_mortgage_dashboard"]("2026", {"visible": True})
        for index, actual in [(5, 444.53), (11, 65.75), (17, 378.78)]:
            self.assertTrue(result[index].startswith(format_eur_es(actual) + "/"))


if __name__ == "__main__":
    unittest.main()
