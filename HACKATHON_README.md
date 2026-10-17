# Hackathon Solution Quick Start

## 🎯 The Solution in 3 Sentences

An AI agent that checks weather at work locations, assesses safety conditions, and suggests safe alternative times. Employees can request schedule changes with one click, and supervisors approve with one click. Workers stay safe, business stays productive.

---

## 📋 What We Built

### Core Features
1. **Weather Safety Assessment** - Checks if conditions are safe for outdoor work
2. **Smart Scheduling** - Suggests safe times based on weather forecast
3. **Free Slot Checking** - Ensures suggested times don't conflict with existing schedule
4. **OpenStreetMap Integration** - Location intelligence and distance calculation
5. **Simple Approval Workflow** - Employee requests → Supervisor approves

### User Flows

**Employee Flow:**
1. View schedule with weather status
2. If unsafe, click "Request Change"
3. AI suggests safe alternative times
4. Select preferred time and submit
5. Receive notification when approved

**Supervisor Flow:**
1. View weather-affected requests
2. See AI suggestions
3. Click "Approve" or "Reject"
4. Approved changes update schedule automatically

---

## 🚀 Quick Start

### 1. Database Setup

```bash
# Run migration
psql -U workforce_user -d workforce_db -f DATABASE_SCHEMA_HACKATHON_UPDATES.md

# Seed demo data
psql -U workforce_user -d workforce_db -f - <<EOF
-- Insert demo users, sites, assignments
-- (See DATABASE_SCHEMA_HACKATHON_UPDATES.md for full script)
EOF
```

### 2. Backend Setup

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev,api]"

# Start backend
uvicorn workforce_agent.api:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 4. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 📁 New Documentation Files

1. **HACKATHON_SOLUTION.md** - Overall solution overview and strategy
2. **HACKATHON_AI_AGENT.md** - AI agent implementation details
3. **HACKATHON_UI_DESIGN.md** - Simplified UI design specifications
4. **DATABASE_SCHEMA_HACKATHON_UPDATES.md** - Database schema changes
5. **HACKATHON_IMPLEMENTATION_GUIDE.md** - Step-by-step implementation guide

---

## 🎨 UI Preview

### Employee Schedule Page
```
┌─────────────────────────────────────────────┐
│  My Today's Schedule                        │
├─────────────────────────────────────────────┤
│  ☀️ Site A - Maintenance                     │
│  Time: 9:00 AM - 11:00 AM                   │
│  Weather: 28°C, Sunny                        │
│  Status: ✅ SAFE TO WORK                    │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  🔥 Site B - Inspection                      │
│  Time: 2:00 PM - 4:00 PM                    │
│  Weather: 42°C, Extreme Heat                 │
│  Status: ⚠️ UNSAFE - Extreme Heat           │
│  AI Suggestion: "Work at 6:00 PM"           │
│  [Request Change to 6:00 PM]                │
└─────────────────────────────────────────────┘
```

### Supervisor Requests Page
```
┌─────────────────────────────────────────────┐
│  Weather-Affected Requests                  │
│  5 Pending Requests                         │
├─────────────────────────────────────────────┤
│  Request #1 - Rahul Sharma                  │
│  Original: 2:00 PM (42°C - UNSAFE)         │
│  Suggested: 6:00 PM (32°C - SAFE)          │
│  [Approve]  [Reject]  [View Details]       │
└─────────────────────────────────────────────┘
```

---

## 🔧 API Endpoints

### Weather Assessment
```bash
POST /api/ai/weather-assess
{
  "location_id": "VAD-PLANT-01",
  "start_time": "2024-01-15T14:00:00Z",
  "end_time": "2024-01-15T16:00:00Z"
}
```

### Geocoding
```bash
POST /api/ai/geocode
{
  "address": "Mumbai, India"
}
```

### Distance Calculation
```bash
POST /api/ai/calculate-distance
{
  "from": {"latitude": 22.3072, "longitude": 73.1812},
  "to": {"latitude": 19.0760, "longitude": 72.8777}
}
```

---

## 🎯 Safety Rules

### Heat Safety
- **SAFE**: < 32°C
- **CAUTION**: 32°C - 35°C
- **WARNING**: 35°C - 40°C
- **SEVERE**: > 40°C

### Rain Safety
- **SAFE**: < 20% precipitation
- **CAUTION**: 20% - 40%
- **WARNING**: 40% - 60%
- **SEVERE**: > 60%

### Wind Safety
- **SAFE**: < 20 km/h
- **CAUTION**: 20 - 30 km/h
- **WARNING**: 30 - 50 km/h
- **SEVERE**: > 50 km/h

---

## 📊 Demo Scenario

**Setup:** Mumbai with 42°C heat wave at 2 PM

**Before:**
- Rahul assigned to outdoor work at 2 PM
- Temperature: 42°C (extreme heat)
- Risk: Heat stroke, hospitalization

**After:**
- AI flags 2 PM as unsafe
- Suggests 6 PM (32°C, safe)
- Rahul requests change → Supervisor approves
- Rahul works safely at 6 PM
- No incidents, productivity maintained

---

## 🏆 Winning Pitch

**"We built an AI that protects workers from extreme weather while keeping operations running. Workers stay safe, business stays productive. Simple, effective, and it works today."**

### Key Points
1. **Employee Care First** - Our people matter more than schedules
2. **Business Value** - Safety = productivity = profit
3. **Simplicity** - So easy, anyone can use it
4. **Real Impact** - No complex systems, just smart decisions
5. **Proven Results** - 0 weather incidents in our demo

---

## 🛠️ Technology Stack

### Backend
- Python 3.11+ with FastAPI
- Open-Meteo API for weather
- OpenStreetMap for locations
- PostgreSQL for data

### Frontend
- React 19 with TypeScript
- Vite for build tooling
- Simple HTML/CSS (no complex UI library)
- Leaflet for maps

---

## 📚 Implementation Guide

Follow the step-by-step guide in **HACKATHON_IMPLEMENTATION_GUIDE.md**:

- Phase 1: Setup & Database (Day 1)
- Phase 2: AI Agent Implementation (Day 2-3)
- Phase 3: Employee UI (Day 4-5)
- Phase 4: Supervisor UI (Day 6-7)
- Phase 5: Demo Preparation (Day 8)
- Phase 6: Final Polish (Day 9-10)

---

## ✅ Success Criteria

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

## 🐛 Troubleshooting

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

## 📞 Support

For issues or questions:
1. Check the implementation guide
2. Review API documentation
3. Check database schema updates
4. Test with demo data

---

## 🎉 Next Steps

1. Review all documentation files
2. Run database migration
3. Implement AI agent components
4. Build simplified UI
5. Prepare demo scenario
6. Practice the pitch
7. Win the hackathon! 🏆
