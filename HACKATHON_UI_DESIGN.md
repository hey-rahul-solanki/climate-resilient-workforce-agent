# Simplified UI Design for Hackathon

## Design Philosophy

**Keep it simple. No flashy UI. Focus on clarity and speed.**

- **Employee**: See schedule → Check weather → Request change (3 clicks max)
- **Supervisor**: See requests → Approve/Reject (2 clicks max)
- **Colors**: Green (safe), Red (unsafe), Yellow (caution)
- **Typography**: Large, readable text
- **Mobile-friendly**: Works on phone screens

---

## Employee UI: My Schedule

### Page: `/employee/schedule`

**Layout**: Single page, card-based layout

```
┌─────────────────────────────────────────────┐
│  My Today's Schedule          [Logout]      │
│  Wednesday, January 15, 2024                │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  ☀️ Site A - Maintenance                     │
│  Time: 9:00 AM - 11:00 AM                   │
│  Duration: 2 hours                           │
│                                              │
│  Weather: 28°C, Sunny                       │
│  Status: ✅ SAFE TO WORK                     │
│                                              │
│  [View Details]                              │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  🔥 Site B - Inspection                      │
│  Time: 2:00 PM - 4:00 PM                    │
│  Duration: 2 hours                           │
│                                              │
│  Weather: 42°C, Extreme Heat                 │
│  Status: ⚠️ UNSAFE - Extreme Heat           │
│                                              │
│  AI Suggestion:                              │
│  "Work at 6:00 PM instead (32°C)"           │
│                                              │
│  [Request Change to 6:00 PM]                │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  🌧️ Site C - Repair                         │
│  Time: 5:00 PM - 7:00 PM                    │
│  Duration: 2 hours                           │
│                                              │
│  Weather: 30°C, Light Rain (25%)            │
│  Status: ⚠️ CAUTION - Light Rain             │
│                                              │
│  Recommendation: Wear waterproof gear       │
│                                              │
│  [Proceed as Planned]  [Request Change]     │
└─────────────────────────────────────────────┘
```

### Components

#### Assignment Card
```typescript
interface AssignmentCardProps {
  id: string;
  site: string;
  task: string;
  startTime: string;
  endTime: string;
  duration: string;
  weather: {
    temperature: number;
    condition: string;
    precipitation: number;
  };
  safetyStatus: 'SAFE' | 'CAUTION' | 'WARNING' | 'SEVERE';
  isSafe: boolean;
  suggestedTime?: string;
}
```

#### Status Badge
```css
.status-safe {
  background: #d4edda;
  color: #155724;
  border: 2px solid #c3e6cb;
}

.status-caution {
  background: #fff3cd;
  color: #856404;
  border: 2px solid #ffeaa7;
}

.status-warning {
  background: #f8d7da;
  color: #721c24;
  border: 2px solid #f5c6cb;
}

.status-severe {
  background: #f5c6cb;
  color: #721c24;
  border: 2px solid #e02d2d;
}
```

### Request Change Modal

```
┌─────────────────────────────────────────────┐
│  Request Schedule Change        [X]        │
├─────────────────────────────────────────────┤
│                                              │
│  Assignment: Site B - Inspection            │
│  Current Time: 2:00 PM - 4:00 PM            │
│  Weather: 42°C (UNSAFE)                     │
│                                              │
│  AI Suggested Times:                        │
│                                              │
│  ◉ 6:00 PM - 8:00 PM (32°C, Sunny)          │
│  ○ 7:00 AM - 9:00 AM (28°C, Sunny)         │
│  ○ Tomorrow 9:00 AM - 11:00 AM (30°C)      │
│                                              │
│  Reason (optional):                         │
│  ┌──────────────────────────────────────┐  │
│  │ Too hot, worried about heat stroke    │  │
│  └──────────────────────────────────────┘  │
│                                              │
│  Urgency: ○ Normal  ◉ High                 │
│                                              │
│              [Cancel]  [Submit Request]     │
└─────────────────────────────────────────────┘
```

---

## Supervisor UI: Weather-Affected Requests

### Page: `/supervisor/requests`

**Layout**: Dashboard with request cards

```
┌─────────────────────────────────────────────┐
│  Weather-Affected Requests    [Logout]      │
│  5 Pending Requests                             │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  Weather Summary                             │
│  Active Alerts: 2                            │
│  Sites Affected: 3                           │
│  Workers Affected: 5                          │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  Request #1 - Rahul Sharma                   │
│  Assignment: Site B - Inspection              │
│  Original Time: 2:00 PM - 4:00 PM            │
│  Weather: 42°C (UNSAFE)                      │
│                                              │
│  AI Suggestion:                              │
│  6:00 PM - 8:00 PM (32°C, Sunny)             │
│  Reason: "Too hot, worried about heat stroke"│
│  Urgency: High                               │
│                                              │
│  [Approve]  [Reject]  [View Details]        │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  Request #2 - Amit Patel                     │
│  Assignment: Site C - Repair                  │
│  Original Time: 1:00 PM - 3:00 PM            │
│  Weather: 38°C (WARNING)                     │
│                                              │
│  AI Suggestion:                              │
│  5:00 PM - 7:00 PM (30°C, Cloudy)            │
│  Reason: "Wants to avoid peak heat"          │
│  Urgency: Medium                             │
│                                              │
│  [Approve]  [Reject]  [View Details]        │
└─────────────────────────────────────────────┘
```

### Components

#### Request Card
```typescript
interface RequestCardProps {
  id: string;
  employeeName: string;
  assignment: string;
  originalTime: string;
  weather: {
    temperature: number;
    status: string;
  };
  suggestedTime: string;
  suggestedWeather: {
    temperature: number;
    condition: string;
  };
  reason: string;
  urgency: 'Low' | 'Medium' | 'High';
}
```

#### Approval Modal
```
┌─────────────────────────────────────────────┐
│  Approve Schedule Change        [X]         │
├─────────────────────────────────────────────┤
│                                              │
│  Employee: Rahul Sharma                      │
│  Assignment: Site B - Inspection              │
│                                              │
│  Original: 2:00 PM - 4:00 PM (42°C)         │
│  New Time: 6:00 PM - 8:00 PM (32°C)         │
│                                              │
│  This will:                                  │
│  ✓ Update assignment time                   │
│  ✓ Notify employee                           │
│  ✓ Mark as approved                          │
│                                              │
│  Supervisor Note (optional):                 │
│  ┌──────────────────────────────────────┐  │
│  │ Approved - stay hydrated!            │  │
│  └──────────────────────────────────────┘  │
│                                              │
│              [Cancel]  [Confirm Approve]    │
└─────────────────────────────────────────────┘
```

---

## Color Scheme

### Primary Colors
```css
--color-primary: #2563eb;      /* Blue */
--color-success: #16a34a;      /* Green */
--color-warning: #ca8a04;      /* Yellow */
--color-danger: #dc2626;       /* Red */
--color-bg: #ffffff;           /* White */
--color-text: #1f2937;         /* Dark gray */
--color-text-light: #6b7280;  /* Light gray */
--color-border: #e5e7eb;       /* Border gray */
```

### Status Colors
```css
--status-safe-bg: #d4edda;
--status-safe-text: #155724;
--status-caution-bg: #fff3cd;
--status-caution-text: #856404;
--status-warning-bg: #f8d7da;
--status-warning-text: #721c24;
--status-severe-bg: #f5c6cb;
--status-severe-text: #721c24;
```

---

## Typography

```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;

/* Headings */
h1 { font-size: 24px; font-weight: 600; }
h2 { font-size: 20px; font-weight: 600; }
h3 { font-size: 18px; font-weight: 500; }

/* Body */
body { font-size: 16px; line-height: 1.5; }
p { font-size: 16px; }

/* Small text */
small { font-size: 14px; color: var(--color-text-light); }
```

---

## Layout Structure

### CSS Grid Layout
```css
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.card {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
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
```

---

## Responsive Design

### Mobile (< 768px)
```css
@media (max-width: 768px) {
  .container {
    padding: 10px;
  }

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

---

## File Structure

```
frontend/src/
├── pages/
│   ├── employee/
│   │   └── SchedulePage.tsx          # Employee schedule view
│   └── supervisor/
│       └── RequestsPage.tsx          # Supervisor requests view
├── components/
│   ├── AssignmentCard.tsx            # Assignment card component
│   ├── RequestCard.tsx               # Request card component
│   ├── StatusBadge.tsx               # Status badge component
│   ├── RequestChangeModal.tsx        # Request change modal
│   └── ApprovalModal.tsx             # Approval modal
├── services/
│   └── aiService.ts                  # AI agent API calls
└── types/
    └── types.ts                      # TypeScript types
```

---

## TypeScript Types

```typescript
// types.ts

export interface WeatherCondition {
  temperature_c: number;
  precipitation_percent: number;
  wind_speed_kmh: number;
  visibility_km: number;
  humidity_percent: number;
}

export interface SafetyStatus {
  status: 'SAFE' | 'CAUTION' | 'WARNING' | 'SEVERE';
  is_safe: boolean;
  reason: string;
  recommendations: string[];
}

export interface Assignment {
  id: string;
  site: string;
  task: string;
  start_time: string;
  end_time: string;
  duration: string;
  weather: WeatherCondition;
  safety_status: SafetyStatus;
  suggested_time?: string;
}

export interface TimeSuggestion {
  start: string;
  end: string;
  weather: WeatherCondition;
  safety_status: SafetyStatus;
  is_available: boolean;
}

export interface ScheduleChangeRequest {
  assignment_id: string;
  suggested_time: string;
  reason: string;
  urgency: 'Low' | 'Medium' | 'High';
}

export interface SupervisorRequest {
  id: string;
  employee_name: string;
  assignment: string;
  original_time: string;
  weather: WeatherCondition;
  suggested_time: string;
  suggested_weather: WeatherCondition;
  reason: string;
  urgency: 'Low' | 'Medium' | 'High';
}
```

---

## API Service

```typescript
// services/aiService.ts

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const aiService = {
  // Assess weather safety
  async assessWeather(locationId: string, startTime: string, endTime: string) {
    const response = await axios.post(`${API_BASE_URL}/api/ai/weather-assess`, {
      location_id: locationId,
      start_time: startTime,
      end_time: endTime
    });
    return response.data;
  },

  // Get time suggestions
  async getSuggestions(locationId: string, userId: string, durationHours: number, date: string) {
    const response = await axios.post(`${API_BASE_URL}/api/ai/suggest-times`, {
      location_id: locationId,
      user_id: userId,
      duration_hours: durationHours,
      preferred_date: date
    });
    return response.data.suggested_times;
  },

  // Submit schedule change request
  async submitChangeRequest(request: ScheduleChangeRequest) {
    const response = await axios.post(`${API_BASE_URL}/api/employee/assignments/${request.assignment_id}/request-change`, request);
    return response.data;
  },

  // Get supervisor requests
  async getSupervisorRequests() {
    const response = await axios.get(`${API_BASE_URL}/api/supervisor/requests?status=pending`);
    return response.data.data;
  },

  // Approve request
  async approveRequest(requestId: string, note?: string) {
    const response = await axios.post(`${API_BASE_URL}/api/supervisor/requests/${requestId}/approve`, {
      reason: note
    });
    return response.data;
  },

  // Reject request
  async rejectRequest(requestId: string, reason: string) {
    const response = await axios.post(`${API_BASE_URL}/api/supervisor/requests/${requestId}/reject`, {
      reason
    });
    return response.data;
  }
};
```

---

## Next Steps

1. Create basic HTML/CSS layout (no React initially)
2. Build assignment card component
3. Add status badges
4. Create request change modal
5. Build supervisor request card
6. Add approval modal
7. Connect to AI agent API
8. Test full flow
9. Add responsive design
10. Polish and optimize
