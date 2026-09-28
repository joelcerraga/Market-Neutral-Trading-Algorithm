"""Verified atomic output writes after an observed empty-ledger artifact."""
from pathlib import Path
import hashlib
import os


def write_text_verified(path, text):
    path = Path(path)
    payload = text.encode("utf-8")
    if not payload:
        raise ValueError(f"Refusing empty research output: {path.name}")
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    if temporary.read_bytes() != payload:
        raise OSError(f"Research output failed byte verification: {path.name}")
    temporary.replace(path)
    if hashlib.sha256(path.read_bytes()).digest() != hashlib.sha256(payload).digest():
        raise OSError(f"Research output changed after replacement: {path.name}")


def write_csv_verified(table, path, **kwargs):
    write_text_verified(path, table.to_csv(**kwargs))
