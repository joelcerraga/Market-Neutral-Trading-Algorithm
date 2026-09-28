"""Download the frozen development/validation basket; never the reserved holdout."""
from pathlib import Path
from market_neutral.historical import fetch_dataset

if __name__ == "__main__":
    dataset, audit = fetch_dataset(Path(__file__).resolve().parent)
    print(f"Acquired {len(dataset.prices)} sessions and {dataset.prices.shape[1]} stocks plus SPY.")
    print(f"Period: {dataset.prices.index.min().date()} to {dataset.prices.index.max().date()}")
    print("Final holdout: not acquired.")
    print(audit[["missing", "nonpositive_volume", "moves_above_40pct"]].to_string())
