#!/usr/bin/env python3
"""Check that reported research figures exist, are referenced, and have context.

Does not assess chart truthfulness, graphical quality or correctness of source.
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

REQUIRED = ("figure_id", "path", "title", "period", "unit", "source_ids", "research_question", "key_message", "limitations")


def check_figures(manifest: Path, report: Path | None = None):
    out = []
    with manifest.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        absent = sorted(set(REQUIRED) - set(reader.fieldnames or []))
        if absent:
            return [("ERROR", f"Missing figure manifest columns: {', '.join(absent)}")]
        rows = list(reader)
    content = report.read_text(encoding="utf-8-sig") if report else ""
    seen = set()
    for idx, item in enumerate(rows, 2):
        fid = item["figure_id"].strip()
        if not fid or fid in seen:
            out.append(("ERROR", f"row {idx}: blank/duplicate figure_id"))
            continue
        seen.add(fid)
        for field in ("path", "title", "period", "unit", "research_question", "key_message"):
            if not item[field].strip():
                out.append(("ERROR", f"{fid}: missing {field}"))
        pth = item["path"].strip()
        if pth and not (manifest.parent / pth).is_file():
            out.append(("ERROR", f"{fid}: figure file not found relative to manifest: {pth}"))
        sources = item["source_ids"].strip()
        if not sources:
            out.append(("WARN", f"{fid}: no source_ids; use 'SELF' only for original calculations and cite their inputs"))
        elif sources != "SELF" and any(not re.fullmatch(r"E\d{3,}", x.strip()) for x in sources.split(";")):
            out.append(("ERROR", f"{fid}: malformed source ID"))
        if report and pth and pth not in content:
            out.append(("WARN", f"{fid}: figure path not embedded in report"))
    if not rows:
        out.append(("WARN", "No figures listed; explain why charts would not improve this study"))
    if not out:
        out.append(("PASS", "Figure references and metadata appear complete; inspect rendered figures and factual sources manually"))
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("manifest", type=Path)
    p.add_argument("--report", type=Path)
    args = p.parse_args()
    try:
        result = check_figures(args.manifest, args.report)
    except (OSError, csv.Error, ValueError) as exc:
        p.exit(2, f"Figure check failed to load input: {exc}\n")
    for level, message in result:
        print(f"[{level}] {message}")
    return 1 if any(l == "ERROR" for l, _ in result) else 0


if __name__ == "__main__":
    raise SystemExit(main())
