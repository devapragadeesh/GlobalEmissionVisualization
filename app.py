"""
Main application for the Interactive 3D Carbon Emissions Globe.
Uses Dash for web interactivity with Plotly globe.
"""
import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import json
from data_fetcher import EmissionsDataFetcher
from globe_visualizer import GlobeVisualizer


# Initialize the app
app = dash.Dash(
    __name__,
    meta_tags=[
        {
            'name': 'viewport',
            'content': 'width=device-width, initial-scale=1, maximum-scale=1'
        }
    ]
)
app.title = "Carbon Emissions Globe"
server = app.server

# Fetch and process data
print("Loading emissions data...")
fetcher = EmissionsDataFetcher()
emissions_data = fetcher.get_all_countries_data()
visualizer = GlobeVisualizer(emissions_data)

# Get current year for display
current_year = visualizer.current_year

# Create initial globe
initial_fig = visualizer.create_globe(current_year)

# App layout
app.layout = html.Div([
    html.Div([
        html.H1("🌍 Interactive Carbon Emissions Globe"),
        html.Div([
            html.Label("Select Year:", className='slider-label'),
            dcc.Slider(
                id='year-slider',
                min=min([min(data['years']) for data in emissions_data.values()]),
                max=current_year,
                value=current_year,
                marks={year: str(year) for year in range(
                    min([min(data['years']) for data in emissions_data.values()]),
                    current_year + 1,
                    10
                )},
                step=1,
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], className='controls-bar'),
    ], className='app-header'),
    
    html.Div([
        html.Div([
            dcc.Graph(
                id='globe-graph',
                figure=initial_fig,
                className='globe-graph',
                config={'displayModeBar': True}
            )
        ], className='globe-section'),
        
        html.Div([
            html.Div(id='country-info', children=[
                html.H3("Click on a country to view details", className='placeholder-text')
            ], className='info-card'),
            
            html.Div(id='country-trend-chart', className='trend-card')
        ], className='sidebar-section')
    ], className='content-wrapper'),
    
    html.Div([
        html.P("Data source: Our World in Data (OWID)", className='footer-note')
    ], className='app-footer'),
    
    # Store for clicked country
    dcc.Store(id='clicked-country-store', data=None),
    dcc.Store(id='globe-rotation-store', data={'lon': 0, 'lat': 0})
], className='app-container')


@app.callback(
    [Output('globe-graph', 'figure'),
     Output('clicked-country-store', 'data'),
     Output('globe-rotation-store', 'data')],
    [Input('year-slider', 'value'),
     Input('globe-graph', 'clickData'),
     Input('globe-graph', 'relayoutData')],
    [State('clicked-country-store', 'data'),
     State('globe-rotation-store', 'data')]
)
def update_globe(year, click_data, relayout_data, stored_country, stored_rotation):
    """Update globe when year changes or country is clicked."""
    # Track the globe rotation to avoid snapping back to default view
    rotation = stored_rotation or {'lon': 0, 'lat': 0}
    if relayout_data:
        # Handle both flattened and nested keys
        lon = (
            relayout_data.get('geo.projection.rotation.lon')
            or relayout_data.get('lon')
        )
        lat = (
            relayout_data.get('geo.projection.rotation.lat')
            or relayout_data.get('lat')
        )
        if 'geo' in relayout_data and isinstance(relayout_data['geo'], dict):
            proj = relayout_data['geo'].get('projection', {})
            rot = proj.get('rotation', {})
            lon = rot.get('lon', lon)
            lat = rot.get('lat', lat)
        rotation = {
            'lon': rotation.get('lon', 0) if lon is None else lon,
            'lat': rotation.get('lat', 0) if lat is None else lat
        }
    
    # Update globe for new year and maintain rotation
    fig = visualizer.create_globe(year, rotation=rotation)
    
    # Handle country click
    clicked_country = stored_country  # Keep previous selection if no new click
    if click_data and 'points' in click_data:
        point = click_data['points'][0]
        if 'customdata' in point and len(point['customdata']) >= 1:
            country_name = point['customdata'][0]
            # Find country code from name
            for code, data in emissions_data.items():
                if data['country_name'] == country_name:
                    clicked_country = code
                    break
        elif 'location' in point:
            # Try to find by location code
            location_code = point['location']
            for code, data in emissions_data.items():
                iso3_code = visualizer.country_codes_map.get(code, code.replace('OWID_', ''))
                if iso3_code == location_code:
                    clicked_country = code
                    break
    
    return fig, clicked_country, rotation


@app.callback(
    [Output('country-info', 'children'),
     Output('country-trend-chart', 'children')],
    [Input('clicked-country-store', 'data')]
)
def update_country_info(country_code):
    """Update country information panel when a country is clicked."""
    if country_code is None or country_code not in emissions_data:
        return html.H3(
            "Click on a country to view details",
            className='placeholder-text'
        ), None
    
    data = emissions_data[country_code]
    
    # Create info panel
    info_panel = html.Div([
        html.H2(data['country_name'], className='info-title'),
        html.Hr(),
        html.Div([
            html.H3("Latest Data", className='section-heading'),
            html.P(f"Year: {data['latest_year']}", className='muted-text'),
            html.P([
                html.Span(f"{data['latest_emission']:.2f}", className='metric-value'),
                html.Span(" Million Tonnes CO₂", className='metric-suffix')
            ], className='metric-row')
        ], className='info-block'),
        html.Div([
            html.H3("Trend", className='section-heading'),
            html.P(
                data['trend'].capitalize(),
                className=f"trend-label trend-{data['trend']}"
            )
        ], className='info-block'),
        html.Div([
            html.H3("Historical Range", className='section-heading'),
            html.P([
                f"Maximum: {data['max_emission']:.2f} Million Tonnes",
                html.Br(),
                f"Minimum: {data['min_emission']:.2f} Million Tonnes"
            ], className='muted-text')
        ], className='info-block'),
        html.Div([
            html.H3("Data Coverage", className='section-heading'),
            html.P(f"{len(data['years'])} years of data", className='muted-text'),
            html.P(
                f"From {min(data['years'])} to {max(data['years'])}",
                className='muted-subtext'
            )
        ], className='info-block')
    ], className='info-panel')
    
    # Create trend chart
    trend_chart = dcc.Graph(
        figure={
            'data': [{
                'x': data['years'],
                'y': data['emissions'],
                'type': 'scatter',
                'mode': 'lines+markers',
                'line': {'color': '#3498db', 'width': 3},
                'marker': {'size': 6, 'color': '#2980b9'},
                'name': 'CO₂ Emissions'
            }],
            'layout': {
                'title': f'Emission Trend Over Time',
                'xaxis': {'title': 'Year'},
                'yaxis': {'title': 'Million Tonnes CO₂'},
                'hovermode': 'closest',
                'plot_bgcolor': '#ffffff',
                'paper_bgcolor': '#ffffff',
                'height': 320,
                'margin': dict(l=40, r=20, t=60, b=50)
            }
        },
        config={'displayModeBar': False, 'responsive': True},
        style={'width': '100%', 'height': '100%'},
        className='trend-graph'
    )
    
    return info_panel, trend_chart


if __name__ == '__main__':
    print("\n" + "="*50)
    print("Carbon Emissions Globe Application")
    print("="*50)
    print(f"\nLoaded data for {len(emissions_data)} countries")
    try:
        min_year = min([min(data['years']) for data in emissions_data.values()])
        print(f"Data range: {min_year} - {current_year}")
    except:
        print(f"Data range: up to {current_year}")
    print("\nStarting server...")
    print("Open your browser to http://127.0.0.1:8050")
    print("="*50 + "\n")
    
    try:
        app.run(debug=True, port=8050, host='127.0.0.1')
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()

