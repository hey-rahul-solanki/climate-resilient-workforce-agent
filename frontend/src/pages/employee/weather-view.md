# Employee - Weather View

## Overview
Display weather information for all assigned sites and allow searching for any location to check conditions and plan work accordingly.

## Layout
- Tab navigation at the top (Assignments, Weather)
- Search bar at the top for location search
- Main content area with weather data table

## Table Columns

### Assigned Sites Weather
| Column | Description | Data Type |
|--------|-------------|-----------|
| Site Name | Name of the site | String |
| Location | City, State, Country | String |
| Assignment ID | Related assignment ID | String |
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
| Advisory | Safety advisory based on conditions | String |
| Alert Level | Normal/Caution/Warning/Severe | Enum |
| Work Suitability | Good/Acceptable/Poor/Unsafe | Enum |
| Last Updated | Last update timestamp | DateTime |

### Actions Column
| Action | Description |
|---------|-------------|
| View Details | Opens modal with detailed weather info |
| View Best Times | Opens modal showing optimal work times |
| Share Concern | Share weather concern with supervisor |
| Check Safety Guidelines | View safety guidelines for conditions |

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
| Advisory | Current advisory | String |
| Work Suitability | Is it suitable for work | Enum |
| Forecast | 5-day forecast summary | String |
| Best Work Times | Recommended time slots | Array |
| Actions | Quick action buttons | - |

## Weather Advisory Levels
Color-coded advisory levels:
- **Green (Normal)**: Safe working conditions
  - Temperature: 15-30°C
  - Wind: < 20 km/h
  - Precipitation: 0-10%
  - Visibility: > 5 km

- **Yellow (Caution)**: Proceed with caution
  - Temperature: 10-15°C or 30-35°C
  - Wind: 20-30 km/h
  - Precipitation: 10-30%
  - Visibility: 2-5 km

- **Orange (Warning)**: Consider rescheduling
  - Temperature: 5-10°C or 35-40°C
  - Wind: 30-50 km/h
  - Precipitation: 30-60%
  - Visibility: 1-2 km

- **Red (Severe)**: Avoid work
  - Temperature: < 5°C or > 40°C
  - Wind: > 50 km/h
  - Precipitation: > 60%
  - Visibility: < 1 km
  - Storms, extreme conditions

## Work Suitability Assessment
| Level | Description | Recommended Action |
|-------|-------------|---------------------|
| Good | Optimal conditions | Proceed as planned |
| Acceptable | Minor issues | Proceed with precautions |
| Poor | Challenging conditions | Consider rescheduling |
| Unsafe | Dangerous conditions | Do not work, report immediately |

## Best Times Modal

### Overview
Shows optimal work time windows based on weather forecast for a specific location.

### Display
- **Weather Timeline**: Visual timeline showing weather conditions throughout the day
- **Recommended Time Slots**: Highlighted optimal time windows
- **Hourly Breakdown**: Detailed weather conditions for each hour
- **Work Suitability Score**: Numerical score (1-10) for each time slot

### Time Slot Information
- Temperature range
- Precipitation probability
- Wind conditions
- UV index
- Visibility
- Overall recommendation

### Actions
- **Share with Supervisor**: Send recommended times to supervisor
- **Request Schedule Change**: Request to move assignment to optimal time
- **Add to Calendar**: Add optimal time to personal calendar

## Weather Details Modal
- Current conditions detailed view
- Hourly forecast (24 hours)
- 7-day forecast
- Historical data
- Weather alerts and warnings
- Radar map (if available)
- Safety guidelines for current conditions
- Recommended PPE (Personal Protective Equipment)
- Work suitability explanation

## Share Concern with Supervisor

### Form
- **Location**: Pre-filled site/location
- **Weather Condition**: Pre-filled current condition
- **Concern Type**: Dropdown (Too hot, Too cold, Rain expected, Windy, Poor visibility, Other)
- **Message**: Text area for detailed concern
- **Affected Assignment**: Select assignment if applicable
- **Suggested Action**: Optional (Reschedule, Cancel, Add safety measures)
- **Urgency**: Urgent/High/Medium/Low

### Submission
- Sends notification to supervisor
- Creates a request in supervisor's requests view
- Provides confirmation to employee

## Safety Guidelines Modal
Display safety guidelines based on current weather conditions:
- PPE requirements
- Work duration limits
- Break frequency recommendations
- Hydration guidelines
- Emergency procedures
- Contact information for site supervisor

## UI Components
- Tab navigation
- Search bar with autocomplete
- Data table with sorting
- Weather icons/visual indicators
- Color-coded advisory badges
- Work suitability badges
- Modal for detailed weather info
- Modal for best times analysis
- Modal for share concern form
- Modal for safety guidelines
- Action dropdown menu
- Refresh button for live data
- Temperature unit toggle (°C/°F)

## Filtering Options
- Filter by site
- Filter by work suitability
- Filter by alert level
- Filter by date range

## Notifications
- Weather alert notification for assigned sites
- Severe weather warning
- Advisory change notification
- Supervisor response to shared concern

## API Endpoints (Tentative)

**Authentication**: All endpoints require JWT authentication. Employee ID is extracted from the token, no need to pass in payload.

- `GET /api/employee/weather/sites` - Get weather for sites assigned to employee
  - Query params: `?alert_level=warning&work_suitability=good&sort=temperature&unit=celsius`
- `GET /api/employee/weather/location` - Get weather for specific location
  - Query params: `?lat=xxx&lng=yyy` or `?city=CityName` or `?zip=12345`
- `GET /api/employee/weather/search` - Search locations for weather
  - Query params: `?q=search_term`
- `GET /api/employee/weather/location/best-times` - Get optimal work times for a location
  - Query params: `?lat=xxx&lng=yyy` or `?city=CityName` or `?zip=12345&date=2024-01-15`
- `POST /api/employee/weather/share-concern` - Share weather concern with supervisor
  - Body: `{ location: "SiteName or coordinates", weather_condition: "current_condition", concern_type: "too_hot|too_cold|rain_expected|windy|poor_visibility|other", message: "Concern details", affected_assignment: "assignment_id", suggested_action: "reschedule|cancel|add_safety_measures", urgency: "high" }`
- `GET /api/employee/weather/safety-guidelines` - Get safety guidelines for current weather conditions
  - Query params: `?temperature=25&wind_speed=10&precipitation=20&visibility=5`
