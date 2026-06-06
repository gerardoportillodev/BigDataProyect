"""Stream the source XLSM to TSV for HDFS ingestion."""

from __future__ import annotations

import argparse
from pathlib import Path

from project_config import RAW_TSV_PATH, RAW_XLSM_PATH
from xlsm_utils import export_xlsm_to_tsv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export XLSM Sheet1 to a UTF-8 TSV file.")
    parser.add_argument("--input", type=Path, default=RAW_XLSM_PATH)
    parser.add_argument("--output", type=Path, default=RAW_TSV_PATH)
    parser.add_argument("--sheet", default="Sheet1")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows_written = export_xlsm_to_tsv(args.input, args.output, args.sheet)
    print(f"TSV generado: {args.output}")
    print(f"Filas escritas incluyendo encabezado: {rows_written}")
    print("No se imprimieron registros ni identificadores personales.")


if __name__ == "__main__":
    main()
