import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


def _stage_log(message: str) -> None:
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    print(f"[SCIP bootstrap] {stamp} {message}")

SOURCE_ROOT = Path(os.environ.get("SCIP_SOURCE_ROOT", "/tmp/scip/r-series"))
FOLDER_ID = os.environ.get("SCIP_GOOGLE_DRIVE_FOLDER_ID", "").strip()
FOLDER_URL = os.environ.get("SCIP_GOOGLE_DRIVE_FOLDER_URL", "").strip()
BOOTSTRAP_ENABLED = os.environ.get("SCIP_RSERIES_BOOTSTRAP", "false").lower() == "true"

REQUIRED_MINIMUM = ["R02", "R04", "R08", "R18", "R36"]
KNOWN_R_CODES = {
    "R02", "R04", "R08", "R09", "R10", "R17", "R18",
    "R20", "R30", "R31", "R32", "R34", "R36", "R38",
}


def r_code_for_file(path: Path) -> str | None:
    match = re.match(r"^(R\d{2})", path.name.upper())
    if not match:
        return None
    code = match.group(1)
    return code if code in KNOWN_R_CODES else None


def main() -> None:
    if not BOOTSTRAP_ENABLED:
        print("[SCIP bootstrap] R-series Google Drive bootstrap disabled.")
        return

    if not FOLDER_ID and not FOLDER_URL:
        raise RuntimeError(
            "SCIP_RSERIES_BOOTSTRAP=true but neither "
            "SCIP_GOOGLE_DRIVE_FOLDER_ID nor SCIP_GOOGLE_DRIVE_FOLDER_URL is set."
        )

    folder_ref = FOLDER_URL or f"https://drive.google.com/drive/folders/{FOLDER_ID}"

    _t_total = time.monotonic()
    download_dir = SOURCE_ROOT.parent / "_drive_folder_download"

    if SOURCE_ROOT.exists():
        print(f"[SCIP bootstrap] Clearing source root: {SOURCE_ROOT}")
        shutil.rmtree(SOURCE_ROOT)

    if download_dir.exists():
        print(f"[SCIP bootstrap] Clearing previous download: {download_dir}")
        shutil.rmtree(download_dir)

    SOURCE_ROOT.mkdir(parents=True, exist_ok=True)
    download_dir.mkdir(parents=True, exist_ok=True)

    print(f"[SCIP bootstrap] Downloading Google Drive folder: {folder_ref}")
    _stage_log("download_start")
    _t_download = time.monotonic()
    subprocess.run(
    ["gdown", "--folder", folder_ref, "-O", str(download_dir)],
    check=True,)
    _stage_log(f"download_end seconds={time.monotonic() - _t_download:.1f}")

    copied = []

    _stage_log("copy_start")
    _t_copy = time.monotonic()
    for path in download_dir.rglob("*"):
        if not path.is_file():
            continue

        name = path.name
        if name.startswith("~$"):
            print(f"[SCIP bootstrap] Skipping temporary Excel file: {name}")
            continue

        if path.suffix.lower() not in {".xlsx", ".xlsm", ".xls"}:
            print(f"[SCIP bootstrap] Skipping non-Excel file: {name}")
            continue

        code = r_code_for_file(path)
        if not code:
            print(f"[SCIP bootstrap] Skipping file without R-code prefix: {name}")
            continue

        target = SOURCE_ROOT / name
        shutil.copy2(path, target)
        copied.append((code, name))

    _stage_log(f"copy_end seconds={time.monotonic() - _t_copy:.1f} files_copied={len(copied)}")

    if not copied:
        raise RuntimeError("No R-series workbooks were copied from Google Drive.")

    present_codes = sorted({code for code, _ in copied})
    missing = [code for code in REQUIRED_MINIMUM if code not in present_codes]

    print(f"[SCIP bootstrap] Source root ready: {SOURCE_ROOT}")
    print("[SCIP bootstrap] Loaded R-series files:")
    for code, name in copied:
        print(f" - {code}: {name}")

    if missing:
        raise RuntimeError(
            "Missing minimum UAT R-series workbooks: " + ", ".join(missing)
        )

    _stage_log(f"bootstrap_total seconds={time.monotonic() - _t_total:.1f}")


if __name__ == "__main__":
    main()
