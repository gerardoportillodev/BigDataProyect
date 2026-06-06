"""Safe XLSM inspection and streaming export helpers.

The helpers read the zipped XML parts inside the workbook and avoid loading the
entire sheet into memory. They do not print row-level values.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable
from xml.etree.ElementTree import fromstring, iterparse
from zipfile import ZipFile

from project_config import DATE_COLUMNS


MAIN_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"
OFFICE_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


@dataclass(frozen=True)
class WorkbookSummary:
    sheets: list[str]
    dimension: str | None
    row_count_including_header: int | None
    column_count: int
    headers: list[str]


def excel_serial_to_date(value: str) -> str:
    """Convert an Excel serial date to ISO format using the standard 1900 base."""
    serial = float(value)
    converted = datetime(1899, 12, 30) + timedelta(days=serial)
    return converted.date().isoformat()


def _load_shared_strings(zf: ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []

    shared: list[str] = []
    with zf.open("xl/sharedStrings.xml") as fh:
        for _, elem in iterparse(fh, events=("end",)):
            if elem.tag == MAIN_NS + "si":
                texts = [node.text or "" for node in elem.iter(MAIN_NS + "t")]
                shared.append("".join(texts))
                elem.clear()
    return shared


def _sheet_paths(zf: ZipFile) -> dict[str, str]:
    rels = fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rel_map = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels.findall(REL_NS + "Relationship")}

    workbook = fromstring(zf.read("xl/workbook.xml"))
    paths = {}
    for sheet in workbook.findall(MAIN_NS + "sheets/" + MAIN_NS + "sheet"):
        name = sheet.attrib["name"]
        relationship_id = sheet.attrib[OFFICE_REL]
        paths[name] = "xl/" + rel_map[relationship_id].lstrip("/")
    return paths


def _cell_text(cell, shared_strings: list[str]) -> str:
    value_node = cell.find(MAIN_NS + "v")
    inline_node = cell.find(MAIN_NS + "is")
    value = value_node.text if value_node is not None else None

    if value is None and inline_node is not None:
        value = "".join(node.text or "" for node in inline_node.iter(MAIN_NS + "t"))

    if value is None:
        return ""

    if cell.attrib.get("t") == "s":
        return shared_strings[int(value)]
    return value


def inspect_workbook(path: Path, sheet_name: str = "Sheet1") -> WorkbookSummary:
    """Read workbook metadata and the header row without exposing data rows."""
    with ZipFile(path) as zf:
        shared = _load_shared_strings(zf)
        sheet_paths = _sheet_paths(zf)
        target_sheet = sheet_name if sheet_name in sheet_paths else next(iter(sheet_paths))
        dimension = None
        headers: list[str] = []

        with zf.open(sheet_paths[target_sheet]) as fh:
            for _, elem in iterparse(fh, events=("end",)):
                if elem.tag == MAIN_NS + "dimension":
                    dimension = elem.attrib.get("ref")
                if elem.tag == MAIN_NS + "row" and elem.attrib.get("r") == "1":
                    headers = [_cell_text(cell, shared) for cell in elem.findall(MAIN_NS + "c")]
                    break
                if elem.tag == MAIN_NS + "row":
                    elem.clear()

    row_count = None
    column_count = len(headers)
    if dimension and ":" in dimension:
        end_cell = dimension.split(":")[-1]
        letters = "".join(ch for ch in end_cell if ch.isalpha())
        digits = "".join(ch for ch in end_cell if ch.isdigit())
        row_count = int(digits) if digits else None
        column_count = _column_letters_to_number(letters) if letters else column_count

    return WorkbookSummary(
        sheets=list(sheet_paths.keys()),
        dimension=dimension,
        row_count_including_header=row_count,
        column_count=column_count,
        headers=headers,
    )


def stream_sheet_rows(path: Path, sheet_name: str = "Sheet1") -> Iterable[list[str]]:
    """Yield rows from the first worksheet as text values."""
    with ZipFile(path) as zf:
        shared = _load_shared_strings(zf)
        sheet_paths = _sheet_paths(zf)
        target_sheet = sheet_name if sheet_name in sheet_paths else next(iter(sheet_paths))
        expected_width = inspect_workbook(path, sheet_name).column_count

        with zf.open(sheet_paths[target_sheet]) as fh:
            for _, elem in iterparse(fh, events=("end",)):
                if elem.tag == MAIN_NS + "row":
                    row = [""] * expected_width
                    for cell in elem.findall(MAIN_NS + "c"):
                        cell_ref = cell.attrib.get("r", "")
                        column_letters = "".join(ch for ch in cell_ref if ch.isalpha())
                        if not column_letters:
                            continue
                        index = _column_letters_to_number(column_letters) - 1
                        if 0 <= index < expected_width:
                            row[index] = _cell_text(cell, shared)
                    yield row
                    elem.clear()


def export_xlsm_to_tsv(input_path: Path, output_path: Path, sheet_name: str = "Sheet1") -> int:
    """Stream the worksheet to TSV and normalize known Excel serial date columns."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows_written = 0
    headers: list[str] = []

    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, delimiter="\t", lineterminator="\n")
        for row in stream_sheet_rows(input_path, sheet_name):
            if rows_written == 0:
                headers = row
                writer.writerow(headers)
                rows_written += 1
                continue

            normalized = []
            for index, value in enumerate(row):
                column = headers[index] if index < len(headers) else ""
                if column in DATE_COLUMNS and value:
                    normalized.append(_normalize_date_value(value))
                else:
                    normalized.append(value)
            writer.writerow(normalized)
            rows_written += 1

    return rows_written


def _normalize_date_value(value: str) -> str:
    try:
        return date.fromisoformat(value[:10]).isoformat()
    except ValueError:
        pass

    try:
        return excel_serial_to_date(value)
    except ValueError:
        return value


def _column_letters_to_number(letters: str) -> int:
    value = 0
    for letter in letters.upper():
        value = value * 26 + (ord(letter) - ord("A") + 1)
    return value
