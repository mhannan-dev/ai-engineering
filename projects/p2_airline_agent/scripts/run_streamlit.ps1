# One-click execution script for the Streamlit Airline Agent.
Write-Host "Starting Airline Customer Support Agent..." -ForegroundColor Cyan

# Set Python path to include src directory
$env:PYTHONPATH = "src"

# Launch Streamlit app
streamlit run src/airline_agent/ui/app.py
