"""
3D Globe visualization module for CO₂ emissions.
Uses Plotly for interactive 3D globe visualization.
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, Optional
import json


class GlobeVisualizer:
    """Creates and manages the 3D interactive globe visualization."""
    
    def __init__(self, emissions_data: Dict[str, Dict]):
        self.emissions_data = emissions_data
        self.current_year = max([data['latest_year'] for data in emissions_data.values()])
        self.country_codes_map = self._load_country_codes()
    
    def _load_country_codes(self) -> Dict[str, str]:
        """Map OWID country codes to ISO-3 codes for Plotly."""
        # Common OWID to ISO-3 mappings
        # Plotly choropleth requires ISO-3 codes
        owid_to_iso3 = {
            'USA': 'USA', 'GBR': 'GBR', 'CHN': 'CHN', 'IND': 'IND', 'RUS': 'RUS',
            'JPN': 'JPN', 'DEU': 'DEU', 'IRN': 'IRN', 'KOR': 'KOR', 'SAU': 'SAU',
            'CAN': 'CAN', 'MEX': 'MEX', 'BRA': 'BRA', 'AUS': 'AUS', 'IDN': 'IDN',
            'TUR': 'TUR', 'FRA': 'FRA', 'ITA': 'ITA', 'ESP': 'ESP', 'POL': 'POL',
            'ZAF': 'ZAF', 'NLD': 'NLD', 'BEL': 'BEL', 'ARG': 'ARG', 'EGY': 'EGY',
            'THA': 'THA', 'PAK': 'PAK', 'BGD': 'BGD', 'VNM': 'VNM', 'PHL': 'PHL',
            'NGA': 'NGA', 'DZA': 'DZA', 'IRQ': 'IRQ', 'UKR': 'UKR', 'KAZ': 'KAZ',
            'ARE': 'ARE', 'VEN': 'VEN', 'MYS': 'MYS', 'CHL': 'CHL', 'ROU': 'ROU',
            'CZE': 'CZE', 'PER': 'PER', 'NZL': 'NZL', 'QAT': 'QAT', 'HUN': 'HUN',
            'SWE': 'SWE', 'PRT': 'PRT', 'GRC': 'GRC', 'NOR': 'NOR', 'FIN': 'FIN',
            'DNK': 'DNK', 'AUT': 'AUT', 'ISR': 'ISR', 'IRL': 'IRL', 'SGP': 'SGP',
            'COL': 'COL', 'ECU': 'ECU', 'BOL': 'BOL', 'URY': 'URY', 'PRY': 'PRY',
            'CRI': 'CRI', 'PAN': 'PAN', 'GTM': 'GTM', 'HND': 'HND', 'NIC': 'NIC',
            'SLV': 'SLV', 'CUB': 'CUB', 'JAM': 'JAM', 'HTI': 'HTI', 'DOM': 'DOM',
            'TWN': 'TWN', 'HKG': 'HKG', 'KWT': 'KWT', 'OMN': 'OMN', 'BHR': 'BHR',
            'LBN': 'LBN', 'JOR': 'JOR', 'SYR': 'SYR', 'YEM': 'YEM', 'AFG': 'AFG',
            'UZB': 'UZB', 'TKM': 'TKM', 'TJK': 'TJK', 'KGZ': 'KGZ', 'MNG': 'MNG',
            'NPL': 'NPL', 'BTN': 'BTN', 'LKA': 'LKA', 'MDV': 'MDV', 'MMR': 'MMR',
            'LAO': 'LAO', 'KHM': 'KHM', 'BRN': 'BRN', 'PNG': 'PNG', 'FJI': 'FJI',
            'KEN': 'KEN', 'TZA': 'TZA', 'UGA': 'UGA', 'ETH': 'ETH', 'SDN': 'SDN',
            'SSD': 'SSD', 'CAF': 'CAF', 'TCD': 'TCD', 'NER': 'NER', 'MLI': 'MLI',
            'BFA': 'BFA', 'GHA': 'GHA', 'CIV': 'CIV', 'SEN': 'SEN', 'GIN': 'GIN',
            'GNB': 'GNB', 'SLE': 'SLE', 'LBR': 'LBR', 'CMR': 'CMR', 'GAB': 'GAB',
            'COG': 'COG', 'COD': 'COD', 'RWA': 'RWA', 'BDI': 'BDI', 'AGO': 'AGO',
            'ZMB': 'ZMB', 'MWI': 'MWI', 'MOZ': 'MOZ', 'ZWE': 'ZWE', 'BWA': 'BWA',
            'NAM': 'NAM', 'LSO': 'LSO', 'SWZ': 'SWZ', 'MDG': 'MDG', 'MUS': 'MUS',
            'COM': 'COM', 'SYC': 'SYC', 'DJI': 'DJI', 'ERI': 'ERI', 'SOM': 'SOM',
            'MAR': 'MAR', 'TUN': 'TUN', 'LBY': 'LBY', 'MRT': 'MRT', 'ESH': 'ESH',
            'GMB': 'GMB', 'CPV': 'CPV', 'STP': 'STP', 'GNQ': 'GNQ', 'BEN': 'BEN',
            'TGO': 'TGO', 'LVA': 'LVA', 'LTU': 'LTU', 'EST': 'EST', 'BLR': 'BLR',
            'MDA': 'MDA', 'GEO': 'GEO', 'ARM': 'ARM', 'AZE': 'AZE', 'ALB': 'ALB',
            'MKD': 'MKD', 'BIH': 'BIH', 'SRB': 'SRB', 'MNE': 'MNE', 'HRV': 'HRV',
            'SVN': 'SVN', 'SVK': 'SVK', 'CHE': 'CHE', 'LIE': 'LIE', 'LUX': 'LUX',
            'ISL': 'ISL', 'MLT': 'MLT', 'CYP': 'CYP', 'BGR': 'BGR', 'MDA': 'MDA',
        }
        
        mapping = {}
        for code, data in self.emissions_data.items():
            clean_code = code.replace('OWID_', '')
            # Use ISO-3 if available, otherwise try the clean code
            iso3_code = owid_to_iso3.get(clean_code, clean_code)
            mapping[code] = iso3_code
        return mapping
    
    def get_emission_color(self, emission_value: float, max_emission: float) -> str:
        """Get color based on emission value (green to red scale)."""
        if emission_value is None or max_emission == 0:
            return '#808080'  # Gray for no data
        
        # Normalize to 0-1 range
        normalized = min(emission_value / max_emission, 1.0)
        
        # Create color scale from green (low) to red (high)
        if normalized < 0.2:
            return '#00FF00'  # Green
        elif normalized < 0.4:
            return '#80FF00'  # Yellow-green
        elif normalized < 0.6:
            return '#FFFF00'  # Yellow
        elif normalized < 0.8:
            return '#FF8000'  # Orange
        else:
            return '#FF0000'  # Red
    
    def create_globe(
        self,
        year: Optional[int] = None,
        rotation: Optional[Dict[str, float]] = None,
        color_range: Optional[Dict[str, float]] = None
    ) -> go.Figure:
        """Create the 3D globe visualization."""
        if year is None:
            year = self.current_year
        if rotation is None:
            rotation = {"lon": 0, "lat": 0}
        
        # Prepare data for choropleth
        country_codes = []
        emission_values = []
        country_names = []
        
        max_emission = max([data['latest_emission'] for data in self.emissions_data.values()])
        
        for code, data in self.emissions_data.items():
            # Get emission for the specified year
            if year in data['years']:
                year_idx = data['years'].index(year)
                emission = data['emissions'][year_idx]
            else:
                # Use latest available
                emission = data['latest_emission']
            
            country_name = data['country_name']
            # Use ISO-3 code from mapping
            iso3_code = self.country_codes_map.get(code, code.replace('OWID_', ''))
            country_codes.append(iso3_code)
            emission_values.append(emission)
            country_names.append(country_name)
        
        emission_array = np.array(emission_values, dtype=float)
        with np.errstate(invalid='ignore'):
            percentile_5 = float(np.nanpercentile(emission_array, 5)) if emission_array.size else 0.0
            percentile_95 = float(np.nanpercentile(emission_array, 95)) if emission_array.size else 0.0
        if color_range:
            zmin = color_range.get("min", max(0.0, percentile_5))
            zmax = color_range.get("max", percentile_95 if percentile_95 > 0 else float(np.nanmax(emission_array)))
        else:
            zmin = max(0.0, percentile_5)
            zmax = percentile_95 if percentile_95 > 0 else float(np.nanmax(emission_array))
        if np.isnan(zmax) or zmax <= 0:
            zmax = max_emission if max_emission > 0 else 1.0
        if zmax <= zmin:
            zmin = 0.0
        
        # Create the globe using Plotly's choropleth
        fig = go.Figure()
        
        # Add countries as colored regions using choropleth
        fig.add_trace(go.Choropleth(
            locations=country_codes,
            z=emission_values,
            colorscale='RdYlGn_r',  # Red-Yellow-Green reversed (high emissions = red)
            zmin=zmin,
            zmax=zmax,
            marker_line_color='white',
            marker_line_width=0.5,
            colorbar=dict(
                title="CO₂ Emissions<br>(Million Tonnes)",
                thickness=15,
                len=0.5,
                x=1.02,
                tickformat=".0f"
            ),
            customdata=[[name, val, code] for name, val, code in zip(country_names, emission_values, country_codes)],
            hovertemplate='<b>%{customdata[0]}</b><br>' +
                         'Emissions: %{z:.2f} Million Tonnes<br>' +
                         '<extra></extra>',
            name=''
        ))
        
        # Update layout for 3D globe projection
        fig.update_geos(
            projection_type="orthographic",
            projection_rotation=dict(
                lon=rotation.get("lon", 0),
                lat=rotation.get("lat", 0)
            ),
            showocean=True,
            oceancolor="LightBlue",
            showland=True,
            landcolor="LightGray",
            showcountries=True,
            countrycolor="White",
            showlakes=True,
            lakecolor="LightBlue",
            showrivers=True,
            rivercolor="LightBlue"
        )
        
        fig.update_layout(
            title=dict(
                text=f'Global CO₂ Emissions by Country ({year})',
                x=0.5,
                font=dict(size=24)
            ),
            geo=dict(
                bgcolor='rgba(0,0,0,0)',
                showframe=False
            ),
            height=800,
            margin=dict(l=0, r=0, t=50, b=0)
        )
        
        return fig
    
    def create_interactive_globe(self, year: Optional[int] = None) -> go.Figure:
        """Create an interactive 3D globe with click functionality."""
        fig = self.create_globe(year)
        
        # Add JavaScript for click interactivity
        # Note: Plotly's click events work with custom JavaScript
        # We'll handle this in the main app with Dash or use Plotly's built-in click callbacks
        
        return fig
    
    def get_country_info_html(self, country_code: str) -> str:
        """Generate HTML info panel for a country."""
        if country_code not in self.emissions_data:
            return "<p>No data available for this country.</p>"
        
        data = self.emissions_data[country_code]
        
        html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>{data['country_name']}</h2>
            <hr>
            <h3>Latest Data ({data['latest_year']})</h3>
            <p style="font-size: 24px; color: #FF6B6B;">
                <strong>{data['latest_emission']:.2f} Million Tonnes CO₂</strong>
            </p>
            <h3>Trend</h3>
            <p style="font-size: 18px;">
                <strong>{data['trend'].capitalize()}</strong>
            </p>
            <h3>Historical Range</h3>
            <p>
                Maximum: {data['max_emission']:.2f} Million Tonnes<br>
                Minimum: {data['min_emission']:.2f} Million Tonnes
            </p>
            <h3>Data Points</h3>
            <p>Years of data: {len(data['years'])} ({min(data['years'])} - {max(data['years'])})</p>
        </div>
        """
        return html

