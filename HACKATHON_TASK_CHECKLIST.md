# Hackathon Task Checklist

**Important:** All tasks are designed for static mode first (no external dependencies). External services can be added later via environment variables. See [HACKATHON_CONFIGURATION.md](HACKATHON_CONFIGURATION.md) for details.

## Phase 0: Configuration Setup

### 0.1 Create Configuration Structure - done
- [x] Create config.py file in src/workforce_agent
- [x] Import BaseSettings from pydantic_settings
- [x] Create Settings class
- [x] Add mode field (default: static)
- [x] Add weather_source field (default: fixture)
- [x] Add fixture_path field
- [x] Add location_source field (default: static)
- [x] Add ai_source field (default: rule_based)
- [x] Add optional API key fields (all Optional[str])
- [x] Add Config class with env_prefix
- [x] Export settings instance

### 0.2 Create Environment Files - done
- [x] Create .env.static template
- [x] Set WORKFORCE_MODE=static
- [x] Set WORKFORCE_WEATHER_SOURCE=fixture
- [x] Set WORKFORCE_FIXTURE_PATH=./data/fixtures/weather.json
- [x] Set WORKFORCE_LOCATION_SOURCE=static
- [x] Set WORKFORCE_AI_SOURCE=rule_based
- [x] Create .env.dynamic template
- [x] Create .env.full template
- [x] Add .env to .gitignore
- [ ] Copy .env.static to .env (manual step - .env is gitignored)

### 0.3 Create Fixture Data Structure - done
- [x] Create data/fixtures directory
- [x] Create weather.json fixture file
- [x] Add VAD-PLANT-01 weather data
- [x] Add MUM-SITE-01 weather data
- [x] Add locations data to weather.json
- [x] Add VAD-PLANT-01 location data
- [x] Add MUM-SITE-01 location data
- [x] Verify fixture JSON structure

### 0.4 Create Factory Classes - done
- [x] Create WeatherClientFactory class
- [x] Add get_client method
- [x] Return FixtureWeatherClient for static mode
- [x] Return OpenMeteoClient for dynamic mode
- [x] Create LocationServiceFactory class
- [x] Add get_service method
- [x] Return StaticLocationService for static mode
- [x] Return OSMLocationService for dynamic mode
- [x] Create AIServiceFactory class
- [x] Add get_service method
- [x] Return RuleBasedAIService for static mode
- [x] Return GeminiAIService for dynamic mode

## Phase 1: Database Setup

### 1.1 Database Migration - migration file created
- [x] Create migration file for weather_safety_rules table
- [x] Create migration file for schedule_change_requests table
- [x] Create migration file for location_cache table
- [x] Add weather_safe column to assignments table
- [x] Add weather_status column to assignments table
- [x] Add weather_assessment column to assignments table
- [x] Add weather_context column to requests table
- [x] Add original_assignment_time column to requests table
- [x] Add suggested_assignment_time column to requests table
- [x] Add osm_display_name column to sites table
- [x] Create index on weather_safety_rules.rule_type
- [x] Create index on weather_safety_rules.active
- [x] Create index on schedule_change_requests.user_id
- [x] Create index on schedule_change_requests.assignment_id
- [x] Create index on schedule_change_requests.status
- [x] Create index on schedule_change_requests.supervisor_id
- [x] Create index on schedule_change_requests.created_on
- [x] Create index on schedule_change_requests.active
- [x] Create index on location_cache.query
- [x] Create index on location_cache.latitude and longitude
- [x] Create index on location_cache.last_accessed
- [x] Create index on location_cache.active
- [x] Create index on assignments.weather_safe
- [x] Create index on assignments.weather_status
- [x] Create index on requests.request_type where weather_change
- [x] Create index on sites.osm_display_name
- [x] Add check constraint for assignments.weather_status
- [x] Add check constraint for schedule_change_requests.status
- [x] Add check constraint for schedule_change_requests.urgency
- [x] Add check constraint for schedule_change_requests.weather_status
- [x] Add foreign key constraint for schedule_change_requests.user_id
- [x] Add foreign key constraint for schedule_change_requests.assignment_id
- [x] Add foreign key constraint for schedule_change_requests.supervisor_id
- [ ] Run migration script on database (manual: psql -U user -d db -f migrations/001_hackathon_schema_updates.sql)
- [ ] Verify weather_safety_rules table exists (manual)
- [ ] Verify schedule_change_requests table exists (manual)
- [ ] Verify location_cache table exists (manual)
- [ ] Verify assignments table has new columns (manual)
- [ ] Verify requests table has new columns (manual)
- [ ] Verify sites table has new column (manual)
- [ ] Verify all indexes created (manual)

### 1.2 Seed Demo Data - seed file created
- [x] Insert demo user: rahul
- [x] Insert demo user: amit
- [x] Insert demo user: supervisor1
- [x] Insert demo site: VAD-PLANT-01
- [x] Insert demo site: MUM-SITE-01
- [x] Insert demo assignment for rahul
- [x] Insert demo assignment for amit
- [x] Insert weather safety rules for heat
- [x] Insert weather safety rules for rain
- [x] Insert weather safety rules for wind
- [x] Insert weather safety rules for visibility
- [x] Insert location cache for Mumbai
- [x] Insert location cache for Vadodara
- [ ] Run seed script on database (manual: psql -U user -d db -f migrations/002_seed_demo_data.sql)
- [ ] Verify demo users exist (manual)
- [ ] Verify demo sites exist (manual)
- [ ] Verify demo assignments exist (manual)
- [ ] Verify weather safety rules exist (manual)
- [ ] Verify location cache entries exist (manual)

---

## Phase 2: AI Agent - Weather Safety Assessor

### 2.1 Create Module Structure
- [ ] Create directory: src/workforce_agent/ai
- [ ] Create file: src/workforce_agent/ai/__init__.py
- [ ] Create file: src/workforce_agent/ai/weather_safety.py
- [ ] Export WeatherSafetyAssessor in __init__.py
- [ ] Export WeatherCondition in __init__.py
- [ ] Export SafetyStatus in __init__.py

### 2.2 Implement WeatherCondition Model
- [ ] Import BaseModel from pydantic
- [ ] Create WeatherCondition class
- [ ] Add temperature_c field
- [ ] Add precipitation_percent field
- [ ] Add wind_speed_kmh field
- [ ] Add visibility_km field
- [ ] Add humidity_percent field

### 2.3 Implement SafetyStatus Model
- [ ] Create SafetyStatus class
- [ ] Add status field (Literal)
- [ ] Add is_safe field (boolean)
- [ ] Add reason field (string)
- [ ] Add recommendations field (list of strings)

### 2.4 Implement WeatherSafetyAssessor Class
- [ ] Create WeatherSafetyAssessor class
- [ ] Define HEAT_SAFE constant (32.0)
- [ ] Define HEAT_CAUTION constant (35.0)
- [ ] Define HEAT_WARNING constant (40.0)
- [ ] Define RAIN_SAFE constant (20.0)
- [ ] Define RAIN_CAUTION constant (40.0)
- [ ] Define RAIN_WARNING constant (60.0)
- [ ] Define WIND_SAFE constant (20.0)
- [ ] Define WIND_CAUTION constant (30.0)
- [ ] Define WIND_WARNING constant (50.0)
- [ ] Define VISIBILITY_SAFE constant (5.0)
- [ ] Define VISIBILITY_CAUTION constant (2.0)
- [ ] Define VISIBILITY_WARNING constant (1.0)

### 2.5 Implement Temperature Check
- [ ] Add temperature > HEAT_WARNING check
- [ ] Set status to SEVERE for extreme heat
- [ ] Add temperature > HEAT_CAUTION check
- [ ] Set status to WARNING for high heat
- [ ] Add temperature > HEAT_SAFE check
- [ ] Set status to CAUTION for warm

### 2.6 Implement Precipitation Check
- [ ] Add precipitation > RAIN_WARNING check
- [ ] Set status to SEVERE for heavy rain
- [ ] Add precipitation > RAIN_CAUTION check
- [ ] Set status to WARNING for rain likely
- [ ] Add precipitation > RAIN_SAFE check
- [ ] Set status to CAUTION for light rain

### 2.7 Implement Wind Check
- [ ] Add wind > WIND_WARNING check
- [ ] Set status to SEVERE for strong wind
- [ ] Add wind > WIND_CAUTION check
- [ ] Set status to WARNING for windy
- [ ] Add wind > WIND_SAFE check
- [ ] Set status to CAUTION for moderate wind

### 2.8 Implement Visibility Check
- [ ] Add visibility < VISIBILITY_WARNING check
- [ ] Set status to SEVERE for poor visibility
- [ ] Add visibility < VISIBILITY_CAUTION check
- [ ] Set status to WARNING for reduced visibility
- [ ] Add visibility < VISIBILITY_SAFE check
- [ ] Set status to CAUTION for limited visibility

### 2.9 Implement Recommendations
- [ ] Add SAFE recommendations
- [ ] Add CAUTION recommendations
- [ ] Add WARNING recommendations
- [ ] Add SEVERE recommendations
- [ ] Add hydration recommendation for heat
- [ ] Add waterproof gear recommendation for rain

### 2.10 Test Weather Safety Assessor
- [ ] Write test for safe conditions
- [ ] Write test for heat warning
- [ ] Write test for heat severe
- [ ] Write test for rain warning
- [ ] Write test for wind warning
- [ ] Write test for visibility warning
- [ ] Run all tests
- [ ] Verify all tests pass

---

## Phase 3: AI Agent - Schedule Checker

### 3.1 Create Schedule Checker File
- [ ] Create file: src/workforce_agent/ai/schedule_checker.py

### 3.2 Implement Assignment Model
- [ ] Create Assignment class
- [ ] Add id field
- [ ] Add user_id field
- [ ] Add site_id field
- [ ] Add start_time field
- [ ] Add end_time field
- [ ] Add description field

### 3.3 Implement FreeSlot Model
- [ ] Create FreeSlot class
- [ ] Add start field
- [ ] Add end field
- [ ] Add duration_minutes field

### 3.4 Implement ScheduleChecker Class
- [ ] Create ScheduleChecker class
- [ ] Add __init__ method with db_client parameter
- [ ] Store db_client as instance variable

### 3.5 Implement get_assignments Method
- [ ] Create get_assignments method
- [ ] Add user_id parameter
- [ ] Add date parameter
- [ ] Write SQL query for assignments
- [ ] Filter by user_id
- [ ] Filter by date
- [ ] Filter by active status
- [ ] Exclude cancelled and completed
- [ ] Order by start_time
- [ ] Execute query
- [ ] Convert rows to Assignment objects
- [ ] Return list of assignments

### 3.6 Implement find_free_slots Method
- [ ] Create find_free_slots method
- [ ] Add user_id parameter
- [ ] Add date parameter
- [ ] Add duration_minutes parameter
- [ ] Add work_start_hour parameter (default 6)
- [ ] Add work_end_hour parameter (default 20)
- [ ] Call get_assignments
- [ ] Calculate busy intervals
- [ ] Define start_of_day
- [ ] Define end_of_day
- [ ] Call _find_gaps method
- [ ] Return free slots

### 3.7 Implement _find_gaps Method
- [ ] Create _find_gaps method
- [ ] Add start parameter
- [ ] Add end parameter
- [ ] Add busy_intervals parameter
- [ ] Add min_duration_minutes parameter
- [ ] Sort busy intervals by start time
- [ ] Initialize gaps list
- [ ] Initialize current_start
- [ ] Loop through busy intervals
- [ ] Check for gap before busy interval
- [ ] Calculate gap duration
- [ ] Add gap if duration sufficient
- [ ] Update current_start
- [ ] Check for gap after last interval
- [ ] Calculate final gap duration
- [ ] Add final gap if sufficient
- [ ] Return gaps list

### 3.8 Implement is_slot_available Method
- [ ] Create is_slot_available method
- [ ] Add user_id parameter
- [ ] Add start parameter
- [ ] Add end parameter
- [ ] Call get_assignments
- [ ] Loop through assignments
- [ ] Check for overlap
- [ ] Return false if overlap found
- [ ] Return true if no overlap

### 3.9 Test Schedule Checker
- [ ] Write test for get_assignments
- [ ] Write test for find_free_slots
- [ ] Write test for _find_gaps
- [ ] Write test for is_slot_available
- [ ] Run all tests
- [ ] Verify all tests pass

---

## Phase 4: AI Agent - Location Service

### 4.1 Create Location Service File
- [ ] Create file: src/workforce_agent/ai/location_service.py
- [ ] Import settings from config
- [ ] Import BaseModel from pydantic

### 4.2 Implement Location Model
- [ ] Create Location class
- [ ] Add latitude field
- [ ] Add longitude field
- [ ] Add display_name field
- [ ] Add city field
- [ ] Add state field
- [ ] Add country field

### 4.3 Implement StaticLocationService Class
- [ ] Create StaticLocationService class
- [ ] Add __init__ method
- [ ] Add _load_static_locations method
- [ ] Load locations from fixture file
- [ ] Implement geocode method (static)
- [ ] Search fixture data for address
- [ ] Return Location object if found
- [ ] Return None if not found
- [ ] Implement calculate_distance method
- [ ] Add Haversine formula
- [ ] Return distance in km

### 4.4 Implement OSMLocationService Class
- [ ] Create OSMLocationService class
- [ ] Define OSM_NOMINATIM_BASE constant
- [ ] Add __init__ method
- [ ] Initialize httpx.AsyncClient
- [ ] Set User-Agent header
- [ ] Implement geocode method (OSM)
- [ ] Add address parameter
- [ ] Build request params
- [ ] Make HTTP GET request to OSM
- [ ] Set timeout from settings
- [ ] Check for errors
- [ ] Parse response JSON
- [ ] Extract first result
- [ ] Create Location object
- [ ] Return Location object
- [ ] Return None on error
- [ ] Implement calculate_distance method
- [ ] Add Haversine formula
- [ ] Return distance in km
- [ ] Implement close method
- [ ] Close HTTP client
- [ ] Mark as async

### 4.5 Implement LocationServiceFactory
- [ ] Create LocationServiceFactory class
- [ ] Add get_service static method
- [ ] Check settings.location_source
- [ ] Return StaticLocationService for static
- [ ] Return OSMLocationService for osm
- [ ] Raise error for unknown source

### 4.6 Test Location Service
- [ ] Write test for StaticLocationService
- [ ] Write test for OSMLocationService
- [ ] Write test for calculate_distance
- [ ] Write test for factory
- [ ] Run all tests
- [ ] Verify all tests pass

---

## Phase 5: AI Agent - Time Suggester

### 5.1 Create Time Suggester File
- [ ] Create file: src/workforce_agent/ai/time_suggester.py

### 5.2 Implement TimeSlot Model
- [ ] Create TimeSlot class
- [ ] Add start field
- [ ] Add end field
- [ ] Add weather_condition field
- [ ] Add safety_status field
- [ ] Add is_available field

### 5.3 Implement TimeSuggester Class
- [ ] Create TimeSuggester class
- [ ] Add __init__ method
- [ ] Add weather_client parameter
- [ ] Add schedule_checker parameter
- [ ] Store as instance variables

### 5.4 Implement suggest_safe_times Method
- [ ] Create suggest_safe_times method
- [ ] Add location_id parameter
- [ ] Add user_id parameter
- [ ] Add duration_hours parameter
- [ ] Add preferred_date parameter
- [ ] Add max_suggestions parameter (default 5)
- [ ] Get hourly weather forecast
- [ ] Get user's existing assignments
- [ ] Calculate busy intervals
- [ ] Find all possible time slots
- [ ] Filter for safe weather only
- [ ] Sort by safety status
- [ ] Return top suggestions

### 5.5 Implement _calculate_busy_intervals Method
- [ ] Create _calculate_busy_intervals method
- [ ] Add assignments parameter
- [ ] Initialize intervals list
- [ ] Loop through assignments
- [ ] Extract start and end times
- [ ] Add to intervals list
- [ ] Return intervals

### 5.6 Implement _find_time_slots Method
- [ ] Create _find_time_slots method
- [ ] Add weather_forecast parameter
- [ ] Add busy_intervals parameter
- [ ] Add duration_hours parameter
- [ ] Add date parameter
- [ ] Convert duration to minutes
- [ ] Define start_of_day (6 AM)
- [ ] Define end_of_day (8 PM)
- [ ] Initialize current_time
- [ ] Loop through day
- [ ] Calculate end_time
- [ ] Check availability
- [ ] Get weather for slot
- [ ] Assess safety
- [ ] Create TimeSlot object
- [ ] Add to slots list
- [ ] Increment current_time
- [ ] Return slots list

### 5.7 Implement _overlaps_with_busy Method
- [ ] Create _overlaps_with_busy method
- [ ] Add start parameter
- [ ] Add end parameter
- [ ] Add busy_intervals parameter
- [ ] Loop through busy intervals
- [ ] Check for overlap
- [ ] Return true if overlap
- [ ] Return false if no overlap

### 5.8 Implement _get_weather_for_slot Method
- [ ] Create _get_weather_for_slot method
- [ ] Add start parameter
- [ ] Add end parameter
- [ ] Add weather_forecast parameter
- [ ] Initialize slot_weather list
- [ ] Initialize current time
- [ ] Loop through slot duration
- [ ] Find weather at time
- [ ] Add to slot_weather
- [ ] Increment current time
- [ ] Check if weather data exists
- [ ] Return safe defaults if no data
- [ ] Calculate average temperature
- [ ] Calculate average precipitation
- [ ] Calculate average wind
- [ ] Calculate average visibility
- [ ] Calculate average humidity
- [ ] Return WeatherCondition object

### 5.9 Implement _find_weather_at_time Method
- [ ] Create _find_weather_at_time method
- [ ] Add time parameter
- [ ] Add forecast parameter
- [ ] Loop through forecast
- [ ] Check hour match
- [ ] Return weather if match
- [ ] Return None if no match

### 5.10 Test Time Suggester
- [ ] Write test for suggest_safe_times
- [ ] Write test for _find_time_slots
- [ ] Write test for _get_weather_for_slot
- [ ] Run all tests
- [ ] Verify all tests pass

---

## Phase 6: API Endpoints

### 6.1 Import AI Components
- [ ] Import WeatherSafetyAssessor in api.py
- [ ] Import WeatherCondition in api.py
- [ ] Import SafetyStatus in api.py
- [ ] Import ScheduleChecker in api.py
- [ ] Import LocationService in api.py
- [ ] Import TimeSuggester in api.py

### 6.2 Initialize AI Services
- [ ] Initialize location_service
- [ ] Initialize schedule_checker
- [ ] Initialize time_suggester

### 6.3 Implement weather-assess Endpoint
- [ ] Create POST /api/ai/weather-assess endpoint
- [ ] Add location_id parameter
- [ ] Add start_time parameter
- [ ] Add end_time parameter
- [ ] Get weather data from weather_client
- [ ] Convert to WeatherCondition
- [ ] Call WeatherSafetyAssessor.assess
- [ ] Return status response
- [ ] Test endpoint with curl

### 6.4 Implement geocode Endpoint
- [ ] Create POST /api/ai/geocode endpoint
- [ ] Add address parameter
- [ ] Call location_service.geocode
- [ ] Check if location found
- [ ] Return location data
- [ ] Return 404 if not found
- [ ] Test endpoint with curl

### 6.5 Implement calculate-distance Endpoint
- [ ] Create POST /api/ai/calculate-distance endpoint
- [ ] Add from_lat parameter
- [ ] Add from_lon parameter
- [ ] Add to_lat parameter
- [ ] Add to_lon parameter
- [ ] Call location_service.calculate_distance
- [ ] Return distance response
- [ ] Test endpoint with curl

### 6.6 Implement suggest-times Endpoint
- [ ] Create POST /api/ai/suggest-times endpoint
- [ ] Add location_id parameter
- [ ] Add user_id parameter
- [ ] Add duration_hours parameter
- [ ] Add preferred_date parameter
- [ ] Call time_suggester.suggest_safe_times
- [ ] Return suggestions response
- [ ] Test endpoint with curl

### 6.7 Update AI Module __init__.py
- [ ] Export WeatherSafetyAssessor
- [ ] Export WeatherCondition
- [ ] Export SafetyStatus
- [ ] Export ScheduleChecker
- [ ] Export LocationService
- [ ] Export TimeSuggester

---

## Phase 7: Frontend - Employee UI

### 7.1 Create Employee Page Structure
- [ ] Create directory: frontend/src/pages/employee
- [ ] Create file: frontend/src/pages/employee/SchedulePage.tsx

### 7.2 Implement SchedulePage Component
- [ ] Import React
- [ ] Import useState
- [ ] Import useEffect
- [ ] Create SchedulePage component
- [ ] Add assignments state
- [ ] Add loading state
- [ ] Add useEffect hook
- [ ] Call loadAssignments on mount
- [ ] Return loading div if loading
- [ ] Return schedule div if loaded

### 7.3 Implement loadAssignments Function
- [ ] Create loadAssignments function
- [ ] Try fetch assignments
- [ ] Set assignments state
- [ ] Catch errors
- [ ] Set loading to false

### 7.4 Implement AssignmentCard Component
- [ ] Create AssignmentCard component
- [ ] Add assignment prop
- [ ] Extract safety_status
- [ ] Get status color
- [ ] Return card div
- [ ] Add card header
- [ ] Add card body
- [ ] Add card footer
- [ ] Add status badge
- [ ] Add warning text if unsafe
- [ ] Add request change button if unsafe
- [ ] Add view details button

### 7.5 Implement getStatusColor Function
- [ ] Create getStatusColor function
- [ ] Add status parameter
- [ ] Return 'status-safe' for SAFE
- [ ] Return 'status-caution' for CAUTION
- [ ] Return 'status-warning' for WARNING
- [ ] Return 'status-severe' for SEVERE
- [ ] Return empty string for unknown

### 7.6 Add CSS Styles
- [ ] Add .status-safe class
- [ ] Add .status-caution class
- [ ] Add .status-warning class
- [ ] Add .status-severe class
- [ ] Add .card class
- [ ] Add .card-header class
- [ ] Add .card-body class
- [ ] Add .card-footer class
- [ ] Add .btn class
- [ ] Add .btn-danger class
- [ ] Add .btn-secondary class
- [ ] Add .warning-text class

### 7.7 Create Types File
- [ ] Create file: frontend/src/types/types.ts
- [ ] Define Assignment interface
- [ ] Define WeatherCondition interface
- [ ] Define SafetyStatus interface
- [ ] Define ScheduleChangeRequest interface

### 7.8 Create API Service
- [ ] Create file: frontend/src/services/aiService.ts
- [ ] Import axios
- [ ] Define API_BASE_URL
- [ ] Create aiService object
- [ ] Add assessWeather method
- [ ] Add getSuggestions method
- [ ] Add submitChangeRequest method
- [ ] Export aiService

### 7.9 Test Employee UI
- [ ] Start frontend dev server
- [ ] Navigate to /employee/schedule
- [ ] Verify page loads
- [ ] Verify assignments display
- [ ] Verify status badges show
- [ ] Verify buttons work

---

## Phase 8: Frontend - Supervisor UI

### 8.1 Create Supervisor Page Structure
- [ ] Create directory: frontend/src/pages/supervisor
- [ ] Create file: frontend/src/pages/supervisor/RequestsPage.tsx

### 8.2 Implement RequestsPage Component
- [ ] Import React
- [ ] Import useState
- [ ] Import useEffect
- [ ] Create RequestsPage component
- [ ] Add requests state
- [ ] Add loading state
- [ ] Add useEffect hook
- [ ] Call loadRequests on mount
- [ ] Return loading div if loading
- [ ] Return requests div if loaded

### 8.3 Implement loadRequests Function
- [ ] Create loadRequests function
- [ ] Call aiService.getSupervisorRequests
- [ ] Set requests state
- [ ] Catch errors
- [ ] Set loading to false

### 8.4 Implement handleApprove Function
- [ ] Create handleApprove function
- [ ] Add requestId parameter
- [ ] Call aiService.approveRequest
- [ ] Call loadRequests to refresh
- [ ] Catch errors

### 8.5 Implement handleReject Function
- [ ] Create handleReject function
- [ ] Add requestId parameter
- [ ] Call aiService.rejectRequest
- [ ] Call loadRequests to refresh
- [ ] Catch errors

### 8.6 Implement RequestCard Component
- [ ] Create RequestCard component
- [ ] Add request prop
- [ ] Add onApprove prop
- [ ] Add onReject prop
- [ ] Return card div
- [ ] Add card header
- [ ] Add card body
- [ ] Add card footer
- [ ] Display employee name
- [ ] Display assignment
- [ ] Display original time
- [ ] Display weather
- [ ] Display suggested time
- [ ] Display reason
- [ ] Add approve button
- [ ] Add reject button
- [ ] Add view details button

### 8.7 Add Supervisor Types
- [ ] Add SupervisorRequest interface to types.ts
- [ ] Add all required fields

### 8.8 Add Supervisor API Methods
- [ ] Add getSupervisorRequests to aiService
- [ ] Add approveRequest to aiService
- [ ] Add rejectRequest to aiService

### 8.9 Test Supervisor UI
- [ ] Navigate to /supervisor/requests
- [ ] Verify page loads
- [ ] Verify requests display
- [ ] Verify approve button works
- [ ] Verify reject button works
- [ ] Verify refresh after action

---

## Phase 9: Demo Preparation

### 9.1 Create Demo Scenario
- [ ] Update assignment with extreme heat
- [ ] Set weather to 42°C
- [ ] Set weather_safe to false
- [ ] Set weather_status to SEVERE
- [ ] Add weather_assessment JSON
- [ ] Create schedule change request
- [ ] Set original time to 2 PM
- [ ] Set suggested time to 6 PM
- [ ] Set original weather to 42°C
- [ ] Set suggested weather to 32°C
- [ ] Set reason text
- [ ] Set urgency to high
- [ ] Set status to pending

### 9.2 Verify Demo Data
- [ ] Check assignment has extreme heat
- [ ] Check request is pending
- [ ] Check AI suggestion is correct
- [ ] Verify in employee view
- [ ] Verify in supervisor view

### 9.3 Practice Demo Script
- [ ] Practice Scene 1: The Problem
- [ ] Practice Scene 2: The Solution
- [ ] Practice Scene 3: Supervisor Review
- [ ] Practice Scene 4: The Result
- [ ] Time each scene
- [ ] Refine transitions

### 9.4 Prepare Pitch Deck
- [ ] Create slide 1: Problem
- [ ] Create slide 2: Solution
- [ ] Create slide 3: Demo
- [ ] Create slide 4: Impact
- [ ] Add speaker notes
- [ ] Practice presentation

---

## Phase 10: Final Polish

### 10.1 Performance Optimization
- [ ] Add weather data caching
- [ ] Optimize database queries
- [ ] Add loading states to UI
- [ ] Add error boundaries
- [ ] Test page load time

### 10.2 Mobile Responsiveness
- [ ] Add mobile breakpoint CSS
- [ ] Test on mobile view
- [ ] Adjust card padding for mobile
- [ ] Stack buttons vertically on mobile
- [ ] Test on actual mobile device

### 10.3 Accessibility
- [ ] Add ARIA labels to buttons
- [ ] Add alt text to images
- [ ] Ensure keyboard navigation works
- [ ] Use semantic HTML
- [ ] Test with screen reader

### 10.4 Error Handling
- [ ] Add try-catch to all API calls
- [ ] Add error messages to UI
- [ ] Add retry logic
- [ ] Add loading indicators
- [ ] Test error scenarios

### 10.5 Documentation
- [ ] Update README with demo steps
- [ ] Add API documentation
- [ ] Create user guide
- [ ] Document deployment steps
- [ ] Add troubleshooting section

### 10.6 Final Testing
- [ ] Run all backend tests
- [ ] Run all frontend tests
- [ ] Test complete user flow
- [ ] Test demo scenario
- [ ] Check for console errors
- [ ] Verify no critical bugs

### 10.7 Deployment Preparation
- [ ] Build frontend for production
- [ ] Test production build
- [ ] Prepare environment variables
- [ ] Document deployment steps
- [ ] Create deployment checklist

---

## Total Tasks: 350+

**Estimated Time:** 10 days (35 tasks/day)

**Progress Tracking:** Mark each task as complete with [x] when done.

**Configuration Note:** All tasks support static mode (no external dependencies). External services can be added later via environment variables. See [HACKATHON_CONFIGURATION.md](HACKATHON_CONFIGURATION.md) for details.
