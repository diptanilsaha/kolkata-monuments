#!/usr/bin/env python3
"""Turn the KMC graded-list PDF into rows.

The PDF has no ruling lines and its cells are vertically centred, so a cell's
text can sit a line *above* the row's own ward number.  Rows are therefore
rebuilt by anchoring on the ward number in the left-hand column and assigning
every other word to whichever anchor it is vertically closest to.
"""
import collections
import json
import pathlib
import re

import pdfplumber

CACHE = pathlib.Path(__file__).parent / "cache"

# x-ranges of the eight columns, in PDF points (stable across all 42 pages)
COLUMNS = [
    ("ward", 0, 70), ("sl", 70, 110), ("premises", 110, 160), ("street", 160, 285),
    ("grade", 285, 315), ("criteria", 315, 445), ("location", 445, 580),
    ("name", 580, 10_000),
]
HEADER_WORDS = {"WARD", "SL.NO.", "GRADE", "CRITERIA", "DESCRIPTION", "LOCATIO", "LOCATION"}
RUNNING_TITLE = {"Kolkata", "Municipal", "Corporation", "Graded", "List", "of", "Heritage",
                 "Buildings", "(I,", "IIA", "and", "IIB)", "Page"}


def column_of(x):
    for name, lo, hi in COLUMNS:
        if lo <= x < hi:
            return name
    return "name"


def parse(pdf_path=None):
    pdf_path = pdf_path or CACHE / "wbhc.pdf"
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_no, page in enumerate(pdf.pages, 1):
            words = [w for w in page.extract_words() if 85 < w["top"] < 565]
            header_rows = {round(w["top"]) for w in words if w["text"] in HEADER_WORDS}
            words = [w for w in words if round(w["top"]) not in header_rows]
            words = [w for w in words if w["text"] not in RUNNING_TITLE or w["x0"] > 160]

            anchors = sorted(
                (w for w in words if w["x0"] < 70 and re.fullmatch(r"\d{3}", w["text"])),
                key=lambda w: w["top"],
            )
            if not anchors:
                continue
            cells = [collections.defaultdict(list) for _ in anchors]
            for w in words:
                nearest = min(range(len(anchors)), key=lambda i: abs(w["top"] - anchors[i]["top"]))
                cells[nearest][column_of(w["x0"])].append(w)

            for bucket in cells:
                row = {"page": page_no}
                for col, ws in bucket.items():
                    ws.sort(key=lambda w: (round(w["top"] / 6), w["x0"]))
                    row[col] = re.sub(r"\s+", " ", " ".join(w["text"] for w in ws)).strip()
                rows.append(row)

    return [_tidy(r) for r in rows]


def _tidy(row):
    grade = re.sub(r"[^IAB ]", "", row.get("grade", "")).strip()
    grade = {"I I": "I", "II": "I", "B": ""}.get(grade, grade)
    if grade not in ("I", "IIA", "IIB"):
        grade = ""
    row["grade"] = grade

    # On a handful of pages an empty LOCATION cell lets the building name drift
    # left into the location column; recover it.
    if not row.get("name") and row.get("location"):
        row["name"], row["location"] = row["location"], ""

    address = " ".join(p for p in (row.get("premises", ""), row.get("street", "")) if p).strip()
    return {
        "ward": row.get("ward", ""),
        "sl": row.get("sl", ""),
        "name": row.get("name", "").strip(),
        "address": address,
        "grade": grade,
        "criteria": row.get("criteria", "").strip(),
        "location": row.get("location", "").strip(),
        "page": row["page"],
    }


if __name__ == "__main__":
    out = parse()
    print(len(out), "rows")
    print(json.dumps(out[:5], indent=1))
