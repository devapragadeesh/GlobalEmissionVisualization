"""
Simple launcher script for the Carbon Emissions Globe application.
"""
if __name__ == '__main__':
    from app import app
    app.run_server(debug=True, port=8050)

