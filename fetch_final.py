"""Acquire the explicitly released test only after verifying its protocol lock."""
from pathlib import Path
from market_neutral.final_data import fetch_final_dataset

if __name__ == "__main__":
    dataset, audit = fetch_final_dataset(Path(__file__).resolve().parent)
    print(audit.to_string())
    print(dataset.metadata)
