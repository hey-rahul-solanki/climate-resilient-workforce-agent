# Configuration Guide for Static/Dynamic Modes

## Overview

The application is designed to work in **static mode** by default (no external dependencies), with optional **dynamic mode** enabled via environment variables for:
- Weather APIs (Open-Meteo, Meteor)
- Location services (OpenStreetMap)
- AI services (Gemini, GCP)
- Any internet-dependent features

---

## Architecture: Static vs Dynamic

### Static Mode (Default)
- ✅ No internet connection required
- ✅ No API keys needed
- ✅ Uses fixture/mock data
- ✅ Pre-configured locations
- ✅ Pre-configured weather data
- ✅ Fully functional for demo

### Dynamic Mode (Optional)
- ✅ Live weather data from APIs
- ✅ Real-time geocoding
- ✅ AI-powered suggestions
- ✅ Cloud integration
- ⚠️ Requires internet connection
- ⚠️ Requires API keys

---

## Environment Variables

### Core Configuration

```bash
# Application Mode
WORKFORCE_MODE=static              # Options: static, dynamic
                                  # Default: static

# Weather Configuration
WORKFORCE_WEATHER_SOURCE=fixture   # Options: fixture, open-meteo, meteor
                                  # Default: fixture

WORKFORCE_FIXTURE_PATH=./data/fixtures/weather.json
                                  # Path to static weather data file

# Open-Meteo (Dynamic Mode)
WORKFORCE_OPEN_METEO_BASE_URL=https://api.open-meteo.com/v1/forecast
WORKFORCE_OPEN_METEO_TIMEOUT=10.0

# Meteor (Dynamic Mode)
WORKFORCE_METEOR_API_KEY=your_meteor_api_key
WORKFORCE_METEOR_BASE_URL=https://api.meteor.com

# Location Configuration
WORKFORCE_LOCATION_SOURCE=static   # Options: static, osm
                                  # Default: static

# OpenStreetMap (Dynamic Mode)
WORKFORCE_OSM_NOMINATIM_BASE=https://nominatim.openstreetmap.org
WORKFORCE_OSM_TIMEOUT=10.0
WORKFORCE_OSM_RATE_LIMIT=1.0

# AI Configuration
WORKFORCE_AI_SOURCE=rule_based    # Options: rule_based, gemini
                                  # Default: rule_based

# Gemini (Dynamic Mode)
WORKFORCE_GEMINI_API_KEY=your_gemini_api_key
WORKFORCE_GEMINI_MODEL=gemini-pro
WORKFORCE_GEMINI_TIMEOUT=30.0

# GCP Configuration (Dynamic Mode)
WORKFORCE_GCP_PROJECT_ID=your_project_id
WORKFORCE_GCP_LOCATION=us-central1
WORKFORCE_GCP_SERVICE_ACCOUNT_KEY_PATH=./gcp-key.json

# Database Configuration
WORKFORCE_DATABASE_URL=postgresql://user:pass@localhost/db
WORKFORCE_USE_STATIC_DB=false      # Use SQLite for static mode

# API Configuration
WORKFORCE_API_HOST=0.0.0.0
WORKFORCE_API_PORT=8000
WORKFORCE_API_CORS_ORIGINS=http://localhost:5173
```

---

## Configuration Implementation

### 1. Settings Class (config.py)

```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Application Mode
    mode: str = "static"  # static or dynamic

    # Weather Configuration
    weather_source: str = "fixture"  # fixture, open-meteo, meteor
    fixture_path: str = "./data/fixtures/weather.json"

    # Open-Meteo
    open_meteo_base_url: str = "https://api.open-meteo.com/v1/forecast"
    open_meteo_timeout: float = 10.0

    # Meteor
    meteor_api_key: Optional[str] = None
    meteor_base_url: str = "https://api.meteor.com"

    # Location Configuration
    location_source: str = "static"  # static, osm

    # OpenStreetMap
    osm_nominatim_base: str = "https://nominatim.openstreetmap.org"
    osm_timeout: float = 10.0
    osm_rate_limit: float = 1.0

    # AI Configuration
    ai_source: str = "rule_based"  # rule_based, gemini

    # Gemini
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-pro"
    gemini_timeout: float = 30.0

    # GCP
    gcp_project_id: Optional[str] = None
    gcp_location: str = "us-central1"
    gcp_service_account_key_path: Optional[str] = None

    # Database
    database_url: str = "postgresql://user:pass@localhost/db"
    use_static_db: bool = False

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_cors_origins: str = "http://localhost:5173"

    class Config:
        env_prefix = "WORKFORCE_"
        env_file = ".env"

settings = Settings()
```

### 2. Weather Client Factory

```python
from workforce_agent.config import settings

class WeatherClientFactory:
    @staticmethod
    def get_client():
        if settings.weather_source == "fixture":
            return FixtureWeatherClient(settings.fixture_path)
        elif settings.weather_source == "open-meteo":
            return OpenMeteoClient(settings.open_meteo_base_url)
        elif settings.weather_source == "meteor":
            return MeteorClient(settings.meteor_base_url, settings.meteor_api_key)
        else:
            raise ValueError(f"Unknown weather source: {settings.weather_source}")
```

### 3. Location Service Factory

```python
from workforce_agent.config import settings

class LocationServiceFactory:
    @staticmethod
    def get_service():
        if settings.location_source == "static":
            return StaticLocationService()
        elif settings.location_source == "osm":
            return OSMLocationService(settings.osm_nominatim_base)
        else:
            raise ValueError(f"Unknown location source: {settings.location_source}")
```

### 4. AI Service Factory

```python
from workforce_agent.config import settings

class AIServiceFactory:
    @staticmethod
    def get_service():
        if settings.ai_source == "rule_based":
            return RuleBasedAIService()
        elif settings.ai_source == "gemini":
            return GeminiAIService(settings.gemini_api_key, settings.gemini_model)
        else:
            raise ValueError(f"Unknown AI source: {settings.ai_source}")
```

---

## Static Data Files

### 1. Weather Fixtures

**File:** `data/fixtures/weather.json`

```json
{
  "VAD-PLANT-01": {
    "location": "Vadodara, Gujarat, India",
    "latitude": 22.3072,
    "longitude": 73.1812,
    "timezone": "Asia/Kolkata",
    "hourly": [
      {
        "time": "2024-01-15T06:00:00Z",
        "temperature_c": 28.0,
        "precipitation_percent": 10.0,
        "wind_speed_kmh": 8.0,
        "visibility_km": 10.0,
        "humidity_percent": 60.0
      },
      {
        "time": "2024-01-15T14:00:00Z",
        "temperature_c": 42.0,
        "precipitation_percent": 5.0,
        "wind_speed_kmh": 10.0,
        "visibility_km": 10.0,
        "humidity_percent": 60.0
      },
      {
        "time": "2024-01-15T18:00:00Z",
        "temperature_c": 32.0,
        "precipitation_percent": 10.0,
        "wind_speed_kmh": 8.0,
        "visibility_km": 10.0,
        "humidity_percent": 55.0
      }
    ]
  },
  "MUM-SITE-01": {
    "location": "Mumbai, Maharashtra, India",
    "latitude": 19.0760,
    "longitude": 72.8777,
    "timezone": "Asia/Kolkata",
    "hourly": [
      {
        "time": "2024-01-15T06:00:00Z",
        "temperature_c": 26.0,
        "precipitation_percent": 15.0,
        "wind_speed_kmh": 12.0,
        "visibility_km": 8.0,
        "humidity_percent": 70.0
      },
      {
        "time": "2024-01-15T14:00:00Z",
        "temperature_c": 38.0,
        "precipitation_percent": 45.0,
        "wind_speed_kmh": 15.0,
        "visibility_km": 5.0,
        "humidity_percent": 75.0
      },
      {
        "time": "2024-01-15T18:00:00Z",
        "temperature_c": 30.0,
        "precipitation_percent": 20.0,
        "wind_speed_kmh": 10.0,
        "visibility_km": 8.0,
        "humidity_percent": 65.0
      }
    ]
  }
}
```

### 2. Static Locations

**File:** `data/fixtures/locations.json`

```json
{
  "VAD-PLANT-01": {
    "site_id": "VAD-PLANT-01",
    "name": "Vadodara Process Plant",
    "city": "Vadodara",
    "state": "Gujarat",
    "country": "India",
    "latitude": 22.3072,
    "longitude": 73.1812,
    "timezone": "Asia/Kolkata",
    "display_name": "Vadodara Process Plant, Vadodara, Gujarat, India"
  },
  "MUM-SITE-01": {
    "site_id": "MUM-SITE-01",
    "name": "Mumbai Industrial Site",
    "city": "Mumbai",
    "state": "Maharashtra",
    "country": "India",
    "latitude": 19.0760,
    "longitude": 72.8777,
    "timezone": "Asia/Kolkata",
    "display_name": "Mumbai Industrial Site, Mumbai, Maharashtra, India"
  }
}
```

---

## Switching Modes

### Static Mode (Default)

**.env file:**
```bash
WORKFORCE_MODE=static
WORKFORCE_WEATHER_SOURCE=fixture
WORKFORCE_LOCATION_SOURCE=static
WORKFORCE_AI_SOURCE=rule_based
```

**Behavior:**
- Uses fixture weather data
- Uses static location coordinates
- Uses rule-based AI logic
- No API calls
- No internet required

### Dynamic Mode with Open-Meteo

**.env file:**
```bash
WORKFORCE_MODE=dynamic
WORKFORCE_WEATHER_SOURCE=open-meteo
WORKFORCE_LOCATION_SOURCE=static
WORKFORCE_AI_SOURCE=rule_based
```

**Behavior:**
- Fetches live weather from Open-Meteo
- Uses static location coordinates
- Uses rule-based AI logic
- Requires internet for weather
- No API key required (Open-Meteo is free)

### Dynamic Mode with All Services

**.env file:**
```bash
WORKFORCE_MODE=dynamic
WORKFORCE_WEATHER_SOURCE=open-meteo
WORKFORCE_LOCATION_SOURCE=osm
WORKFORCE_AI_SOURCE=gemini
WORKFORCE_GEMINI_API_KEY=your_gemini_api_key
```

**Behavior:**
- Fetches live weather from Open-Meteo
- Uses OpenStreetMap for geocoding
- Uses Gemini AI for suggestions
- Requires internet
- Requires Gemini API key

---

## Implementation Strategy

### Phase 1: Static Mode (Current)
1. Implement with fixture data
2. Use static location coordinates
3. Use rule-based AI logic
4. No external dependencies
5. Fully functional demo

### Phase 2: Add Weather API (Optional)
1. Set `WORKFORCE_WEATHER_SOURCE=open-meteo`
2. Add Open-Meteo client
3. Test with live data
4. Fallback to fixture on error

### Phase 3: Add Location Service (Optional)
1. Set `WORKFORCE_LOCATION_SOURCE=osm`
2. Add OSM client
3. Test geocoding
4. Fallback to static on error

### Phase 4: Add AI Service (Optional)
1. Set `WORKFORCE_AI_SOURCE=gemini`
2. Add Gemini client
3. Test AI suggestions
4. Fallback to rule-based on error

### Phase 5: Add GCP (Optional)
1. Set GCP environment variables
2. Add GCP integration
3. Test cloud features
4. Fallback to local on error

---

## Error Handling & Fallbacks

### Weather Client Fallback

```python
class WeatherClientWithFallback:
    def __init__(self):
        self.primary_client = WeatherClientFactory.get_client()
        self.fallback_client = FixtureWeatherClient(settings.fixture_path)

    async def get_forecast(self, location_id, days):
        try:
            return await self.primary_client.get_forecast(location_id, days)
        except Exception as e:
            print(f"Primary weather client failed: {e}")
            print("Falling back to fixture data")
            return await self.fallback_client.get_forecast(location_id, days)
```

### Location Service Fallback

```python
class LocationServiceWithFallback:
    def __init__(self):
        self.primary_service = LocationServiceFactory.get_service()
        self.fallback_service = StaticLocationService()

    async def geocode(self, address):
        try:
            return await self.primary_service.geocode(address)
        except Exception as e:
            print(f"Primary location service failed: {e}")
            print("Falling back to static data")
            return await self.fallback_service.geocode(address)
```

---

## Environment File Templates

### .env.static (Default)

```bash
# Static Mode - No External Dependencies
WORKFORCE_MODE=static
WORKFORCE_WEATHER_SOURCE=fixture
WORKFORCE_FIXTURE_PATH=./data/fixtures/weather.json
WORKFORCE_LOCATION_SOURCE=static
WORKFORCE_AI_SOURCE=rule_based
WORKFORCE_USE_STATIC_DB=true
```

### .env.dynamic (With Open-Meteo)

```bash
# Dynamic Mode - Open-Meteo Weather
WORKFORCE_MODE=dynamic
WORKFORCE_WEATHER_SOURCE=open-meteo
WORKFORCE_OPEN_METEO_BASE_URL=https://api.open-meteo.com/v1/forecast
WORKFORCE_OPEN_METEO_TIMEOUT=10.0
WORKFORCE_LOCATION_SOURCE=static
WORKFORCE_AI_SOURCE=rule_based
```

### .env.full (All Services)

```bash
# Full Dynamic Mode - All Services
WORKFORCE_MODE=dynamic
WORKFORCE_WEATHER_SOURCE=open-meteo
WORKFORCE_OPEN_METEO_BASE_URL=https://api.open-meteo.com/v1/forecast
WORKFORCE_OPEN_METEO_TIMEOUT=10.0
WORKFORCE_LOCATION_SOURCE=osm
WORKFORCE_OSM_NOMINATIM_BASE=https://nominatim.openstreetmap.org
WORKFORCE_OSM_TIMEOUT=10.0
WORKFORCE_AI_SOURCE=gemini
WORKFORCE_GEMINI_API_KEY=your_gemini_api_key
WORKFORCE_GEMINI_MODEL=gemini-pro
WORKFORCE_GEMINI_TIMEOUT=30.0
WORKFORCE_GCP_PROJECT_ID=your_project_id
WORKFORCE_GCP_LOCATION=us-central1
WORKFORCE_GCP_SERVICE_ACCOUNT_KEY_PATH=./gcp-key.json
```

---

## Testing Both Modes

### Test Static Mode
```bash
cp .env.static .env
python -m pytest
```

### Test Dynamic Mode
```bash
cp .env.dynamic .env
python -m pytest -m network
```

### Test Full Mode
```bash
cp .env.full .env
python -m pytest -m integration
```

---

## Benefits of This Approach

1. **No Code Changes Required** - Switch modes via environment variables
2. **Offline Development** - Work without internet
3. **Easy Testing** - Test with predictable fixture data
4. **Gradual Migration** - Add services one at a time
5. **Fallback Safety** - Always falls back to static on error
6. **Demo Ready** - Static mode works for hackathon demo
7. **Production Ready** - Dynamic mode for real deployment
