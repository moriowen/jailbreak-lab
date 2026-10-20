"""Render report/report.html to HW4_P_Mohite_Atharva.pdf through headless Chrome.

    STUDENT_ID=... python -m src.build_pdf

The student ID goes only into a temporary copy of the page, from the environment, so it never lands
in a tracked file. The PDF is gitignored for the same reason.
"""
import os
import subprocess

from config import ROOT
from src.report_lib import SID_SLOT

SRC = ROOT / "report" / "report.html"
PDF = ROOT / "HW4_P_Mohite_Atharva.pdf"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def main():
    page = SRC.read_text()
    assert SID_SLOT in page, "student ID slot missing; rebuild with python -m src.build_report"
    sid = os.environ.get("STUDENT_ID", "").strip()
    if sid:
        page = page.replace(SID_SLOT, SID_SLOT.replace("></span>", f">{sid}</span>"))
    tmp = SRC.with_name(".report-print.html")
    tmp.write_text(page)
    try:
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        "--virtual-time-budget=10000", f"--print-to-pdf={PDF}", tmp.as_uri()],
                       check=True, capture_output=True)
    finally:
        tmp.unlink()
    print(f"wrote {PDF.name}  {PDF.stat().st_size // 1024} KB"
          + ("" if sid else "  (no STUDENT_ID set; the ID line is blank)"))


if __name__ == "__main__":
    main()
