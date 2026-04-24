"""
Main application for the Interactive 3D Carbon Emissions Globe.
Uses Dash for web interactivity with Plotly globe.
"""
import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import json
from dash.exceptions import PreventUpdate
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
min_year = min([min(data['years']) for data in emissions_data.values()])

# Create initial globe
initial_fig = visualizer.create_globe(current_year)


def build_year_marks(start_year: int, end_year: int) -> dict[int, str]:
    """Create a compact set of slider marks suitable for mobile screens."""
    if start_year >= end_year:
        return {start_year: str(start_year)}

    anchors = {start_year, end_year}

    # Add notable historical anchors if they fall within the range
    for anchor in (1800, 1850, 1900, 1950, 2000, 2010, 2020):
        if start_year < anchor < end_year:
            anchors.add(anchor)

    span = end_year - start_year
    target_marks = 8
    step = max(10, int(span / (target_marks - 1)))
    # Round to nearest 5 for cleaner labels
    step = ((step + 4) // 5) * 5

    first_step = ((start_year + step - 1) // step) * step
    for year in range(first_step, end_year, step):
        anchors.add(year)

    return {year: str(year) for year in sorted(anchors)}

# App layout
app.layout = html.Div([
    html.Div([
        html.H1("🌍 Interactive Carbon Emissions Globe"),
        html.P(
            "Explore historical CO₂ emissions by country in a real-time interactive world view",
            className='header-subtitle'
        ),
        html.Div([
            html.Label("Select Year:", className='slider-label'),
            dcc.Slider(
                id='year-slider',
                min=min_year,
                max=current_year,
                value=current_year,
                marks=build_year_marks(min_year, current_year),
                step=1,
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], className='controls-bar'),
        html.Div([
            html.Div(id='year-pill', className='status-pill'),
            html.Div(id='selected-country-pill', className='status-pill status-pill-secondary')
        ], className='status-pills-row'),
        html.Div([
            html.Button("▶ Play timeline", id='play-button', n_clicks=0, className='action-button primary-action'),
            html.Div([
                html.Label("Speed", className='speed-label'),
                dcc.Dropdown(
                    id='play-speed-dropdown',
                    options=[
                        {'label': '0.5×', 'value': 0.5},
                        {'label': '1×', 'value': 1},
                        {'label': '2×', 'value': 2},
                        {'label': '4×', 'value': 4},
                    ],
                    value=1,
                    clearable=False,
                    searchable=False,
                    className='speed-dropdown'
                )
            ], className='speed-control-group'),
            html.Button("🧭 Reset globe view", id='reset-view-button', n_clicks=0, className='action-button secondary-action')
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
    dcc.Store(id='globe-rotation-store', data={'lon': 0, 'lat': 0}),
    dcc.Interval(id='year-play-interval', interval=1200, n_intervals=0, disabled=True)
], className='app-container')


@app.callback(
    [Output('year-play-interval', 'disabled'),
     Output('play-button', 'children')],
    [Input('play-button', 'n_clicks')],
    [State('year-play-interval', 'disabled')]
)
def toggle_timeline_playback(n_clicks, is_disabled):
    """Toggle year slider autoplay."""
    if not n_clicks:
        return True, "▶ Play timeline"

    should_play = is_disabled
    return (not should_play), ("⏸ Pause timeline" if should_play else "▶ Play timeline")


@app.callback(
    Output('year-slider', 'value'),
    [Input('year-play-interval', 'n_intervals')],
    [State('year-play-interval', 'disabled'),
     State('year-slider', 'value')]
)
def autoplay_year_slider(_n_intervals, is_disabled, current_value):
    """Advance year during autoplay."""
    if is_disabled:
        raise PreventUpdate

    if current_value is None:
        return min_year

    return min_year if current_value >= current_year else current_value + 1


@app.callback(
    Output('year-play-interval', 'interval'),
    [Input('play-speed-dropdown', 'value')]
)
def update_timeline_speed(speed_value):
    """Update autoplay speed based on selected multiplier."""
    base_interval_ms = 1200
    speed = float(speed_value or 1)
    if speed <= 0:
        speed = 1
    return max(250, int(base_interval_ms / speed))


@app.callback(
    [Output('globe-graph', 'figure'),
     Output('clicked-country-store', 'data'),
     Output('globe-rotation-store', 'data'),
     Output('year-pill', 'children'),
     Output('selected-country-pill', 'children')],
    [Input('year-slider', 'value'),
     Input('globe-graph', 'clickData'),
     Input('globe-graph', 'relayoutData'),
     Input('reset-view-button', 'n_clicks')],
    [State('clicked-country-store', 'data'),
     State('globe-rotation-store', 'data')]
)
def update_globe(year, click_data, relayout_data, _reset_clicks, stored_country, stored_rotation):
    """Update globe when year changes or country is clicked."""
    triggered_id = dash.ctx.triggered_id

    # Track the globe rotation to avoid snapping back to default view
    rotation = stored_rotation or {'lon': 0, 'lat': 0}
    if triggered_id == 'reset-view-button':
        rotation = {'lon': 0, 'lat': 0}
    elif relayout_data:
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

    selected_country_name = "No country selected"
    if clicked_country and clicked_country in emissions_data:
        selected_country_name = emissions_data[clicked_country]['country_name']

    return (
        fig,
        clicked_country,
        rotation,
        f"Year in focus: {year}",
        f"Selected: {selected_country_name}"
    )


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
                'line': {'color': '#6b7cff', 'width': 3, 'shape': 'spline', 'smoothing': 0.9},
                'marker': {'size': 6, 'color': '#9a8cff', 'line': {'color': '#ffffff', 'width': 1}},
                'fill': 'tozeroy',
                'fillcolor': 'rgba(107, 124, 255, 0.15)',
                'name': 'CO₂ Emissions'
            }],
            'layout': {
                'title': f'Emission Trend Over Time',
                'xaxis': {'title': 'Year'},
                'yaxis': {'title': 'Million Tonnes CO₂'},
                'hovermode': 'closest',
                'plot_bgcolor': 'rgba(246, 248, 255, 1)',
                'paper_bgcolor': 'rgba(0,0,0,0)',
                'hoverlabel': {'bgcolor': '#111827', 'font': {'color': '#f9fafb'}},
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

