"""Package the final paper, editable source and frozen private research context."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT.parent / "Market-Neutral-Trading-Algorithm-Final-Paper-Source.zip"


def included(path):
    relative = path.relative_to(ROOT)
    if not path.is_file() or any(part in {".git", ".venv", "__pycache__", ".ipynb_checkpoints",
            ".pytest_cache", "qa", "tmp", "build", "dist"} or part.endswith(".egg-info")
            for part in relative.parts):
        return False
    if relative.parts[:2] in {("paper", "archive"), ("paper", "output")}:
        return False
    if path.suffix in {".pyc", ".zip", ".tmp"} or path.name == ".DS_Store":
        return False
    if relative.parts[:2] == ("paper", "final"):
        return (relative.parts[2:3] == ("assets",) and path.suffix == ".png") or path.name in {
            "Market-Neutral-Trading-Algorithm-Final-Paper.pdf",
            "Market-Neutral-Trading-Algorithm-Final-Paper.tex",
            "README.md", "compile_source.py", "manuscript.md", "references-harvard.md", "references.bib"}
    return path.suffix != ".pdf"


def package():
    verification = json.loads((ROOT / "validation/final-paper-validation.json").read_text())
    pdf = ROOT / "paper/final/Market-Neutral-Trading-Algorithm-Final-Paper.pdf"
    assert verification["status"] == "passed"
    assert hashlib.sha256(pdf.read_bytes()).hexdigest() == verification["pdf_sha256"]
    manifest = ROOT / "validation/final-paper-package-sha256.json"
    files = sorted(path for path in ROOT.rglob("*") if included(path) and path != manifest)
    hashes = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    manifest.write_text(json.dumps({"created_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Final-paper source archive and private research snapshot; excludes this manifest",
        "files": hashes}, indent=2) + "\n")
    files.append(manifest)
    temporary = TARGET.with_suffix(".zip.tmp")
    with temporary.open("wb") as stream:
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for path in files:
                archive.write(path, str(Path(ROOT.name) / path.relative_to(ROOT)))
        stream.flush()
        os.fsync(stream.fileno())
    with zipfile.ZipFile(temporary) as archive:
        assert archive.testzip() is None
        for relative, expected in hashes.items():
            assert hashlib.sha256(archive.read(ROOT.name + "/" + relative)).hexdigest() == expected, relative
        assert len([name for name in archive.namelist() if name.endswith(".pdf")]) == 1
    digest = hashlib.sha256(temporary.read_bytes()).hexdigest()
    temporary.replace(TARGET)
    assert hashlib.sha256(TARGET.read_bytes()).hexdigest() == digest
    print(json.dumps({"path": str(TARGET), "files": len(files), "bytes": TARGET.stat().st_size,
                      "sha256": digest}, indent=2))


if __name__ == "__main__":
    package()
