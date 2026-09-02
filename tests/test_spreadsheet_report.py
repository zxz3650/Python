import importlib.util
from importlib.util import find_spec
from decimal import Decimal
from pathlib import Path
import sys
import tempfile
import unittest


MODULE_PATH = (
    Path(__file__).parents[1]
    / "examples"
    / "13-python-automate"
    / "spreadsheet_report.py"
)
SPEC = importlib.util.spec_from_file_location("spreadsheet_report", MODULE_PATH)
assert SPEC and SPEC.loader
spreadsheet_report = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = spreadsheet_report
SPEC.loader.exec_module(spreadsheet_report)


class SpreadsheetReportTests(unittest.TestCase):
    def test_load_sales_preserves_invalid_rows(self):
        with tempfile.TemporaryDirectory() as temporary:
            csv_path = Path(temporary) / "sales.csv"
            csv_path.write_text(
                "date,category,item,amount\n"
                "2026-08-01,training,Python,100.25\n"
                "2026-15-01,training,Broken date,10\n"
                "2026-08-03,books,Broken amount,NaN\n",
                encoding="utf-8",
            )

            records, issues = spreadsheet_report.load_sales(csv_path)

            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].amount, Decimal("100.25"))
            self.assertEqual([issue.row_number for issue in issues], [3, 4])
            self.assertIn("YYYY-MM-DD", issues[0].reason)
            self.assertIn("0 이상", issues[1].reason)

    def test_missing_required_column_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            csv_path = Path(temporary) / "sales.csv"
            csv_path.write_text(
                "date,category,item\n2026-08-01,training,Python\n",
                encoding="utf-8",
            )

            with self.assertRaises(spreadsheet_report.InputContractError):
                spreadsheet_report.load_sales(csv_path)

    def test_category_totals_use_decimal(self):
        records = [
            spreadsheet_report.SaleRecord(
                2,
                spreadsheet_report.date(2026, 8, 1),
                "training",
                "A",
                Decimal("0.1"),
            ),
            spreadsheet_report.SaleRecord(
                3,
                spreadsheet_report.date(2026, 8, 2),
                "training",
                "B",
                Decimal("0.2"),
            ),
        ]

        self.assertEqual(
            spreadsheet_report.category_totals(records),
            {"training": Decimal("0.3")},
        )

    def test_formula_like_text_is_escaped(self):
        self.assertEqual(spreadsheet_report.safe_excel_text("=2+3"), "'=2+3")
        self.assertEqual(spreadsheet_report.safe_excel_text("normal"), "normal")

    @unittest.skipUnless(find_spec("openpyxl"), "openpyxl is not installed")
    def test_workbook_structure(self):
        import openpyxl

        with tempfile.TemporaryDirectory() as temporary:
            tmp_path = Path(temporary)
            csv_path = tmp_path / "sales.csv"
            csv_path.write_text(
                "date,category,item,amount\n"
                "2026-08-01,training,Python,100\n"
                "broken,training,Bad,10\n",
                encoding="utf-8",
            )
            records, issues = spreadsheet_report.load_sales(csv_path)
            workbook = spreadsheet_report.build_workbook(records, issues)
            output = spreadsheet_report.save_workbook(
                workbook, tmp_path / "report.xlsx"
            )

            spreadsheet_report.verify_workbook(output, 1, 1)
            reopened = openpyxl.load_workbook(output, data_only=False)
            self.assertEqual(
                reopened.sheetnames,
                ["요약", "정상 데이터", "검증 오류"],
            )
            self.assertEqual(
                reopened["요약"]["B6"].value,
                "=SUM('정상 데이터'!D:D)",
            )
            self.assertEqual(reopened["정상 데이터"]["D2"].value, 100)
            reopened.close()
