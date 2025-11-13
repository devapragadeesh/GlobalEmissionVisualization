# Interactive 3D Carbon Emissions Globe

An interactive 3D digital globe that displays carbon emissions for every country. Users can click on countries to view detailed emission data, including historical trends and annual values.

## Features

- **3D Globe Visualization**: Interactive 3D globe using Plotly's orthographic projection
- **Color-Coded Countries**: Countries are colored based on their CO₂ emission levels (green = low, red = high)
- **Interactive Click Events**: Click on any country to view detailed information
- **Historical Data**: View annual CO₂ emission values from 1750 to present
- **Trend Analysis**: See emission trends (increasing/decreasing) for each country
- **Year Slider**: Navigate through different years to see how emissions have changed over time
- **Trend Charts**: Visual charts showing emission trends for selected countries

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### 1. Prepare data (first run only)

The app stores all emissions data locally under the `data/` directory. Populate or refresh the dataset with:
```bash
python prepare_data.py
```
This step downloads the latest Our World in Data CO₂ dataset, converts it into the app's format, and saves both the raw and processed JSON files locally for offline use.

### 2. Start the application

Run the application:
```bash
python app.py
```

## Data Sources

- **Annual Historical Data**: Our World in Data (OWID) - CO₂ emissions dataset
  - Stored locally in `data/owid_co2_raw.json`
  - Processed country-level metrics cached in `data/emissions_processed.json`

## How It Works

1. **Data Fetching**: The `data_fetcher.py` module fetches CO₂ emissions data from Our World in Data
2. **Data Processing & Persistence**: Country data is processed, then saved to `data/emissions_processed.json` for reuse
3. **Visualization**: The `globe_visualizer.py` module creates the 3D globe using Plotly
4. **Interactivity**: Dash framework handles user interactions (clicks, slider changes)

## Project Structure

```
carbon_globe/
├── app.py                 # Main Dash application
├── data_fetcher.py        # Data fetching and processing
├── globe_visualizer.py    # Globe visualization logic
├── prepare_data.py        # CLI to download & cache data locally
├── data/                  # Stored raw & processed emission datasets
├── Procfile               # Production start command (Render/Heroku)
├── render.yaml            # Render deployment blueprint
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Features in Detail

### Globe Visualization
- Uses Plotly's choropleth map with orthographic projection for 3D globe effect
- Countries colored on a Red-Yellow-Green scale based on emission levels
- Interactive rotation and zoom capabilities

### Country Information Panel
When you click a country, you'll see:
- Latest emission data (year and value)
- Trend indicator (increasing/decreasing)
- Historical range (min/max emissions)
- Data coverage information
- Interactive trend chart

### Year Navigation
- Use the slider to navigate through different years
- Globe updates in real-time to show emissions for the selected year
- Historical data available from 1750 onwards

## Future Enhancements

- Near-real-time estimates from Carbon Monitor API
- Daily emission estimates
- Comparison mode (compare multiple countries)
- Export functionality for data and charts
- Additional emission metrics (per capita, per GDP, etc.)


## License

This project uses data from Our World in Data, which is available under the Creative Commons BY license.

