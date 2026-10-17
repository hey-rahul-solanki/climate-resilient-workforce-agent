# Hackathon Solution: AI-Powered Weather-Resilient Workforce Scheduling

## Problem Statement

Field workers are assigned to outdoor locations without considering weather conditions, leading to:
- **Safety risks**: Heat strokes, accidents during extreme weather
- **Productivity loss**: Work delays, poor quality in bad conditions
- **Business impact**: Increased costs, worker dissatisfaction

## Our Solution

An AI agent that:
1. **Checks weather** at assignment location/time
2. **Assesses safety** based on weather conditions
3. **Suggests safe alternative times** when conditions are unsafe
4. **Requires human approval** for any schedule changes

## Key Features

### 1. Weather Safety Assessment
- Real-time weather data from Open-Meteo API
- Safety thresholds for heat, rain, wind, visibility
- Clear status: SAFE, CAUTION, WARNING, SEVERE

### 2. Smart Scheduling
- Checks available free slots in team calendar
- Suggests optimal times based on weather forecast
- Considers work duration and team availability

### 3. Simple Approval Workflow
- Employee requests change with AI suggestion
- Supervisor reviews and approves/rejects
- Schedule updated only on approval

### 4. Location Intelligence
- OpenStreetMap integration for site locations
- Visual map view of assignment sites
- Distance-based scheduling optimization

---

## User Flows

### Employee Flow

```
1. Employee logs in
   ↓
2. Views "My Today's Schedule"
   ↓
3. Sees assignment with weather status
   ↓
4. If UNSAFE:
   - Clicks "Request Change"
   - AI suggests safe alternative times
   - Employee selects preferred time
   - Submits request to supervisor
   ↓
5. Receives notification when supervisor responds
```

### Supervisor Flow

```
1. Supervisor logs in
   ↓
2. Views "Weather-Affected Requests" dashboard
   ↓
3. For each request:
   - Sees original time, weather condition
   - Sees AI-suggested alternative time
   - Clicks [Approve] or [Reject]
   ↓
4. Approved requests update schedule automatically
   ↓
5. Employee receives notification
```

---

## Technology Stack

### Backend
- **Python 3.11+** with FastAPI
- **Weather**: Open-Meteo API (optional), Meteor (optional), or static fixtures
- **Location**: OpenStreetMap (optional) or static coordinates
- **AI**: Gemini (optional) or rule-based logic
- **Database**: PostgreSQL or SQLite for static mode
- **Pydantic** for data validation
- **Configuration**: Environment variables for mode switching

### Frontend
- **React 19** with TypeScript
- **Vite** for build tooling
- **Simple HTML/CSS** (no complex UI library)
- **Leaflet** for map integration (optional)

**Note:** All external services are optional. The application works in static mode with no dependencies, and can be upgraded to dynamic mode via environment variables. See [HACKATHON_CONFIGURATION.md](HACKATHON_CONFIGURATION.md) for details.

---

## Safety Rules

### Heat Safety
- **SAFE**: Temperature < 32°C
- **CAUTION**: 32°C - 35°C (add breaks)
- **WARNING**: 35°C - 40°C (reschedule)
- **SEVERE**: > 40°C (do not work)

### Rain Safety
- **SAFE**: Precipitation < 20%
- **CAUTION**: 20% - 40% (waterproof gear)
- **WARNING**: 40% - 60% (consider rescheduling)
- **SEVERE**: > 60% (do not work)

### Wind Safety
- **SAFE**: Wind speed < 20 km/h
- **CAUTION**: 20 - 30 km/h (secure equipment)
- **WARNING**: 30 - 50 km/h (reschedule)
- **SEVERE**: > 50 km/h (do not work)

---

## Business Impact

### Metrics to Track
- **Safety Incidents**: Number of weather-related incidents
- **Scheduling Efficiency**: Time to reschedule affected work
- **Worker Satisfaction**: Survey scores on safety perception
- **Cost Savings**: Reduced accident-related costs

### Demo Scenario
**Before**: Rahul assigned to outdoor work at 2 PM in 42°C heat → Heat stroke → Hospital → 3 days lost
**After**: AI flags 2 PM as unsafe → Suggests 6 PM (32°C) → Rahul works safely → Productivity maintained

---

## Development Phases

### Phase 1: Core AI Agent (Week 1)
- [ ] Weather safety assessment function
- [ ] Alternative time suggestion function
- [ ] Free slot checking logic
- [ ] API endpoints for weather checks

### Phase 2: Employee UI (Week 2)
- [ ] My Schedule page
- [ ] Weather status badges
- [ ] Request change form
- [ ] Request submission

### Phase 3: Supervisor Dashboard (Week 3)
- [ ] Weather-affected requests view
- [ ] AI suggestion display
- [ ] Approve/Reject functionality
- [ ] Schedule update on approval

### Phase 4: Map Integration (Week 4)
- [ ] OpenStreetMap integration
- [ ] Site location display
- [ ] Distance calculation
- [ ] Visual site map

### Phase 5: Polish & Demo (Week 5)
- [ ] Demo data setup
- [ ] Walkthrough script
- [ ] Metrics dashboard
- [ ] Pitch preparation

---

## API Endpoints

### Weather Assessment
```
POST /api/weather/assess
Request: { location_id, start_time, end_time }
Response: { is_safe, status, reason, suggested_times }
```

### Free Slot Check
```
POST /api/schedule/free-slots
Request: { user_id, site_id, duration, date }
Response: { available_slots: [{ start, end }] }
```

### Weather-Based Suggestion
```
POST /api/weather/suggest-time
Request: { location_id, duration, preferred_date }
Response: { suggested_times: [{ start, end, weather_condition }] }
```

### Assignment with Weather Check
```
POST /api/assignments/with-weather-check
Request: { user_id, site_id, start_time, end_time }
Response: { created, weather_safe, suggested_alternatives }
```

---

## Database Updates

### New Table: weather_safety_rules
```sql
CREATE TABLE weather_safety_rules (
    id UUID PRIMARY KEY,
    rule_type VARCHAR(50), -- heat, rain, wind
    safe_threshold JSONB,
    caution_threshold JSONB,
    warning_threshold JSONB,
    severe_threshold JSONB,
    active BOOLEAN DEFAULT TRUE,
    created_on TIMESTAMPTZ DEFAULT NOW()
);
```

### Updated assignments table
- Add `weather_safe` boolean column
- Add `weather_status` varchar column
- Add `weather_assessment` jsonb column

---

## Success Criteria

### Technical
- [ ] Weather assessment accuracy > 90%
- [ ] Free slot checking finds valid alternatives
- [ ] Map integration displays sites correctly
- [ ] Approval workflow completes in < 5 seconds

### User Experience
- [ ] Employee can request change in < 3 clicks
- [ ] Supervisor can approve in < 2 clicks
- [ ] Clear weather status (green/red badges)
- [ ] Mobile-responsive UI

### Business
- [ ] Demo shows clear safety improvement
- [ ] Metrics dashboard shows impact
- [ ] Pitch tells compelling story
- [ ] No critical bugs in demo

---

## Demo Script

### Scene 1: The Problem
"Rahul is assigned to outdoor maintenance at 2 PM. The temperature is 42°C. This is dangerous."

### Scene 2: The Solution
"Our AI checks the weather at the assignment location. It flags 2 PM as unsafe."

### Scene 3: The Suggestion
"The AI suggests 6 PM as an alternative, when the temperature drops to 32°C. It also checks Rahul's calendar and confirms he's free at 6 PM."

### Scene 4: The Action
"Rahul requests the change with one click. His supervisor reviews and approves with one click."

### Scene 5: The Result
"Rahul works safely at 6 PM. No heat stroke, no lost productivity. Everyone wins."

---

## Winning Pitch

**"We built an AI that protects workers from extreme weather while keeping operations running. Workers stay safe, business stays productive. Simple, effective, and it works today."**

### Key Points
1. **Employee Care First**: Our people matter more than schedules
2. **Business Value**: Safety = productivity = profit
3. **Simplicity**: So easy, anyone can use it
4. **Real Impact**: No complex systems, just smart decisions
5. **Proven Results**: 0 weather incidents in our demo

---

## OpenStreetMap Integration

### Purpose
- Display assignment sites on map
- Calculate distances between sites
- Optimize routing for multiple assignments
- Visual weather overlay on map

### Implementation
- Use **OSM API** for geocoding
- Use **Leaflet.js** for map display
- Cache location data in database
- Update weather data hourly

### Benefits
- Visual site management
- Better scheduling with distance awareness
- Enhanced supervisor oversight
- Improved emergency response

---

## Free Slot Checking Logic

### Algorithm
1. Get user's existing assignments for the date
2. Calculate busy time intervals
3. Get weather forecast for the day
4. Find gaps in busy intervals that are:
   - Long enough for the task duration
   - Have safe weather conditions
5. Return sorted list of available slots

### Example
```
User: Rahul
Date: 2024-01-15
Task Duration: 2 hours
Location: Site A

Existing Assignments:
- 9:00 AM - 11:00 AM (Site B)
- 3:00 PM - 5:00 PM (Site C)

Weather Forecast:
- 6:00 AM - 9:00 AM: 28°C (SAFE)
- 11:00 AM - 3:00 PM: 38°C (WARNING)
- 5:00 PM - 8:00 PM: 30°C (SAFE)

Available Safe Slots:
1. 6:00 AM - 8:00 AM (2 hours, 28°C)
2. 5:00 PM - 7:00 PM (2 hours, 30°C)

Suggested: 5:00 PM - 7:00 PM
```

---

## Next Steps

1. Review and approve this solution document
2. Set up development environment
3. Start Phase 1: Core AI Agent
4. Create wireframes for simplified UI
5. Set up demo data
