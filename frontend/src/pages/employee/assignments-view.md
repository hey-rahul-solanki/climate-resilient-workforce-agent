# Employee - Assignments View

## Overview
Display all assignments assigned to the employee in a tabular format with weather information and advisory for each assignment.

## Layout
- Tab navigation at the top (Assignments, Weather)
- Main content area with a data table

## Table Columns

### Assignment Information
| Column | Description | Data Type |
|--------|-------------|-----------|
| Assignment ID | Unique identifier | String |
| Project/Task | Name of project or task | String |
| Site | Location of assignment | String |
| Start Date | Assignment start date | Date |
| End Date | Assignment end date | Date |
| Shift | Morning/Evening/Night | Enum |
| Status | Scheduled/In Progress/Completed/Cancelled | Enum |
| Priority | High/Medium/Low | Enum |
| Hours Allocated | Total hours assigned | Number |
| Hours Completed | Hours worked so far | Number |
| Supervisor | Name of supervisor | String |
| Team Members | Other members on same assignment | Array(String) |
| Description | Assignment details | String |
| Notes | Additional notes | String |

### Weather Information Column
| Column | Description | Data Type |
|--------|-------------|-----------|
| Weather Condition | Current weather at site | String |
| Temperature | Current temperature | Number (°C/°F) |
| Weather Advisory | Safety advisory based on conditions | String |
| Forecast | Short forecast for assignment period | String |
| Alert Level | Normal/Caution/Warning/Severe | Enum |

### Actions Column
| Action | Description |
|---------|-------------|
| View Best Time | Opens modal showing optimal work times based on weather |
| Share with Supervisor | Share weather concerns with supervisor |
| Request Change | Request schedule/assignment change |

## Weather Advisory Levels
Color-coded advisory levels:
- **Green (Normal)**: Safe working conditions
- **Yellow (Caution)**: Light rain, moderate wind - proceed with caution
- **Orange (Warning)**: Heavy rain, strong wind - consider rescheduling
- **Red (Severe)**: Storm, extreme conditions - avoid work

## Best Time Modal

### Overview
Shows optimal work time windows based on weather forecast for the assignment site.

### Display
- **Current Date/Time**: Real-time clock
- **Weather Timeline**: Visual timeline showing weather conditions throughout the day
- **Recommended Time Slots**: Highlighted optimal time windows
- **Conditions Breakdown**: Detailed weather conditions for each time slot
  - Temperature
  - Precipitation chance
  - Wind speed
  - UV index
  - Visibility

### Time Slot Details
| Time Slot | Weather | Temp | Precipitation | Wind | Recommendation |
|-----------|---------|------|---------------|------|----------------|
| 6:00 AM - 9:00 AM | Sunny | 22°C | 0% | 5 km/h | Excellent |
| 9:00 AM - 12:00 PM | Partly Cloudy | 25°C | 10% | 8 km/h | Good |
| 12:00 PM - 3:00 PM | Cloudy | 24°C | 30% | 12 km/h | Fair |
| 3:00 PM - 6:00 PM | Light Rain | 20°C | 60% | 15 km/h | Poor |

### Actions in Modal
- **Select Time Slot**: Choose preferred time for assignment
- **Request Schedule Change**: Send request to supervisor with selected time
- **Add to Calendar**: Add optimal time to personal calendar
- **Share**: Share weather info with team members

## Share with Supervisor

### Form
- **Pre-filled Information**: Assignment ID, Site, Date
- **Weather Concern**: Dropdown (Too hot, Too cold, Rain expected, Windy, Other)
- **Message**: Text area for detailed concern
- **Suggested Alternative**: Optional alternative time or date
- **Urgency**: Urgent/High/Medium/Low

### Submission
- Sends notification to supervisor
- Creates a request in supervisor's requests view
- Provides confirmation to employee

## Request Change

### Change Type Options
- **Reschedule**: Request different date/time
- **Reassign**: Request different site/assignment
- **Cancel**: Request cancellation (with reason)

### Form Fields
- **Change Type**: Dropdown selection
- **Reason**: Text area for justification
- **Preferred Date/Time**: Date/time picker
- **Alternative Assignment**: If requesting reassignment
- **Attachments**: Upload supporting documents (medical certificate, etc.)
- **Urgency**: Urgent/High/Medium/Low

## Filtering Options
- Filter by status
- Filter by priority
- Filter by site
- Filter by date range
- Filter by weather alert level

## Assignment Details Modal
- Full assignment information
- Site location map
- Detailed weather forecast
- Team member contact information
- Related tasks and milestones
- Safety guidelines for the site
- Equipment requirements
- Progress tracking

## UI Components
- Tab navigation
- Data table with sorting and filtering
- Weather icons and indicators
- Color-coded advisory badges
- Modal for best time analysis
- Modal for request forms
- Share button
- Status badges
- Priority badges
- Pagination
- Date range picker
- Temperature unit toggle (°C/°F)

## Notifications
- New assignment notification
- Assignment reminder (before start)
- Weather alert notification for assignment
- Supervisor response to request
- Schedule change confirmation

## API Endpoints (Tentative)

**Authentication**: All endpoints require JWT authentication. Employee ID is extracted from the token, no need to pass in payload.

- `GET /api/employee/assignments` - Get all assignments for the authenticated employee
  - Query params: `?status=in_progress&site=site_id&priority=high&start_date=2024-01-01&end_date=2024-12-31&page=1&limit=20`
- `GET /api/employee/assignments/{id}` - Get assignment details
  - Path param: `id` - Assignment ID
- `GET /api/employee/assignments/{id}/weather` - Get weather for assignment site
  - Path param: `id` - Assignment ID
  - Query params: `?unit=celsius|fahrenheit`
- `GET /api/employee/assignments/{id}/best-times` - Get optimal work times based on weather
  - Path param: `id` - Assignment ID
  - Query params: `?date=2024-01-15`
- `POST /api/employee/assignments/{id}/share` - Share weather concern with supervisor
  - Path param: `id` - Assignment ID
  - Body: `{ concern_type: "too_hot|too_cold|rain_expected|windy|other", message: "Concern details", suggested_alternative: "2024-01-16 09:00", urgency: "high" }`
- `POST /api/employee/assignments/{id}/request-change` - Request schedule/assignment change
  - Path param: `id` - Assignment ID
  - Body: `{ change_type: "reschedule|reassign|cancel", reason: "Justification", preferred_date_time: "2024-01-16 09:00", alternative_assignment: "assignment_id", urgency: "high" }`
- `GET /api/employee/assignments/search` - Search assignments
  - Query params: `?q=search_term&field=project/site/description`
