"""Build the submission ZIP: report PDF, source, data, every result record, Slurm scripts and job logs.

    python -m src.package                      # reuses the existing PDF if its ID line is filled in
    STUDENT_ID=... python -m src.package       # rebuilds the PDF first

Refuses to package a PDF with a blank ID line. Raw model outputs (results/gen_*.json, results/judge_*.json) are DELIBERATELY excluded: they
hold full jailbreak payloads, and the report shows only redacted snippets. Only aggregates
(summary.json, first_token.json) and the human labels go in. Slurm logs go in.
"""
import os
import re
import subprocess
import sys
import zipfile

from config import ROOT
from src import build_pdf

NAME = "HW4_P_Mohite_Atharva"
ZIP = ROOT / f"{NAME}.zip"


def members():
    yield build_pdf.PDF
    yield from (ROOT / f for f in ("README.md", "requirements.txt", "config.py"))
    # NB: results/gen_*.json and results/judge_*.json are excluded on purpose (full payloads).
    for pattern in ("src/*.py", "data/behaviors.json", "data/templates.json",
                    "results/summary.json", "results/first_token.json", "results/manual_labels.json",
                    "slurm/*.sbatch", "slurm/jobs/*", "slurm/logs/*.out",
                    "report/report.html", "report/critique-notes.md", "report/ai_analysis_r*.md"):
        yield from sorted(p for p in ROOT.glob(pattern) if p.is_file() and "smoke" not in p.name)


def pdf_has_id():
    if not build_pdf.PDF.exists():
        return False
    text = subprocess.run(["pdftotext", "-f", "1", "-l", "1", str(build_pdf.PDF), "-"],
                          capture_output=True, text=True).stdout
    m = re.search(r"Student ID:\s*(\S+)", text)
    return bool(m and m.group(1)[0].isdigit())


def main():
    if os.environ.get("STUDENT_ID", "").strip():
        build_pdf.main()
    elif not pdf_has_id():
        sys.exit("the PDF has no student ID; run with STUDENT_ID=... to rebuild it")
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in members():
            z.write(f, f"{NAME}/{f.relative_to(ROOT)}")
    with zipfile.ZipFile(ZIP) as z:
        n = len(z.namelist())
    print(f"wrote {ZIP.name}  {n} files  {ZIP.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
