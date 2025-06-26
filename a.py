import requests
from datetime import datetime, timedelta, timezone

# Calculate 9 days ago (UTC)
now = datetime.now(timezone.utc)
nine_days_ago = now - timedelta(days=14)
nine_days_str = nine_days_ago.strftime('%Y-%m-%dT%H:%M:%S')

# Coordinates for within_box() spatial filter
north = 41.94775059922128
east = -87.65116121064099
south = 41.9400173076878
west = -87.68954611946626

# Build SOQL WHERE clause
where_clause = (
    f"within_box(location, {north}, {east}, {south}, {west}) "
    f"AND date >= '{nine_days_str}'"
)

# API endpoint
base_url = "https://data.cityofchicago.org/resource/ijzp-q8t2.json"

# Query parameters
params = {
    "$where": where_clause,
    "$order": "date DESC",
    "$limit": 1000  # adjust as needed
}

# Make the request
response = requests.get(base_url, params=params)
data = response.json()
