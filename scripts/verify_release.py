"""Verify the exact delivered files without research dependencies or vendor access."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys


def verify(root):
    manifest_path = root / "package-manifest.json"
    if not manifest_path.is_file():
        raise ValueError("No package-manifest.json found. Run this in an extracted release package.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1 or manifest.get("profile") not in {"github", "complete"}:
        raise ValueError("Unsupported release manifest")
    records = manifest["files"]
    problems = []
    for name, record in records.items():
        relative = PurePosixPath(name)
        if relative.is_absolute() or ".." in relative.parts or "\\" in name:
            raise ValueError(f"Invalid manifest path: {name}")
        path = root.joinpath(*relative.parts)
        if not path.is_file():
            problems.append(f"Missing: {name}")
            continue
        content = path.read_bytes()
        if len(content) != record["bytes"] or hashlib.sha256(content).hexdigest() != record["sha256"]:
            problems.append(f"Changed: {name}")
    if len(records) + 1 != manifest["file_count_including_manifest"]:
        problems.append("Manifest file count is inconsistent")
    if problems:
        raise ValueError("\n".join(problems[:20]) + (f"\n... {len(problems)} problems in total" if len(problems) > 20 else ""))
    return {"status": "passed", "profile": manifest["profile"], "files_checked": len(records),
            "research_outputs": manifest["output_count"], "notebooks": manifest["notebook_count"],
            "interactive_explorers": manifest["interactive_html_count"],
            "vendor_input_files": manifest["vendor_input_files_included"],
            "scope": "Listed files verified; manifest itself and unlisted additions are not checked"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        result = verify(args.root.resolve())
    except (ValueError, KeyError, OSError) as error:
        print(f"Release verification failed:\n{error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
