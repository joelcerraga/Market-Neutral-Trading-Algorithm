"""Render and verify every final-paper page for visual review.

Requires Poppler's pdftoppm and requirements-paper.txt. Images are temporary QA
artifacts, not additions to the scientific paper or the source release.
"""
from pathlib import Path
from io import BytesIO
import hashlib
import json
import os
import subprocess
import fitz
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "paper/final/Market-Neutral-Trading-Algorithm-Final-Paper.pdf"
QA = PDF.parent / "qa"


def safe_write(path, data):
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    assert temporary.read_bytes() == data
    temporary.replace(path)
    assert path.read_bytes() == data


def render():
    pages = QA / "final-pages"
    sheets = QA / "contact-sheets"
    pages.mkdir(parents=True, exist_ok=True)
    sheets.mkdir(parents=True, exist_ok=True)
    manifest = QA / "render-manifest.json"
    previous = json.loads(manifest.read_text())["pages"] if manifest.exists() else {}
    count = len(fitz.open(PDF))
    hashes = {}
    changed = []
    for number in range(1, count + 1):
        result = subprocess.run(["pdftoppm", "-f", str(number), "-l", str(number),
            "-singlefile", "-r", "110", "-png", str(PDF)], capture_output=True, check=True)
        Image.open(BytesIO(result.stdout)).load()
        target = pages / f"page-{number:02}.png"
        safe_write(target, result.stdout)
        digest = hashlib.sha256(result.stdout).hexdigest()
        hashes[target.name] = digest
        if previous.get(target.name) != digest:
            changed.append(number)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 18)
    except OSError:
        font = ImageFont.load_default(size=18)
    for first in range(1, count + 1, 2):
        sheet = Image.new("RGB", (1840, 1340), "#dfe3e7")
        draw = ImageDraw.Draw(sheet)
        for column in range(2):
            number = first + column
            if number > count:
                continue
            page = Image.open(pages / f"page-{number:02}.png").convert("RGB")
            page.thumbnail((900, 1280))
            sheet.paste(page, (10 + 920 * column, 45))
            draw.text((14 + 920 * column, 12), f"Physical page {number}", font=font, fill="#222222")
        buffer = BytesIO()
        sheet.save(buffer, format="JPEG", quality=93)
        safe_write(sheets / f"pages-{first:02}-{min(first + 1, count):02}.jpg", buffer.getvalue())
    result = {"pdf_sha256": hashlib.sha256(PDF.read_bytes()).hexdigest(), "renderer": "pdftoppm",
        "dpi": 110, "page_count": count, "pages": hashes, "changed_since_previous_render": changed}
    safe_write(manifest, (json.dumps(result, indent=2) + "\n").encode())
    print(json.dumps({"rendered_and_decoded_pages": count, "changed_pages": changed}, indent=2))


if __name__ == "__main__":
    render()
