"""
file_resolver.py - R-series File Resolver for SCIP Backend

Scans the /data directory and matches files by R-code prefix.
Allows team to use natural filenames like:
    R18_Consolidated and Overdue 01-05-26.xlsx
    R08_Advance Summary 06-05-2026.xlsx
    R04_Total Daily Collection Report 07-05-2026.xlsx

Rules:
    - Only .xlsx files are matched (openpyxl only)
    - One file per R-code in /data at any time (recommended)
    - If multiple files share the same R-code prefix, picks
      the one that sorts last alphabetically (latest date)
    - Missing R-code = None = graceful degradation
    - Non-xlsx files and Excel temp files (~$) silently ignored

Imports: os, re, logging only. No external dependencies.
Called by: data_loader.py
Position: constants.py > utils.py > file_resolver.py > data_loader.py
"""

import os
import re
import logging

logger = logging.getLogger(__name__)

VALID_R_CODES = {f"R{i:02d}" for i in range(1, 39)}

# Accept R-code prefixes followed by underscore, space, hyphen, dot, or end of name.
# Examples matched:
#   R18_consolidated_overdue.xlsx
#   R18 Consolidated and Overdue 01-05-26.xlsx
#   R18-Consolidated and Overdue.xlsx
#   R18.xlsx
R_CODE_PATTERN = re.compile(r"^(R\d{2})(?:[\s_.-].*)?\.xlsx$", re.IGNORECASE)


def resolve_r_series(data_dir):
    resolved = {}
    duplicates = {}

    if not os.path.isdir(data_dir):
        logger.warning("Data directory not found: %s", data_dir)
        return resolved

    for filename in os.listdir(data_dir):
        if not filename.lower().endswith(".xlsx"):
            continue
        if filename.startswith("~$") or filename.startswith("."):
            continue

        match = R_CODE_PATTERN.match(filename)
        if not match:
            logger.info("Skipping unrecognised file: %s", filename)
            continue

        r_code = match.group(1).upper()

        if r_code not in VALID_R_CODES:
            logger.info("Skipping unknown R-code: %s (%s)", r_code, filename)
            continue

        full_path = os.path.join(data_dir, filename)

        if r_code in resolved:
            if r_code not in duplicates:
                duplicates[r_code] = [os.path.basename(resolved[r_code])]
            duplicates[r_code].append(filename)
            existing = os.path.basename(resolved[r_code])
            if filename > existing:
                resolved[r_code] = full_path
        else:
            resolved[r_code] = full_path

    for r_code, files in duplicates.items():
        logger.warning(
            "Multiple files for %s: %s. Using: %s.",
            r_code, files, os.path.basename(resolved[r_code])
        )

    found = sorted(resolved.keys())
    missing = sorted(VALID_R_CODES - set(found))
    logger.info("Resolved %d/%d R-series files: %s",
                len(found), len(VALID_R_CODES), found)
    if missing:
        logger.info("Missing (graceful degradation): %s", missing)

    return resolved


def get_file_for_code(resolved, r_code):
    return resolved.get(r_code.upper())


def get_snapshot_date_from_filename(resolved, r_code):
    filepath = resolved.get(r_code.upper())
    if not filepath:
        return None
    filename = os.path.basename(filepath)

    m = re.search(r"(\d{2})-(\d{2})-(\d{2})(?!\d)", filename)
    if m:
        day, month, year = m.groups()
        year_full = "20" + year if int(year) < 50 else "19" + year
        return "{}-{}-{}".format(year_full, month, day)

    m = re.search(r"(\d{2})-(\d{2})-(\d{4})", filename)
    if m:
        day, month, year = m.groups()
        return "{}-{}-{}".format(year, month, day)

    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", filename)
    if m:
        return m.group(0)

    return None


def get_resolution_summary(resolved):
    found = sorted(resolved.keys())
    missing = sorted(VALID_R_CODES - set(found))
    files = {}
    for code in found:
        files[code] = {
            "filename": os.path.basename(resolved[code]),
            "snapshot_date": get_snapshot_date_from_filename(resolved, code)
        }
    return {
        "total_found": len(found),
        "total_expected": len(VALID_R_CODES),
        "status": "healthy" if len(found) >= 5 else "degraded",
        "found": found,
        "missing": missing,
        "files": files
    }
