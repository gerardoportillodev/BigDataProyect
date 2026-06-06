"""Inspect the source XLSM without printing personal data."""

from __future__ import annotations

from project_config import EXPECTED_COLUMNS, RAW_XLSM_PATH
from xlsm_utils import inspect_workbook


def main() -> None:
    summary = inspect_workbook(RAW_XLSM_PATH)
    print(f"Archivo: {RAW_XLSM_PATH}")
    print(f"Hojas: {summary.sheets}")
    print(f"Dimension: {summary.dimension}")
    print(f"Filas incluyendo encabezado: {summary.row_count_including_header}")
    print(f"Columnas: {summary.column_count}")
    print(f"Encabezados coinciden: {summary.headers == EXPECTED_COLUMNS}")
    print(f"Encabezados: {summary.headers}")


if __name__ == "__main__":
    main()
