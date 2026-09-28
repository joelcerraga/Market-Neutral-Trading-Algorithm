"""Package the current source, frozen inputs and results, without legacy PDFs."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def included(path):
    relative = path.relative_to(ROOT)
    if any(part in {".git", ".venv", "__pycache__", ".ipynb_checkpoints", "qa", "build", "dist"}
           or part.endswith(".egg-info") for part in relative.parts):
        return False
    if relative.parts[:2] in {("paper", "archive"), ("paper", "output")}:
        return False
    if path.suffix in {".pyc", ".pdf", ".zip", ".tmp"} or path.name == ".DS_Store":
        return False
    if path.name == "requirements-paper.txt":
        return False
    return path.is_file()


def package():
    hash_file = ROOT / "validation/milestone-5-package-sha256.json"
    files = sorted(path for path in ROOT.rglob("*") if included(path) and path != hash_file)
    hashes = {str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    hash_file.write_text(json.dumps({"created_utc":datetime.now(timezone.utc).isoformat(),
                                    "scope":"Files in the Milestone 5 ZIP, excluding this manifest",
                                    "files":hashes},indent=2)+"\n")
    files.append(hash_file)
    target = ROOT.parent / "Market-Neutral-Trading-Algorithm-Milestone-5.zip"
    with zipfile.ZipFile(target,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for path in files:
            archive.write(path,arcname=str(Path(ROOT.name)/path.relative_to(ROOT)))
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        assert not any(name.endswith(".pdf") for name in archive.namelist())
        for relative, expected in hashes.items():
            actual = hashlib.sha256(archive.read(ROOT.name+"/"+relative)).hexdigest()
            assert actual == expected,relative
    print(json.dumps({"path":str(target),"files":len(files),"bytes":target.stat().st_size,
                      "sha256":hashlib.sha256(target.read_bytes()).hexdigest()},indent=2))


if __name__ == "__main__":
    package()
