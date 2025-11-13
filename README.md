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

Then open your web browser and navigate to:
```
http://127.0.0.1:8050
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

## Deployment

You can host the globe publicly using a free Python web service such as [Render](https://render.com/), GitHub as the source of truth, and Gunicorn as the production server.

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Add carbon emissions globe"
git branch -M main
git remote add origin https://github.com/<your-user>/carbon-globe.git
git push -u origin main
```

### 2. Deploy on Render (Free Web Service)

1. Create a free Render account and click **New > Web Service**.
2. Connect your GitHub repository and choose it.
3. Render auto-detects the Python environment using `render.yaml`. If not, set:
   - **Environment**: Python
   - **Build command**: `pip install -r requirements.txt`
   - **Start command**: `python prepare_data.py && gunicorn app:server --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
4. Deploy. Render will build the container, run `prepare_data.py` (downloading the latest dataset into the ephemeral `data/` directory), and start the Dash app via Gunicorn.
5. When the service turns green, copy the public URL and share it.

Render keeps the app running 24/7 on the free plan (it may sleep after inactivity but auto-resumes on the next request). To refresh the dataset, redeploy or trigger a manual restart.

### Alternative Hosts

- **Railway / Fly.io / Heroku**: Use the provided `Procfile` (`web: python prepare_data.py && gunicorn app:server --bind 0.0.0.0:$PORT --workers 2 --timeout 120`). Configure their dashboards to run the same start command.
- **Vercel / Netlify**: Better suited for static or Node-based projects. They do not natively run long-lived Python Dash servers without serverless workarounds. Prefer a dedicated Python host.

## Offline / Air-gapped Usage

1. Connect to the internet and run `python prepare_data.py` to download the latest dataset.
2. Copy the project (including the `data/` directory) to the offline machine.
3. Install requirements and launch the app with `python app.py`.

## License

This project uses data from Our World in Data, which is available under the Creative Commons BY license.

