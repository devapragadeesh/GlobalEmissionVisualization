"""Test script to check if the app can start."""
import sys
print("Testing imports...")
try:
    from data_fetcher import EmissionsDataFetcher
    from globe_visualizer import GlobeVisualizer
    import dash
    print("✓ All imports successful")
except Exception as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

print("\nTesting data fetcher...")
try:
    fetcher = EmissionsDataFetcher()
    print("✓ Data fetcher created")
    print("Fetching data (this may take a moment)...")
    data = fetcher.get_all_countries_data()
    print(f"✓ Data fetched: {len(data)} countries")
except Exception as e:
    print(f"✗ Data fetch error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nTesting app initialization...")
try:
    from app import app
    print("✓ App imported successfully")
    print("\n" + "="*50)
    print("App is ready! Starting server...")
    print("="*50 + "\n")
    app.run_server(debug=True, port=8050, host='127.0.0.1')
except Exception as e:
    print(f"✗ App error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

