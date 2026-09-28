"""Refresh the current checkout's file manifest after a reviewed repository change."""
from pathlib import Path
import hashlib
import json
from package_release import ROOT, included


def refresh():
    target = ROOT / 'package-manifest.json'
    manifest = json.loads(target.read_text())
    paths = [p for p in ROOT.rglob('*') if included(p, manifest['profile'])]
    paths.append(ROOT / 'PACKAGE_README.md')
    manifest['files'] = {p.relative_to(ROOT).as_posix(): {
        'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()
    } for p in sorted(paths)}
    manifest['file_count_including_manifest'] = len(paths) + 1
    target.write_text(json.dumps(manifest, indent=2) + '\n')
    print(f"Updated manifest for {len(paths) + 1} files including the manifest itself.")


if __name__ == '__main__':
    refresh()
