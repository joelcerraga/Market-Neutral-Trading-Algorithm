"""Build public and complete research archives without rerunning experiments.

Uses only the standard library. Run from a complete project to build both.
"""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PROJECT = "Market-Neutral-Trading-Algorithm"
RELEASE_DATE = "2026-09-28"
PDF = "paper/final/Market-Neutral-Trading-Algorithm-Final-Paper.pdf"
GENERATED = {"PACKAGE_README.md", "package-manifest.json"}
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".ipynb_checkpoints",
             ".pytest_cache", "qa", "tmp", "build", "dist", "release-build"}
SKIP_SUFFIXES = {".pyc", ".zip", ".tmp", ".aux", ".log", ".out", ".toc",
                 ".lof", ".lot", ".loe", ".lol", ".fls", ".fdb_latexmk"}
DATA_DIRS = {"cache", "processed", "final-cache (separate from original frozen cache)",
             "final-processed"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def vendor_input(relative):
    return len(relative.parts) > 2 and relative.parts[0] == "data" and relative.parts[1] in DATA_DIRS


def included(path, profile):
    rel = path.relative_to(ROOT)
    if not path.is_file() or path.name in GENERATED:
        return False
    if any(part in SKIP_DIRS or part.endswith(".egg-info") for part in rel.parts):
        return False
    if path.name in {".DS_Store", "Thumbs.db", ".env"} or path.name.startswith(".env."):
        return False
    if path.suffix in SKIP_SUFFIXES | {".pem", ".key"} or path.name.endswith(".synctex.gz"):
        return False
    if rel.parts[:2] == ("paper", "final") and path.name.startswith("compile-pass-"):
        return False
    if rel.parts[:2] == ("paper", "output") and path.name.startswith("equation-"):
        return False
    if profile == "github" and vendor_input(rel):
        return False
    if path.is_symlink():
        raise ValueError(f"Refusing to package a symlink: {rel}")
    return True


def profile_readme(profile):
    purpose = (
        "This is the **GitHub package**. Upload its extracted contents to your repository. "
        "Vendor input/cache files and processed price snapshots are omitted. "
        "All saved research outputs are included. Historical replay needs the Complete archive."
        if profile == "github" else
        "This is the **Complete personal archive**. It includes the exact vendor observations "
        "and processed snapshots for offline historical replay after dependency installation. "
        "Use the separate GitHub package for public upload."
    )
    return (f"# {PROJECT}: {profile.title()} archive\n\n{purpose}\n\n"
            "Read `README.md`, `START_HERE.md`, `GITHUB_UPLOAD.md` and `docs/OUTPUTS.md`.\n\n"
            "Run `python scripts/verify_release.py` immediately after extraction to verify "
            "every listed file. The manifest excludes itself; unlisted additions are not checked.\n\n"
            f"Packaging date: {RELEASE_DATE}. The final PDF's requested cover date remains March 2026.\n")


def build(profile, destination):
    files = {p.relative_to(ROOT).as_posix(): p.read_bytes()
             for p in sorted(ROOT.rglob("*")) if included(p, profile)}
    vendor_count = sum(vendor_input(Path(name)) for name in files)
    expected = 102 if profile == "complete" else 0
    if vendor_count != expected:
        raise ValueError(f"{profile}: expected {expected} vendor input files, found {vendor_count}")
    outputs = [name for name in files if name.startswith("outputs/")]
    notebooks = [name for name in files if name.startswith("notebooks/") and name.endswith(".ipynb")]
    explorers = [name for name in outputs if name.endswith(".html")]
    if (len(outputs), len(notebooks), len(explorers)) != (175, 5, 4):
        raise ValueError("The frozen output/notebook/explorer collection is incomplete")
    verification = json.loads(files["validation/final-paper-validation.json"])
    if verification["status"] != "passed" or digest(files[PDF]) != verification["pdf_sha256"]:
        raise ValueError("The PDF differs from the verified final document")
    for name, content in files.items():
        if name.startswith("protocol/") and name.endswith(".lock.json"):
            lock = json.loads(content)
            definition = name.replace(".lock.json", ".json")
            if digest(files[definition]) != lock["sha256"]:
                raise ValueError(f"Protocol hash mismatch: {definition}")
    files["PACKAGE_README.md"] = profile_readme(profile).encode("utf-8")
    manifest = {
        "schema_version": 1, "release_date": RELEASE_DATE, "profile": profile,
        "project": PROJECT, "scope": "Every packaged file except package-manifest.json",
        "file_count_including_manifest": len(files) + 1,
        "output_count": len(outputs), "notebook_count": len(notebooks),
        "interactive_html_count": len(explorers), "vendor_input_files_included": vendor_count,
        "files": {name: {"bytes": len(content), "sha256": digest(content)}
                  for name, content in sorted(files.items())},
    }
    files["package-manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    destination.mkdir(parents=True, exist_ok=True)
    label = "GitHub" if profile == "github" else "Complete"
    target = destination / f"{PROJECT}-{label}.zip"
    temporary = target.with_suffix(".zip.tmp")
    day = date.fromisoformat(RELEASE_DATE)
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, content in sorted(files.items()):
            info = zipfile.ZipInfo(f"{PROJECT}/{name}", (day.year, day.month, day.day, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, content, compresslevel=6)
    with zipfile.ZipFile(temporary) as archive:
        if archive.testzip() is not None or len(archive.namelist()) != len(files):
            raise ValueError("ZIP integrity failure")
        for name, content in files.items():
            if archive.read(f"{PROJECT}/{name}") != content:
                raise ValueError(f"ZIP byte mismatch: {name}")
    temporary.replace(target)
    return {"path": str(target.resolve()), "profile": profile, "files": len(files),
            "bytes": target.stat().st_size, "sha256": digest(target.read_bytes()),
            "outputs": len(outputs), "vendor_inputs": vendor_count}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=["all", "github", "complete"], default="all")
    parser.add_argument("--destination", type=Path, default=ROOT.parent)
    args = parser.parse_args()
    profiles = ["github", "complete"] if args.profile == "all" else [args.profile]
    print(json.dumps([build(profile, args.destination.resolve()) for profile in profiles], indent=2))


if __name__ == "__main__":
    main()
