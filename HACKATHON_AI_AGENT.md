# AI Agent Implementation Guide

## Overview

The AI Agent is the core intelligence that:
1. Assesses weather safety for work assignments
2. Suggests safe alternative times based on weather
3. Checks team availability (free slots)
4. Integrates with location services (OpenStreetMap or static)

**Important:** All components support both static mode (no external dependencies) and dynamic mode (with external APIs). Configuration is handled via environment variables. See [HACKATHON_CONFIGURATION.md](HACKATHON_CONFIGURATION.md) for details.

---

## Core Components

### 1. Weather Safety Assessor

**File**: `src/workforce_agent/ai/weather_safety.py`

```python
from typing import Literal, Optional
from datetime import datetime
from pydantic import BaseModel

class WeatherCondition(BaseModel):
    temperature_c: float
    precipitation_percent: float
    wind_speed_kmh: float
    visibility_km: float
    humidity_percent: float

class SafetyStatus(BaseModel):
    status: Literal["SAFE", "CAUTION", "WARNING", "SEVERE"]
    is_safe: bool
    reason: str
    recommendations: list[str]

class WeatherSafetyAssessor:
    """Assesses weather safety for outdoor work"""

    # Safety thresholds
    HEAT_SAFE = 32.0
    HEAT_CAUTION = 35.0
    HEAT_WARNING = 40.0

    RAIN_SAFE = 20.0
    RAIN_CAUTION = 40.0
    RAIN_WARNING = 60.0

    WIND_SAFE = 20.0
    WIND_CAUTION = 30.0
    WIND_WARNING = 50.0

    VISIBILITY_SAFE = 5.0
    VISIBILITY_CAUTION = 2.0
    VISIBILITY_WARNING = 1.0

    @classmethod
    def assess(cls, weather: WeatherCondition) -> SafetyStatus:
        """Assess if weather conditions are safe for outdoor work"""
        issues = []
        status = "SAFE"

        # Check temperature
        if weather.temperature_c > cls.HEAT_WARNING:
            status = "SEVERE"
            issues.append(f"Extreme heat: {weather.temperature_c}°C")
        elif weather.temperature_c > cls.HEAT_CAUTION:
            if status != "SEVERE":
                status = "WARNING"
            issues.append(f"High temperature: {weather.temperature_c}°C")
        elif weather.temperature_c > cls.HEAT_SAFE:
            if status == "SAFE":
                status = "CAUTION"
            issues.append(f"Warm: {weather.temperature_c}°C")

        # Check precipitation
        if weather.precipitation_percent > cls.RAIN_WARNING:
            status = "SEVERE"
            issues.append(f"Heavy rain: {weather.precipitation_percent}%")
        elif weather.precipitation_percent > cls.RAIN_CAUTION:
            if status != "SEVERE":
                status = "WARNING"
            issues.append(f"Rain likely: {weather.precipitation_percent}%")
        elif weather.precipitation_percent > cls.RAIN_SAFE:
            if status == "SAFE":
                status = "CAUTION"
            issues.append(f"Light rain: {weather.precipitation_percent}%")

        # Check wind
        if weather.wind_speed_kmh > cls.WIND_WARNING:
            status = "SEVERE"
            issues.append(f"Strong wind: {weather.wind_speed_kmh} km/h")
        elif weather.wind_speed_kmh > cls.WIND_CAUTION:
            if status != "SEVERE":
                status = "WARNING"
            issues.append(f"Windy: {weather.wind_speed_kmh} km/h")
        elif weather.wind_speed_kmh > cls.WIND_SAFE:
            if status == "SAFE":
                status = "CAUTION"
            issues.append(f"Moderate wind: {weather.wind_speed_kmh} km/h")

        # Check visibility
        if weather.visibility_km < cls.VISIBILITY_WARNING:
            status = "SEVERE"
            issues.append(f"Poor visibility: {weather.visibility_km} km")
        elif weather.visibility_km < cls.VISIBILITY_CAUTION:
            if status != "SEVERE":
                status = "WARNING"
            issues.append(f"Reduced visibility: {weather.visibility_km} km")
        elif weather.visibility_km < cls.VISIBILITY_SAFE:
            if status == "SAFE":
                status = "CAUTION"
            issues.append(f"Limited visibility: {weather.visibility_km} km")

        # Generate recommendations
        recommendations = cls._get_recommendations(status, weather)

        return SafetyStatus(
            status=status,
            is_safe=status in ["SAFE", "CAUTION"],
            reason="; ".join(issues) if issues else "Conditions are safe for outdoor work",
            recommendations=recommendations
        )

    @classmethod
    def _get_recommendations(cls, status: str, weather: WeatherCondition) -> list[str]:
        """Get safety recommendations based on status"""
        if status == "SAFE":
            return ["Normal work conditions", "Stay hydrated", "Take regular breaks"]
        elif status == "CAUTION":
            recs = ["Proceed with caution", "Increase break frequency"]
            if weather.temperature_c > cls.HEAT_SAFE:
                recs.append("Ensure adequate hydration")
            if weather.precipitation_percent > cls.RAIN_SAFE:
                recs.append("Use waterproof gear")
            return recs
        elif status == "WARNING":
            return [
                "Consider rescheduling to safer time",
                "If work must proceed: add extra breaks",
                "Monitor workers for heat/rain stress",
                "Have emergency plan ready"
            ]
        else:  # SEVERE
            return [
                "DO NOT PROCEED - Reschedule immediately",
                "Work is unsafe under these conditions",
                "Find alternative safe time window"
            ]
```

---

### 2. Alternative Time Suggester

**File**: `src/workforce_agent/ai/time_suggester.py`

```python
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

class TimeSlot(BaseModel):
    start: datetime
    end: datetime
    weather_condition: WeatherCondition
    safety_status: SafetyStatus
    is_available: bool

class TimeSuggester:
    """Suggests safe alternative times for outdoor work"""

    def __init__(self, weather_client, schedule_checker):
        self.weather_client = weather_client
        self.schedule_checker = schedule_checker

    async def suggest_safe_times(
        self,
        location_id: str,
        user_id: str,
        duration_hours: float,
        preferred_date: datetime,
        max_suggestions: int = 5
    ) -> List[TimeSlot]:
        """
        Suggest safe time slots for work based on:
        1. Weather conditions
        2. User's existing schedule (free slots)
        3. Work duration
        """
        # Get hourly weather forecast for the day
        weather_forecast = await self.weather_client.get_hourly_forecast(
            location_id=location_id,
            date=preferred_date
        )

        # Get user's existing assignments for the day
        existing_assignments = await self.schedule_checker.get_assignments(
            user_id=user_id,
            date=preferred_date
        )

        # Calculate busy intervals
        busy_intervals = self._calculate_busy_intervals(existing_assignments)

        # Find all possible time slots
        possible_slots = self._find_time_slots(
            weather_forecast=weather_forecast,
            busy_intervals=busy_intervals,
            duration_hours=duration_hours,
            date=preferred_date
        )

        # Filter for safe weather only
        safe_slots = [
            slot for slot in possible_slots
            if slot.safety_status.is_safe
        ]

        # Sort by safety status (SAFE first, then CAUTION)
        safe_slots.sort(key=lambda x: (
            0 if x.safety_status.status == "SAFE" else 1,
            x.start
        ))

        return safe_slots[:max_suggestions]

    def _calculate_busy_intervals(self, assignments: List) -> List[tuple]:
        """Calculate busy time intervals from assignments"""
        intervals = []
        for assignment in assignments:
            intervals.append((assignment.start_time, assignment.end_time))
        return intervals

    def _find_time_slots(
        self,
        weather_forecast: List,
        busy_intervals: List[tuple],
        duration_hours: float,
        date: datetime
    ) -> List[TimeSlot]:
        """Find all possible time slots considering weather and availability"""
        slots = []
        duration_minutes = int(duration_hours * 60)

        # Start from 6 AM to 8 PM (typical work hours)
        start_of_day = date.replace(hour=6, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=20, minute=0, second=0, microsecond=0)

        current_time = start_of_day
        while current_time + timedelta(minutes=duration_minutes) <= end_of_day:
            end_time = current_time + timedelta(minutes=duration_minutes)

            # Check if slot overlaps with busy intervals
            is_available = not self._overlaps_with_busy(
                current_time, end_time, busy_intervals
            )

            # Get weather for this time slot
            weather = self._get_weather_for_slot(
                current_time, end_time, weather_forecast
            )

            # Assess safety
            safety_status = WeatherSafetyAssessor.assess(weather)

            slots.append(TimeSlot(
                start=current_time,
                end=end_time,
                weather_condition=weather,
                safety_status=safety_status,
                is_available=is_available
            ))

            # Move to next hour
            current_time += timedelta(hours=1)

        return slots

    def _overlaps_with_busy(
        self,
        start: datetime,
        end: datetime,
        busy_intervals: List[tuple]
    ) -> bool:
        """Check if time slot overlaps with busy intervals"""
        for busy_start, busy_end in busy_intervals:
            if not (end <= busy_start or start >= busy_end):
                return True
        return False

    def _get_weather_for_slot(
        self,
        start: datetime,
        end: datetime,
        weather_forecast: List
    ) -> WeatherCondition:
        """Get average weather conditions for time slot"""
        # Get weather data for each hour in the slot
        slot_weather = []
        current = start
        while current < end:
            hour_weather = self._find_weather_at_time(current, weather_forecast)
            if hour_weather:
                slot_weather.append(hour_weather)
            current += timedelta(hours=1)

        if not slot_weather:
            # Return safe defaults if no weather data
            return WeatherCondition(
                temperature_c=25.0,
                precipitation_percent=0.0,
                wind_speed_kmh=10.0,
                visibility_km=10.0,
                humidity_percent=50.0
            )

        # Calculate averages
        avg_temp = sum(w.temperature_c for w in slot_weather) / len(slot_weather)
        avg_precip = sum(w.precipitation_percent for w in slot_weather) / len(slot_weather)
        avg_wind = sum(w.wind_speed_kmh for w in slot_weather) / len(slot_weather)
        avg_visibility = sum(w.visibility_km for w in slot_weather) / len(slot_weather)
        avg_humidity = sum(w.humidity_percent for w in slot_weather) / len(slot_weather)

        return WeatherCondition(
            temperature_c=avg_temp,
            precipitation_percent=avg_precip,
            wind_speed_kmh=avg_wind,
            visibility_km=avg_visibility,
            humidity_percent=avg_humidity
        )

    def _find_weather_at_time(self, time: datetime, forecast: List) -> Optional[WeatherCondition]:
        """Find weather data at specific time"""
        for weather in forecast:
            if weather.time.hour == time.hour:
                return weather
        return None
```

---

### 3. Free Slot Checker

**File**: `src/workforce_agent/ai/schedule_checker.py`

```python
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

class Assignment(BaseModel):
    id: str
    user_id: str
    site_id: str
    start_time: datetime
    end_time: datetime
    description: str

class FreeSlot(BaseModel):
    start: datetime
    end: datetime
    duration_minutes: int

class ScheduleChecker:
    """Checks user's schedule for free time slots"""

    def __init__(self, db_client):
        self.db_client = db_client

    async def get_assignments(
        self,
        user_id: str,
        date: datetime
    ) -> List[Assignment]:
        """Get all assignments for a user on a specific date"""
        query = """
            SELECT id, user_id, site_id, start_time, end_time, description
            FROM assignments
            WHERE user_id = $1
            AND DATE(start_time) = $2
            AND active = TRUE
            AND status NOT IN ('cancelled', 'completed')
            ORDER BY start_time
        """
        rows = await self.db_client.fetch(query, user_id, date.date())
        return [Assignment(**row) for row in rows]

    async def find_free_slots(
        self,
        user_id: str,
        date: datetime,
        duration_minutes: int,
        work_start_hour: int = 6,
        work_end_hour: int = 20
    ) -> List[FreeSlot]:
        """
        Find free time slots for a user on a specific date

        Args:
            user_id: User to check
            date: Date to check
            duration_minutes: Required duration in minutes
            work_start_hour: Start of work day (default 6 AM)
            work_end_hour: End of work day (default 8 PM)
        """
        # Get existing assignments
        assignments = await self.get_assignments(user_id, date)

        # Calculate busy intervals
        busy_intervals = [
            (a.start_time, a.end_time)
            for a in assignments
        ]

        # Define work day boundaries
        start_of_day = date.replace(hour=work_start_hour, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=work_end_hour, minute=0, second=0, microsecond=0)

        # Find free slots
        free_slots = self._find_gaps(
            start_of_day,
            end_of_day,
            busy_intervals,
            duration_minutes
        )

        return free_slots

    def _find_gaps(
        self,
        start: datetime,
        end: datetime,
        busy_intervals: List[tuple],
        min_duration_minutes: int
    ) -> List[FreeSlot]:
        """Find gaps between busy intervals"""
        # Sort busy intervals by start time
        busy_intervals.sort(key=lambda x: x[0])

        gaps = []
        current_start = start

        for busy_start, busy_end in busy_intervals:
            # Check if there's a gap before this busy interval
            if current_start < busy_start:
                gap_duration = (busy_start - current_start).total_seconds() / 60
                if gap_duration >= min_duration_minutes:
                    gaps.append(FreeSlot(
                        start=current_start,
                        end=busy_start,
                        duration_minutes=int(gap_duration)
                    ))
            # Move current start to after this busy interval
            current_start = max(current_start, busy_end)

        # Check if there's a gap after the last busy interval
        if current_start < end:
            gap_duration = (end - current_start).total_seconds() / 60
            if gap_duration >= min_duration_minutes:
                gaps.append(FreeSlot(
                    start=current_start,
                    end=end,
                    duration_minutes=int(gap_duration)
                ))

        return gaps

    async def is_slot_available(
        self,
        user_id: str,
        start: datetime,
        end: datetime
    ) -> bool:
        """Check if a specific time slot is available"""
        assignments = await self.get_assignments(user_id, start)

        for assignment in assignments:
            # Check for overlap
            if not (end <= assignment.start_time or start >= assignment.end_time):
                return False

        return True
```

---

### 4. OpenStreetMap Integration

**File**: `src/workforce_agent/ai/location_service.py`

```python
import httpx
from typing import Optional, Dict
from pydantic import BaseModel

class Location(BaseModel):
    latitude: float
    longitude: float
    display_name: str
    city: str
    state: str
    country: str

class LocationService:
    """Service for OpenStreetMap integration"""

    OSM_NOMINATIM_BASE = "https://nominatim.openstreetmap.org"

    def __init__(self):
        self.client = httpx.AsyncClient(
            headers={"User-Agent": "ClimateResilientWorkforce/1.0"}
        )

    async def geocode(self, address: str) -> Optional[Location]:
        """
        Convert address to coordinates using OpenStreetMap Nominatim API

        Args:
            address: Address string to geocode

        Returns:
            Location with coordinates and details
        """
        try:
            params = {
                "q": address,
                "format": "json",
                "limit": 1
            }

            response = await self.client.get(
                f"{self.OSM_NOMINATIM_BASE}/search",
                params=params,
                timeout=10.0
            )
            response.raise_for_status()

            data = response.json()
            if not data:
                return None

            result = data[0]
            return Location(
                latitude=float(result["lat"]),
                longitude=float(result["lon"]),
                display_name=result["display_name"],
                city=result.get("address", {}).get("city", ""),
                state=result.get("address", {}).get("state", ""),
                country=result.get("address", {}).get("country", "")
            )
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None

    async def reverse_geocode(
        self,
        latitude: float,
        longitude: float
    ) -> Optional[Location]:
        """
        Convert coordinates to address using OpenStreetMap Nominatim API

        Args:
            latitude: Latitude
            longitude: Longitude

        Returns:
            Location with address details
        """
        try:
            params = {
                "lat": str(latitude),
                "lon": str(longitude),
                "format": "json"
            }

            response = await self.client.get(
                f"{self.OSM_NOMINATIM_BASE}/reverse",
                params=params,
                timeout=10.0
            )
            response.raise_for_status()

            data = response.json()
            address = data.get("address", {})

            return Location(
                latitude=latitude,
                longitude=longitude,
                display_name=data.get("display_name", ""),
                city=address.get("city", ""),
                state=address.get("state", ""),
                country=address.get("country", "")
            )
        except Exception as e:
            print(f"Reverse geocoding error: {e}")
            return None

    def calculate_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calculate distance between two coordinates using Haversine formula

        Returns distance in kilometers
        """
        from math import radians, cos, sin, asin, sqrt

        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))

        # Radius of Earth in kilometers
        r = 6371

        return c * r

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
```

---

## API Endpoints

### POST /api/ai/weather-assess

Assess weather safety for a specific time and location.

**Request:**
```json
{
  "location_id": "VAD-PLANT-01",
  "start_time": "2024-01-15T14:00:00Z",
  "end_time": "2024-01-15T16:00:00Z"
}
```

**Response:**
```json
{
  "status": "WARNING",
  "is_safe": false,
  "reason": "High temperature: 38°C; Rain likely: 45%",
  "recommendations": [
    "Consider rescheduling to safer time",
    "If work must proceed: add extra breaks",
    "Monitor workers for heat/rain stress"
  ]
}
```

### POST /api/ai/suggest-times

Get safe alternative time suggestions.

**Request:**
```json
{
  "location_id": "VAD-PLANT-01",
  "user_id": "user-uuid",
  "duration_hours": 2,
  "preferred_date": "2024-01-15"
}
```

**Response:**
```json
{
  "suggested_times": [
    {
      "start": "2024-01-15T06:00:00Z",
      "end": "2024-01-15T08:00:00Z",
      "weather": {
        "temperature_c": 28,
        "precipitation_percent": 10,
        "wind_speed_kmh": 8
      },
      "safety_status": "SAFE",
      "is_available": true
    },
    {
      "start": "2024-01-15T17:00:00Z",
      "end": "2024-01-15T19:00:00Z",
      "weather": {
        "temperature_c": 30,
        "precipitation_percent": 15,
        "wind_speed_kmh": 10
      },
      "safety_status": "SAFE",
      "is_available": true
    }
  ]
}
```

### POST /api/ai/geocode

Convert address to coordinates.

**Request:**
```json
{
  "address": "123 Main Street, Vadodara, Gujarat, India"
}
```

**Response:**
```json
{
  "latitude": 22.3072,
  "longitude": 73.1812,
  "display_name": "123, Main Street, Vadodara, Gujarat, India",
  "city": "Vadodara",
  "state": "Gujarat",
  "country": "India"
}
```

### POST /api/ai/calculate-distance

Calculate distance between two locations.

**Request:**
```json
{
  "from": {"latitude": 22.3072, "longitude": 73.1812},
  "to": {"latitude": 19.0760, "longitude": 72.8777}
}
```

**Response:**
```json
{
  "distance_km": 423.5
}
```

---

## Testing

### Unit Tests

```python
# tests/test_weather_safety.py
def test_heat_assessment():
    weather = WeatherCondition(
        temperature_c=38.0,
        precipitation_percent=10.0,
        wind_speed_kmh=15.0,
        visibility_km=8.0,
        humidity_percent=60.0
    )
    status = WeatherSafetyAssessor.assess(weather)
    assert status.status == "WARNING"
    assert not status.is_safe

def test_safe_conditions():
    weather = WeatherCondition(
        temperature_c=28.0,
        precipitation_percent=5.0,
        wind_speed_kmh=10.0,
        visibility_km=10.0,
        humidity_percent=50.0
    )
    status = WeatherSafetyAssessor.assess(weather)
    assert status.status == "SAFE"
    assert status.is_safe
```

### Integration Tests

```python
# tests/test_integration.py
async def test_full_flow():
    # 1. Get weather forecast
    weather = await weather_client.get_hourly_forecast("VAD-PLANT-01", date)

    # 2. Assess safety
    status = WeatherSafetyAssessor.assess(weather[0])

    # 3. If unsafe, get suggestions
    if not status.is_safe:
        suggestions = await time_suggester.suggest_safe_times(
            location_id="VAD-PLANT-01",
            user_id="user-uuid",
            duration_hours=2,
            preferred_date=date
        )
        assert len(suggestions) > 0
```

---

## Configuration

Add to `src/workforce_agent/config.py`:

```python
class Settings(BaseSettings):
    # AI Agent Settings
    AI_WORK_START_HOUR: int = 6
    AI_WORK_END_HOUR: int = 20
    AI_MAX_SUGGESTIONS: int = 5
    AI_MIN_SLOT_DURATION_MINUTES: int = 30

    # OpenStreetMap Settings
    OSM_RATE_LIMIT_DELAY: float = 1.0  # seconds between requests
    OSM_TIMEOUT_SECONDS: float = 10.0

    class Config:
        env_prefix = "WORKFORCE_"
```

**Important:** For full configuration options including static/dynamic mode switching, see [HACKATHON_CONFIGURATION.md](HACKATHON_CONFIGURATION.md). All AI components support both static mode (no external dependencies) and dynamic mode (with external APIs) via environment variables.

---

## Next Steps

1. Implement the four core components
2. Add API endpoints
3. Write unit tests
4. Integrate with existing weather client
5. Add database queries for schedule checking
6. Test with real data
