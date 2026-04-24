"""
Data fetching module for CO₂ emissions data.
Fetches data from Our World in Data (OWID) API.
"""
import json
import os
from io import StringIO
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
import requests
from requests.exceptions import RequestException


class EmissionsDataFetcher:
    """Fetches and processes CO₂ emissions data from various sources."""
    
    def __init__(self):
        # OWID data URLs - try CSV first as it's more reliable
        self.owid_csv_urls = [
            "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv",
            "https://cdn.jsdelivr.net/gh/owid/co2-data@master/owid-co2-data.csv",
        ]
        self.owid_json_urls = [
            "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.json",
            "https://github.com/owid/co2-data/raw/master/owid-co2-data.json",
        ]
        self.carbon_monitor_url = "https://datas.carbonmonitor.org/API/downloadFullDataset.php?source=carbon_global"
        self.data_dir = Path("data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.raw_cache_file = self.data_dir / "owid_co2_raw.json"
        self.processed_cache_file = self.data_dir / "emissions_processed.json"
        self.recent_years_cache_file = self.data_dir / "carbon_monitor_recent_years.json"
        # Legacy bundled cache shipped in this repository
        self.bundled_raw_cache_file = Path("emissions_data_cache.json")

    @staticmethod
    def _normalize_country_name(name: str) -> str:
        """Normalize country names to improve cross-dataset matching."""
        if not name:
            return ""
        normalized = name.strip().lower()
        for old, new in [
            ("&", "and"),
            (".", ""),
            (",", ""),
            ("-", " "),
            ("'", ""),
        ]:
            normalized = normalized.replace(old, new)
        return " ".join(normalized.split())

    def _country_aliases(self) -> Dict[str, str]:
        """Country name aliases from Carbon Monitor to OWID naming."""
        return {
            "russian federation": "russia",
            "czech republic": "czechia",
            "viet nam": "vietnam",
            "korea": "south korea",
            "korea republic of": "south korea",
            "iran islamic republic of": "iran",
            "syrian arab republic": "syria",
            "democratic republic of the congo": "democratic republic of congo",
            "united states of america": "united states",
            "bolivia plurinational state of": "bolivia",
            "venezuela bolivarian republic of": "venezuela",
            "türkiye": "turkey",
        }

    def _load_recent_years_from_carbon_monitor(self) -> Dict[str, Dict[str, float]]:
        """Build country-level annual totals for 2024 and 2025 from Carbon Monitor daily data."""
        # Load aggregated cache first
        if self.recent_years_cache_file.exists():
            try:
                with open(self.recent_years_cache_file, 'r') as f:
                    cached = json.load(f)
                if isinstance(cached, dict) and cached:
                    print(f"Loaded recent-year cache from {self.recent_years_cache_file}")
                    return cached
            except Exception as exc:
                print(f"Recent-year cache load failed ({exc}), rebuilding...")

        try:
            print("Downloading Carbon Monitor daily dataset for 2024/2025 enrichment...")
            cm_df = pd.read_csv(self.carbon_monitor_url, usecols=['country', 'date', 'value'])
            cm_df['date'] = pd.to_datetime(cm_df['date'], format='%d/%m/%Y', errors='coerce')
            cm_df = cm_df.dropna(subset=['date', 'value', 'country'])
            cm_df['year'] = cm_df['date'].dt.year
            cm_df = cm_df[cm_df['year'].isin([2024, 2025])]

            if cm_df.empty:
                print("Carbon Monitor returned no 2024/2025 records.")
                return {}

            grouped = (
                cm_df.groupby(['country', 'year'], as_index=False)['value']
                .sum()
                .sort_values(['country', 'year'])
            )

            output: Dict[str, Dict[str, float]] = {}
            for _, row in grouped.iterrows():
                country = str(row['country']).strip()
                year_key = str(int(row['year']))
                output.setdefault(country, {})[year_key] = float(row['value'])

            with open(self.recent_years_cache_file, 'w') as f:
                json.dump(output, f)
            print(f"Saved Carbon Monitor recent-year cache to {self.recent_years_cache_file}")

            return output
        except Exception as exc:
            print(f"Carbon Monitor enrichment unavailable ({exc})")
            return {}

    def _refresh_country_summary(self, record: Dict) -> Dict:
        """Recalculate summary fields after timeline updates."""
        pairs = sorted(zip(record['years'], record['emissions']), key=lambda x: x[0])
        years = [int(y) for y, _ in pairs]
        emissions = [float(v) for _, v in pairs]

        latest_year = years[-1]
        latest_emission = emissions[-1]

        recent_pairs = [(y, v) for y, v in pairs if y >= latest_year - 5]
        if len(recent_pairs) > 1:
            trend = "increasing" if recent_pairs[-1][1] > recent_pairs[0][1] else "decreasing"
        else:
            trend = "stable"

        record['years'] = years
        record['emissions'] = emissions
        record['latest_year'] = latest_year
        record['latest_emission'] = latest_emission
        record['trend'] = trend
        record['max_emission'] = max(emissions)
        record['min_emission'] = min(emissions)
        return record

    def _augment_with_recent_years(self, processed_data: Dict[str, Dict]) -> Dict[str, Dict]:
        """Merge Carbon Monitor 2024/2025 annual totals into existing country series."""
        recent_data = self._load_recent_years_from_carbon_monitor()
        if not recent_data:
            return processed_data

        name_to_code: Dict[str, str] = {}
        for code, rec in processed_data.items():
            normalized = self._normalize_country_name(rec.get('country_name', ''))
            if normalized:
                name_to_code[normalized] = code

        aliases = self._country_aliases()
        updates = 0

        for country_name, yearly_values in recent_data.items():
            normalized = self._normalize_country_name(country_name)
            normalized = aliases.get(normalized, normalized)
            country_code = name_to_code.get(normalized)
            if not country_code:
                continue

            record = processed_data[country_code]
            merged = {int(y): float(v) for y, v in zip(record['years'], record['emissions'])}

            for year_str, value in yearly_values.items():
                year = int(year_str)
                merged[year] = float(value)

            record['years'] = sorted(merged.keys())
            record['emissions'] = [merged[y] for y in record['years']]
            processed_data[country_code] = self._refresh_country_summary(record)
            updates += 1

        if updates:
            print(f"Applied 2024/2025 enrichment to {updates} countries")

        return processed_data

    def _load_raw_cache(self, cache_file: Path, label: str) -> Optional[Dict]:
        """Load raw emissions data from a JSON cache file."""
        if not cache_file.exists():
            return None

        try:
            print(f"Loading data from {label}...")
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            if isinstance(cached_data, dict) and cached_data:
                print(f"Loaded {len(cached_data)} countries/regions from {label}")
                return cached_data
            print(f"{label} exists but is empty or invalid.")
        except Exception as e:
            print(f"Error loading {label}: {e}")

        return None

    @staticmethod
    def _max_year_in_raw_data(raw_data: Dict) -> int:
        """Return max year observed in raw OWID-like data."""
        max_year = 0
        for country_data in raw_data.values():
            co2 = country_data.get('co2', {}) if isinstance(country_data, dict) else {}
            for year_str in co2.keys():
                try:
                    year = int(year_str)
                    if year > max_year:
                        max_year = year
                except Exception:
                    continue
        return max_year

    def _download_csv_with_retries(self, url: str, attempts: int = 3) -> pd.DataFrame:
        """Download OWID CSV with explicit timeout/retry behavior."""
        last_error = None

        for attempt in range(1, attempts + 1):
            try:
                print(f"Downloading CSV (attempt {attempt}/{attempts}) from: {url}")
                response = requests.get(
                    url,
                    timeout=(10, 90),
                    headers={
                        "User-Agent": "GlobalEmissionVisualization/1.0",
                        "Accept": "text/csv,application/octet-stream,*/*",
                    },
                )
                response.raise_for_status()
                return pd.read_csv(StringIO(response.text))
            except RequestException as exc:
                last_error = exc
                print(f"CSV download failed on attempt {attempt}: {exc}")
            except Exception as exc:
                last_error = exc
                print(f"CSV parse failed on attempt {attempt}: {exc}")

        raise Exception(f"Failed to download CSV from {url}: {last_error}")
    
    def fetch_owid_data(self) -> Dict:
        """Fetch CO₂ emissions data from Our World in Data."""
        # Try to load from cache first
        cached_data = self._load_raw_cache(self.raw_cache_file, "local cache")
        cached_max_year = self._max_year_in_raw_data(cached_data) if cached_data else 0
        if cached_data and cached_max_year >= 2024:
            return cached_data
        if cached_data and cached_max_year > 0:
            print(f"Local cache is older (max year: {cached_max_year}), attempting refresh from remote source...")

        # Try fetching CSV first (more reliable)
        for csv_url in self.owid_csv_urls:
            try:
                print("Fetching data from Our World in Data (CSV format)...")
                df = self._download_csv_with_retries(csv_url)
                print(f"Downloaded CSV with {len(df)} rows")
            
                # Convert CSV to the expected JSON format
                data = {}
                for country in df['country'].unique():
                    country_df = df[df['country'] == country]
                    # Get country code (use iso_code if available, otherwise use country name)
                    country_code = country_df['iso_code'].iloc[0] if 'iso_code' in country_df.columns and pd.notna(country_df['iso_code'].iloc[0]) else country

                    # Skip if no valid code
                    if pd.isna(country_code) or country_code == '':
                        continue

                    # Build data structure
                    country_data = {'country': country}
                    if 'co2' in country_df.columns:
                        co2_data = {}
                        for _, row in country_df.iterrows():
                            if pd.notna(row['year']) and pd.notna(row['co2']):
                                year = int(row['year'])
                                co2_data[str(year)] = float(row['co2'])
                        if co2_data:
                            country_data['co2'] = co2_data

                    # Use country code as key, prefix with OWID_ if it's an ISO code
                    key = country_code if country_code.startswith('OWID_') else f"OWID_{country_code}" if len(country_code) == 3 else country_code
                    data[key] = country_data

                # Cache the data
                with open(self.raw_cache_file, 'w') as f:
                    json.dump(data, f)

                print(f"Successfully processed data for {len(data)} countries/regions")
                return data
            except Exception as e:
                print(f"Error fetching CSV from {csv_url}: {e}")

        # Fallback to bundled cache included in repo
        bundled_data = self._load_raw_cache(self.bundled_raw_cache_file, "bundled cache")
        if bundled_data:
            try:
                with open(self.raw_cache_file, 'w') as f:
                    json.dump(bundled_data, f)
                print(f"Copied bundled cache to {self.raw_cache_file}")
            except Exception as exc:
                print(f"Warning: could not write local cache from bundled data ({exc})")
            return bundled_data

        if cached_data:
            print("Remote refresh failed; using existing local cache.")
            return cached_data
        
        # Fallback: Try JSON URLs
        for url in self.owid_json_urls:
            try:
                print(f"Trying JSON format... ({url})")
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                # Cache the data
                with open(self.raw_cache_file, 'w') as f:
                    json.dump(data, f)
                
                print(f"Successfully fetched data for {len(data)} countries/regions")
                return data
            except Exception as e:
                print(f"Error fetching from {url}: {e}")
                continue
        
        # If all URLs fail and no cache, raise error
        raise Exception("Could not fetch data from any source and no cache available. Please check your internet connection.")
    
    def process_country_data(self, country_code: str, country_data: Dict) -> Optional[Dict]:
        """Process data for a single country."""
        if 'co2' not in country_data:
            return None
        
        co2_data = country_data['co2']
        years = []
        emissions = []
        
        # Extract annual CO₂ emissions
        for year_str, value in co2_data.items():
            try:
                year = int(year_str)
                if value is not None and isinstance(value, (int, float)):
                    years.append(year)
                    emissions.append(float(value))
            except (ValueError, TypeError):
                continue
        
        if not years:
            return None
        
        # Create DataFrame for easier manipulation
        df = pd.DataFrame({'year': years, 'emissions': emissions})
        df = df.sort_values('year')
        
        # Calculate trend
        latest_year = df['year'].max()
        latest_emission = df[df['year'] == latest_year]['emissions'].values[0]
        
        # Calculate 5-year average trend
        recent_years = df[df['year'] >= latest_year - 5]
        if len(recent_years) > 1:
            trend = "increasing" if recent_years['emissions'].iloc[-1] > recent_years['emissions'].iloc[0] else "decreasing"
        else:
            trend = "stable"
        
        return {
            'country_code': country_code,
            'country_name': country_data.get('country', country_code),
            'years': df['year'].tolist(),
            'emissions': df['emissions'].tolist(),
            'latest_year': int(latest_year),
            'latest_emission': float(latest_emission),
            'trend': trend,
            'max_emission': float(df['emissions'].max()),
            'min_emission': float(df['emissions'].min())
        }
    
    def get_all_countries_data(self) -> Dict[str, Dict]:
        """Get processed data for all countries."""
        # Load pre-processed data if available
        if self.processed_cache_file.exists():
            try:
                print("Loading processed emissions from local cache...")
                with open(self.processed_cache_file, 'r') as f:
                    cached_processed = json.load(f)
                    if cached_processed:
                        cached_max_year = max(
                            int(rec.get('latest_year', 0))
                            for rec in cached_processed.values()
                            if isinstance(rec, dict)
                        )
                        if cached_max_year < 2024:
                            print(f"Processed cache max year is {cached_max_year}; rebuilding from refreshed raw data...")
                        else:
                            enriched_cached = self._augment_with_recent_years(cached_processed)
                            with open(self.processed_cache_file, 'w') as wf:
                                json.dump(enriched_cached, wf)
                            return enriched_cached
            except Exception as exc:
                print(f"Processed cache load failed ({exc}), rebuilding...")

        raw_data = self.fetch_owid_data()
        processed_data = {}
        
        for country_code, country_data in raw_data.items():
            # Skip aggregate regions
            if country_code in ['OWID_WRL', 'OWID_EUR', 'OWID_ASI', 'OWID_AFR', 
                              'OWID_NAM', 'OWID_SAM', 'OWID_OCE', 'OWID_KOS']:
                continue
            
            processed = self.process_country_data(country_code, country_data)
            if processed:
                processed_data[country_code] = processed

        processed_data = self._augment_with_recent_years(processed_data)
        
        # Persist processed dataset for future runs
        try:
            with open(self.processed_cache_file, 'w') as f:
                json.dump(processed_data, f)
            print(f"Saved processed emissions dataset to {self.processed_cache_file}")
        except Exception as exc:
            print(f"Warning: could not write processed cache ({exc})")
        
        return processed_data
    
    def get_country_emission_by_year(self, country_code: str, year: int) -> Optional[float]:
        """Get emission value for a specific country and year."""
        raw_data = self.fetch_owid_data()
        if country_code not in raw_data:
            return None
        
        country_data = raw_data[country_code]
        if 'co2' not in country_data:
            return None
        
        co2_data = country_data['co2']
        year_str = str(year)
        
        if year_str in co2_data and co2_data[year_str] is not None:
            return float(co2_data[year_str])
        return None

