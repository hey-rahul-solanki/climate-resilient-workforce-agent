# Hackathon Implementation Guide

## Overview

This guide provides step-by-step instructions to implement the simplified hackathon solution.

**Important:** The application is designed to work in **static mode** by default (no external dependencies). All external services (weather APIs, OpenStreetMap, Gemini, GCP) are optional and can be enabled later via environment variables. See [HACKATHON_CONFIGURATION.md](HACKATHON_CONFIGURATION.md) for complete configuration details.

---

## Phase 1: Setup & Database (Day 1)

### 1.1 Configuration Setup

Create `.env` file for static mode (default):

```bash
# Static Mode - No External Dependencies
WORKFORCE_MODE=static
WORKFORCE_WEATHER_SOURCE=fixture
WORKFORCE_FIXTURE_PATH=./data/fixtures/weather.json
WORKFORCE_LOCATION_SOURCE=static
WORKFORCE_AI_SOURCE=rule_based
WORKFORCE_USE_STATIC_DB=true
```

See [HACKATHON_CONFIGURATION.md](HACKATHON_CONFIGURATION.md) for all configuration options.

### 1.2 Create Fixture Data

Create directory structure:
```bash
mkdir -p data/fixtures
```

Create `data/fixtures/weather.json` with static weather data (see HACKATHON_CONFIGURATION.md for example).

### 1.3 Database Migration

Run the migration script to add new tables and columns:

```bash
# Connect to PostgreSQL
psql -U workforce_user -d workforce_db

# Run migration
\i DATABASE_SCHEMA_HACKATHON_UPDATES.md
```

Or use the migration script directly:

```bash
psql -U workforce_user -d workforce_db -f DATABASE_SCHEMA_HACKATHON_UPDATES.md
```

### 1.2 Seed Demo Data

```bash
psql -U workforce_user -d workforce_db -f - <<EOF
-- Seed demo users
INSERT INTO users (username, email, employee_id, full_name, role, status, location_id) VALUES
('rahul', 'rahul@example.com', 'EMP001', 'Rahul Sharma', 'employee', 'active', (SELECT id FROM locations WHERE location_code = 'vadodara-gujarat' LIMIT 1)),
('amit', 'amit@example.com', 'EMP002', 'Amit Patel', 'employee', 'active', (SELECT id FROM locations WHERE location_code = 'vadodara-gujarat' LIMIT 1)),
('supervisor1', 'supervisor1@example.com', 'SUP001', 'Jane Smith', 'supervisor', 'active', (SELECT id FROM locations WHERE location_code = 'vadodara-gujarat' LIMIT 1))
ON CONFLICT (username) DO NOTHING;

-- Seed demo sites
INSERT INTO sites (site_id, name, city, state, country, latitude, longitude, location_id, timezone, status) VALUES
('VAD-PLANT-01', 'Vadodara Process Plant', 'Vadodara', 'Gujarat', 'India', 22.3072, 73.1812, (SELECT id FROM locations WHERE location_code = 'vadodara-gujarat' LIMIT 1), 'Asia/Kolkata', 'active'),
('MUM-SITE-01', 'Mumbai Industrial Site', 'Mumbai', 'Maharashtra', 'India', 19.0760, 72.8777, (SELECT id FROM locations WHERE location_code = 'vadodara-gujarat' LIMIT 1), 'Asia/Kolkata', 'active')
ON CONFLICT (site_id) DO NOTHING;

-- Seed demo assignments
INSERT INTO assignments (user_id, site_id, status, description, start_time, end_time, shift, hours_allocated) VALUES
((SELECT id FROM users WHERE username = 'rahul'), (SELECT id FROM sites WHERE site_id = 'VAD-PLANT-01'), 'scheduled', 'Site B - Inspection', '2024-01-15T14:00:00Z', '2024-01-15T16:00:00Z', 'afternoon', 2),
((SELECT id FROM users WHERE username = 'amit'), (SELECT id FROM sites WHERE site_id = 'MUM-SITE-01'), 'scheduled', 'Site C - Repair', '2024-01-15T13:00:00Z', '2024-01-15T15:00:00Z', 'afternoon', 2)
ON CONFLICT DO NOTHING;
EOF
```

### 1.3 Verify Setup

```bash
# Check new tables exist
psql -U workforce_user -d workforce_db -c "\dt"

# Check weather_safety_rules data
psql -U workforce_user -d workforce_db -c "SELECT * FROM weather_safety_rules;"
```

---

## Phase 2: AI Agent Implementation (Day 2-3)

### 2.1 Create AI Module Structure

```bash
mkdir -p src/workforce_agent/ai
touch src/workforce_agent/ai/__init__.py
```

### 2.2 Implement Weather Safety Assessor

Create `src/workforce_agent/ai/weather_safety.py`:

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

### 2.3 Implement Schedule Checker

Create `src/workforce_agent/ai/schedule_checker.py`:

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
        """Find free time slots for a user on a specific date"""
        assignments = await self.get_assignments(user_id, date)
        busy_intervals = [(a.start_time, a.end_time) for a in assignments]

        start_of_day = date.replace(hour=work_start_hour, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=work_end_hour, minute=0, second=0, microsecond=0)

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
        busy_intervals.sort(key=lambda x: x[0])
        gaps = []
        current_start = start

        for busy_start, busy_end in busy_intervals:
            if current_start < busy_start:
                gap_duration = (busy_start - current_start).total_seconds() / 60
                if gap_duration >= min_duration_minutes:
                    gaps.append(FreeSlot(
                        start=current_start,
                        end=busy_start,
                        duration_minutes=int(gap_duration)
                    ))
            current_start = max(current_start, busy_end)

        if current_start < end:
            gap_duration = (end - current_start).total_seconds() / 60
            if gap_duration >= min_duration_minutes:
                gaps.append(FreeSlot(
                    start=current_start,
                    end=end,
                    duration_minutes=int(gap_duration)
                ))

        return gaps
```

### 2.4 Implement OpenStreetMap Integration

Create `src/workforce_agent/ai/location_service.py`:

```python
import httpx
from typing import Optional
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
        """Convert address to coordinates using OpenStreetMap Nominatim API"""
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

    def calculate_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """Calculate distance between two coordinates using Haversine formula"""
        from math import radians, cos, sin, asin, sqrt

        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Earth radius in km
        return c * r

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
```

### 2.5 Add AI Endpoints to API

Update `src/workforce_agent/api.py`:

```python
from workforce_agent.ai.weather_safety import WeatherSafetyAssessor, WeatherCondition, SafetyStatus
from workforce_agent.ai.schedule_checker import ScheduleChecker
from workforce_agent.ai.location_service import LocationService

# Initialize AI services
location_service = LocationService()

@app.post("/api/ai/weather-assess")
async def assess_weather(
    location_id: str,
    start_time: datetime,
    end_time: datetime
):
    """Assess weather safety for a specific time and location"""
    # Get weather data (use existing weather client)
    weather_data = await weather_client.get_forecast(location_id, 1)

    # Convert to WeatherCondition
    weather = WeatherCondition(
        temperature_c=weather_data.temperature_c,
        precipitation_percent=weather_data.precipitation_percent,
        wind_speed_kmh=weather_data.wind_speed_kmh,
        visibility_km=weather_data.visibility_km,
        humidity_percent=weather_data.humidity_percent
    )

    # Assess safety
    status = WeatherSafetyAssessor.assess(weather)

    return {
        "status": status.status,
        "is_safe": status.is_safe,
        "reason": status.reason,
        "recommendations": status.recommendations
    }

@app.post("/api/ai/geocode")
async def geocode(address: str):
    """Convert address to coordinates"""
    location = await location_service.geocode(address)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location.dict()

@app.post("/api/ai/calculate-distance")
async def calculate_distance(
    from_lat: float,
    from_lon: float,
    to_lat: float,
    to_lon: float
):
    """Calculate distance between two locations"""
    distance = location_service.calculate_distance(from_lat, from_lon, to_lat, to_lon)
    return {"distance_km": distance}
```

### 2.6 Test AI Agent

```bash
# Test weather assessment
curl -X POST "http://localhost:8000/api/ai/weather-assess?location_id=VAD-PLANT-01&start_time=2024-01-15T14:00:00Z&end_time=2024-01-15T16:00:00Z"

# Test geocoding
curl -X POST "http://localhost:8000/api/ai/geocode?address=Mumbai,%20India"

# Test distance calculation
curl -X POST "http://localhost:8000/api/ai/calculate-distance?from_lat=22.3072&from_lon=73.1812&to_lat=19.0760&to_lon=72.8777"
```

---

## Phase 3: Employee UI (Day 4-5)

### 3.1 Create Employee Schedule Page

Create `frontend/src/pages/employee/SchedulePage.tsx`:

```typescript
import React, { useState, useEffect } from 'react';
import { aiService } from '../../services/aiService';
import { Assignment, SafetyStatus } from '../../types/types';

export default function SchedulePage() {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAssignments();
  }, []);

  const loadAssignments = async () => {
    try {
      // Fetch assignments with weather assessment
      const response = await fetch('/api/employee/assignments');
      const data = await response.json();
      setAssignments(data.data);
    } catch (error) {
      console.error('Error loading assignments:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="schedule-page">
      <h1>My Today's Schedule</h1>
      <p>{new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>

      {assignments.map((assignment) => (
        <AssignmentCard key={assignment.id} assignment={assignment} />
      ))}
    </div>
  );
}

function AssignmentCard({ assignment }: { assignment: Assignment }) {
  const { safety_status } = assignment.weather || { safety_status: { status: 'SAFE', is_safe: true } };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'SAFE': return 'status-safe';
      case 'CAUTION': return 'status-caution';
      case 'WARNING': return 'status-warning';
      case 'SEVERE': return 'status-severe';
      default: return '';
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3>{assignment.site} - {assignment.task}</h3>
        <span className={`status-badge ${getStatusColor(safety_status.status)}`}>
          {safety_status.is_safe ? '✅ SAFE' : '⚠️ UNSAFE'}
        </span>
      </div>
      <div className="card-body">
        <p><strong>Time:</strong> {new Date(assignment.start_time).toLocaleTimeString()} - {new Date(assignment.end_time).toLocaleTimeString()}</p>
        <p><strong>Duration:</strong> {assignment.duration}</p>
        <p><strong>Weather:</strong> {assignment.weather?.temperature}°C, {assignment.weather?.condition}</p>
        {!safety_status.is_safe && (
          <p className="warning-text">{safety_status.reason}</p>
        )}
      </div>
      <div className="card-footer">
        {!safety_status.is_safe && (
          <button className="btn btn-danger">Request Change</button>
        )}
        <button className="btn btn-secondary">View Details</button>
      </div>
    </div>
  );
}
```

### 3.2 Add CSS Styles

Update `frontend/src/index.css`:

```css
/* Status badges */
.status-safe {
  background: #d4edda;
  color: #155724;
  border: 2px solid #c3e6cb;
  padding: 4px 8px;
  border-radius: 4px;
}

.status-caution {
  background: #fff3cd;
  color: #856404;
  border: 2px solid #ffeaa7;
  padding: 4px 8px;
  border-radius: 4px;
}

.status-warning {
  background: #f8d7da;
  color: #721c24;
  border: 2px solid #f5c6cb;
  padding: 4px 8px;
  border-radius: 4px;
}

.status-severe {
  background: #f5c6cb;
  color: #721c24;
  border: 2px solid #e02d2d;
  padding: 4px 8px;
  border-radius: 4px;
}

/* Card styles */
.card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.card-body {
  margin-bottom: 15px;
}

.card-footer {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

/* Buttons */
.btn {
  padding: 8px 16px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-size: 14px;
}

.btn-danger {
  background: #dc2626;
  color: white;
}

.btn-secondary {
  background: #6b7280;
  color: white;
}

.warning-text {
  color: #dc2626;
  font-weight: bold;
}
```

### 3.3 Test Employee UI

```bash
cd frontend
npm run dev
```

Visit `http://localhost:5173/employee/schedule`

---

## Phase 4: Supervisor UI (Day 6-7)

### 4.1 Create Supervisor Requests Page

Create `frontend/src/pages/supervisor/RequestsPage.tsx`:

```typescript
import React, { useState, useEffect } from 'react';
import { aiService } from '../../services/aiService';
import { SupervisorRequest } from '../../types/types';

export default function RequestsPage() {
  const [requests, setRequests] = useState<SupervisorRequest[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRequests();
  }, []);

  const loadRequests = async () => {
    try {
      const data = await aiService.getSupervisorRequests();
      setRequests(data);
    } catch (error) {
      console.error('Error loading requests:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (requestId: string) => {
    try {
      await aiService.approveRequest(requestId);
      loadRequests(); // Refresh
    } catch (error) {
      console.error('Error approving request:', error);
    }
  };

  const handleReject = async (requestId: string) => {
    try {
      await aiService.rejectRequest(requestId, 'Not approved');
      loadRequests(); // Refresh
    } catch (error) {
      console.error('Error rejecting request:', error);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="requests-page">
      <h1>Weather-Affected Requests</h1>
      <p>{requests.length} Pending Requests</p>

      {requests.map((request) => (
        <RequestCard
          key={request.id}
          request={request}
          onApprove={() => handleApprove(request.id)}
          onReject={() => handleReject(request.id)}
        />
      ))}
    </div>
  );
}

function RequestCard({
  request,
  onApprove,
  onReject
}: {
  request: SupervisorRequest;
  onApprove: () => void;
  onReject: () => void;
}) {
  return (
    <div className="card">
      <div className="card-header">
        <h3>Request #{request.id.slice(0, 8)} - {request.employee_name}</h3>
        <span className={`status-badge status-${request.urgency.toLowerCase()}`}>
          {request.urgency}
        </span>
      </div>
      <div className="card-body">
        <p><strong>Assignment:</strong> {request.assignment}</p>
        <p><strong>Original Time:</strong> {new Date(request.original_time).toLocaleTimeString()}</p>
        <p><strong>Weather:</strong> {request.weather.temperature}°C ({request.weather.status})</p>
        <hr />
        <p><strong>AI Suggestion:</strong> {new Date(request.suggested_time).toLocaleTimeString()}</p>
        <p><strong>Reason:</strong> {request.reason}</p>
      </div>
      <div className="card-footer">
        <button className="btn btn-success" onClick={onApprove}>Approve</button>
        <button className="btn btn-danger" onClick={onReject}>Reject</button>
        <button className="btn btn-secondary">View Details</button>
      </div>
    </div>
  );
}
```

### 4.2 Test Supervisor UI

Visit `http://localhost:5173/supervisor/requests`

---

## Phase 5: Demo Preparation (Day 8)

### 5.1 Create Demo Scenario

```bash
# Create extreme heat scenario in Mumbai
psql -U workforce_user -d workforce_db <<EOF
-- Update assignment to have extreme heat
UPDATE assignments
SET weather = '{"temperature_c": 42, "precipitation_percent": 5, "wind_speed_kmh": 10, "visibility_km": 10, "humidity_percent": 60}',
    weather_safe = false,
    weather_status = 'SEVERE',
    weather_assessment = '{"status": "SEVERE", "is_safe": false, "reason": "Extreme heat: 42°C", "recommendations": ["DO NOT PROCEED - Reschedule immediately"]}'
WHERE id = (SELECT id FROM assignments WHERE description LIKE '%Site B%' LIMIT 1);

-- Create schedule change request
INSERT INTO schedule_change_requests (
    user_id,
    assignment_id,
    original_start_time,
    original_end_time,
    suggested_start_time,
    suggested_end_time,
    original_weather,
    suggested_weather,
    weather_status,
    reason,
    urgency,
    status
) VALUES (
    (SELECT id FROM users WHERE username = 'rahul' LIMIT 1),
    (SELECT id FROM assignments WHERE description LIKE '%Site B%' LIMIT 1),
    '2024-01-15T14:00:00Z',
    '2024-01-15T16:00:00Z',
    '2024-01-15T18:00:00Z',
    '2024-01-15T20:00:00Z',
    '{"temperature_c": 42, "precipitation_percent": 5, "wind_speed_kmh": 10, "visibility_km": 10, "humidity_percent": 60}',
    '{"temperature_c": 32, "precipitation_percent": 10, "wind_speed_kmh": 8, "visibility_km": 10, "humidity_percent": 55}',
    'SEVERE',
    'Too hot, worried about heat stroke',
    'high',
    'pending'
);
EOF
```

### 5.2 Practice Demo Script

**Scene 1: The Problem**
1. Show Rahul's schedule at 2 PM
2. Display weather: 42°C extreme heat
3. Show status: UNSAFE (red badge)

**Scene 2: The Solution**
1. Click "Request Change"
2. Show AI suggestion: 6 PM (32°C)
3. Show reason: "Too hot, worried about heat stroke"
4. Submit request

**Scene 3: Supervisor Review**
1. Switch to supervisor view
2. See pending request
3. Show original vs suggested time
4. Click "Approve"

**Scene 4: The Result**
1. Assignment updated to 6 PM
2. Notification sent to Rahul
3. Show safe weather at new time

### 5.3 Prepare Pitch

**Slide 1: Problem**
- Workers assigned to outdoor work without weather consideration
- Heat strokes, accidents, lost productivity
- Business impact: costs, delays, dissatisfaction

**Slide 2: Solution**
- AI agent checks weather at assignment location
- Assesses safety based on thresholds
- Suggests safe alternative times
- Simple approval workflow

**Slide 3: Demo**
- Live walkthrough of the system
- Show real weather data
- Show AI suggestion
- Show approval process

**Slide 4: Impact**
- Reduced weather incidents
- Improved worker satisfaction
- Minimal scheduling disruption
- Cost savings

---

## Phase 6: Final Polish (Day 9-10)

### 6.1 Performance Optimization

- Add caching for weather data
- Optimize database queries
- Add loading states
- Handle errors gracefully

### 6.2 Mobile Responsiveness

```css
@media (max-width: 768px) {
  .card {
    padding: 15px;
  }

  .card-footer {
    flex-direction: column;
  }

  button {
    width: 100%;
  }
}
```

### 6.3 Accessibility

- Add ARIA labels
- Ensure keyboard navigation
- Use semantic HTML
- Add alt text for images

### 6.4 Documentation

- Update README
- Add API documentation
- Create user guide
- Document deployment steps

---

## Quick Start Commands

```bash
# Backend
cd /path/to/project
source .venv/bin/activate
uvicorn workforce_agent.api:app --host 0.0.0.0 --port 8000 --reload

# Frontend
cd frontend
npm run dev

# Database
psql -U workforce_user -d workforce_db
```

---

## Troubleshooting

### Weather API Not Working
- Check Open-Meteo API status
- Verify location coordinates
- Check network connectivity

### Database Connection Issues
- Verify PostgreSQL is running
- Check connection string in config
- Ensure database exists

### UI Not Loading
- Check backend is running
- Verify API base URL in frontend .env
- Check browser console for errors

---

## Success Checklist

- [ ] Database migration completed
- [ ] AI agent implemented and tested
- [ ] Employee UI working
- [ ] Supervisor UI working
- [ ] Demo scenario prepared
- [ ] Pitch deck ready
- [ ] Documentation complete
- [ ] No critical bugs
- [ ] Mobile responsive
- [ ] Accessibility checked

---

## Resources

- [Open-Meteo API](https://open-meteo.com/)
- [OpenStreetMap Nominatim](https://nominatim.openstreetmap.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
