# Supervisor - Weather View

## Overview
Display weather information for assigned site locations and allow searching for any location to take quick action.

## Layout
- Tab navigation at the top (Members, Events, Weather, Requests)
- Search bar at the top for location search
- Main content area with weather data table

## Table Columns

### Assigned Sites Weather
| Column | Description | Data Type |
|--------|-------------|-----------|
| Site Name | Name of the site | String |
| Location | City, State, Country | String |
| Coordinates | Latitude, Longitude | Object |
| Current Temp | Current temperature | Number (°C/°F) |
| Feels Like | Feels like temperature | Number (°C/°F) |
| Weather Condition | Sunny, Rainy, Cloudy, etc. | String |
| Humidity | Humidity percentage | Number (%) |
| Wind Speed | Wind speed | Number (km/h) |
| Wind Direction | Wind direction | String (N, S, E, W, etc.) |
| Visibility | Visibility distance | Number (km) |
| UV Index | UV index level | Number |
| Air Quality | Air quality index | Number/Enum |
| Precipitation | Rain/Snow amount | Number (mm) |
| Forecast | Short forecast summary | String |
| Last Updated | Last update timestamp | DateTime |
| Alert | Weather alerts (if any) | String/Array |

### Actions Column
| Action | Description |
|---------|-------------|
| View Details | Opens modal with detailed weather info |
| Quick Action | Opens action menu for the site |

## Location Search
- Search bar at the top of the page
- Autocomplete suggestions
- Search by:
  - City name
  - Zip/Postal code
  - Coordinates
  - Site name

## Search Results Table
When searching for a location, display:
| Column | Description | Data Type |
|--------|-------------|-----------|
| Location Name | Searched location | String |
| Current Temp | Current temperature | Number |
| Weather Condition | Current weather | String |
| Forecast | 5-day forecast summary | String |
| Alerts | Active weather alerts | String/Array |
| Actions | Quick action buttons | - |

## Quick Actions
For any location (assigned or searched):
- **Send Alert**: Send weather alert to members at location
- **Schedule Adjustment**: Adjust work schedules based on weather
- **Site Inspection**: Request site inspection
- **Notify Members**: Send notification to members
- **Create Task**: Create a task related to weather condition

## Weather Details Modal
- Current conditions detailed view
- Hourly forecast (24 hours)
- 7-day forecast
- Historical data
- Weather alerts and warnings
- Radar map (if available)
- Action buttons

## UI Components
- Tab navigation
- Search bar with autocomplete
- Data table with sorting
- Weather icons/visual indicators
- Alert badges
- Modal for detailed weather info
- Action dropdown menu
- Refresh button for live data
- Temperature unit toggle (°C/°F)

## Weather Alert Indicators
- Color-coded rows based on severity:
  - Green: Normal conditions
  - Yellow: Caution (light rain, moderate wind)
  - Orange: Warning (heavy rain, strong wind)
  - Red: Severe (storm, extreme conditions)

## API Endpoints (Tentative)

**Authentication**: All endpoints require JWT authentication. Supervisor ID is extracted from the token, no need to pass in payload.

- `GET /api/supervisor/weather/sites` - Get weather for sites assigned to supervisor's members
  - Query params: `?alert_level=warning&sort=temperature&unit=celsius`
- `GET /api/supervisor/weather/location` - Get weather for specific location
  - Query params: `?lat=xxx&lng=yyy` or `?city=CityName` or `?zip=12345`
- `GET /api/supervisor/weather/search` - Search locations for weather
  - Query params: `?q=search_term`
- `POST /api/supervisor/weather/alert` - Send weather alert to members at location
  - Body: `{ location: "SiteName", alert_type: "warning", message: "Alert text", urgency: "high" }`
- `POST /api/supervisor/weather/action` - Take quick action based on weather
  - Body: `{ action_type: "schedule_adjustment|notify_members|site_inspection", location: "SiteName", details: "..." }`
