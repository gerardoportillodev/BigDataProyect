from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from xlsm_utils import excel_serial_to_date


def test_excel_serial_to_date_uses_expected_base():
    assert excel_serial_to_date("46142") == "2026-04-30"
