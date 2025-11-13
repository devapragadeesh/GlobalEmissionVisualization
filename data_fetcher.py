"""
Data fetching module for CO₂ emissions data.
Fetches data from Our World in Data (OWID) API.
"""
import json
import os
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
import requests


class EmissionsDataFetcher:
    """Fetches and processes CO₂ emissions data from various sources."""
    
    def __init__(self):
        # OWID data URLs - try CSV first as it's more reliable
        self.owid_csv_url = "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv"
        self.owid_json_urls = [
            "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.json",
            "https://github.com/owid/co2-data/raw/master/owid-co2-data.json",
        ]
        self.data_dir = Path("data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.raw_cache_file = self.data_dir / "owid_co2_raw.json"
        self.processed_cache_file = self.data_dir / "emissions_processed.json"
    
    def fetch_owid_data(self) -> Dict:
        """Fetch CO₂ emissions data from Our World in Data."""
        # Try to load from cache first
        if self.raw_cache_file.exists():
            try:
                print("Loading data from cache...")
                with open(self.raw_cache_file, 'r') as f:
                    cached_data = json.load(f)
                    print(f"Loaded {len(cached_data)} countries/regions from cache")
                    return cached_data
            except Exception as e:
                print(f"Error loading cache: {e}")
        
        # Try fetching CSV first (more reliable)
        try:
            print("Fetching data from Our World in Data (CSV format)...")
            df = pd.read_csv(self.owid_csv_url)
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
            print(f"Error fetching CSV: {e}")
        
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
                        return cached_processed
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

