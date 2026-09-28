"""Compile the included final-paper LaTeX and figure assets without research reruns."""
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
NAME = "Market-Neutral-Trading-Algorithm-Final-Paper"


if __name__ == "__main__":
    if shutil.which("xelatex") is None:
        raise SystemExit("XeLaTeX is required; see README.md for TeX and font dependencies.")
    for iteration in range(1, 5):
        result = subprocess.run(
            ["xelatex", "-interaction=nonstopmode", "-halt-on-error", NAME + ".tex"],
            cwd=HERE, capture_output=True, text=True,
        )
        log = HERE / f"compile-pass-{iteration}.txt"
        log.write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
        if result.returncode:
            raise SystemExit(f"XeLaTeX failed on pass {iteration}; inspect {log.name}.")
    print(HERE / (NAME + ".pdf"))
