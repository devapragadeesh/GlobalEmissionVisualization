"""
Utility script to download and persist CO₂ emissions data locally.
"""
from data_fetcher import EmissionsDataFetcher


def main() -> None:
    fetcher = EmissionsDataFetcher()
    print("Refreshing emissions dataset...")
    data = fetcher.get_all_countries_data()
    print(f"Dataset ready: {len(data)} countries stored locally.")


if __name__ == "__main__":
    main()

