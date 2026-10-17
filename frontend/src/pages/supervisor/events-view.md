# Supervisor - Events View

## Overview
Display all events scheduled for members working under the supervisor.

## Layout
- Tab navigation at the top (Members, Events, Weather, Requests)
- Main content area with a data table or calendar view

## Table Columns

### Event Information
| Column | Description | Data Type |
|--------|-------------|-----------|
| Event ID | Unique identifier | String |
| Event Name | Title of the event | String |
| Member | Name of assigned member | String |
| Member ID | Employee ID of member | String |
| Event Type | Training/Meeting/Inspection/Emergency Drill | Enum |
| Start Date/Time | Event start timestamp | DateTime |
| End Date/Time | Event end timestamp | DateTime |
| Location | Event location | String |
| Site | Associated site | String |
| Status | Scheduled/In Progress/Completed/Cancelled | Enum |
| Priority | High/Medium/Low | Enum |
| Attendance | Expected vs Actual | Object |
| Description | Event details | String |
| Created By | Who created the event | String |
| Created Date | When event was created | DateTime |

### Actions Column
| Action | Description |
|---------|-------------|
| View Details | Opens modal with full event details |
| Edit | Edit event details (if permitted) |
| Cancel | Cancel event (if permitted) |

## View Options
- **Table View**: Default tabular display
- **Calendar View**: Monthly/Weekly/Daily calendar view
- **Timeline View**: Gantt-style timeline view

## Calendar View Features
- Toggle between Monthly, Weekly, Daily views
- Color-coded events by type or status
- Filter by member, event type, status, or priority
- Click on event to view details
- Drag-and-drop rescheduling (if permitted)

## Filtering Options
- Filter by member
- Filter by event type
- Filter by status
- Filter by date range
- Filter by priority
- Filter by site

## Event Details Modal
- Full event information
- Attendee list
- Related assignments
- Attachments (if any)
- Notes/comments
- Action buttons (Edit, Cancel, Add Note)

## UI Components
- Tab navigation
- View toggle (Table/Calendar/Timeline)
- Data table with sorting and filtering
- Calendar component
- Search bar
- Filter dropdowns
- Date range picker
- Modal for event details
- Pagination for table view

## API Endpoints (Tentative)

**Authentication**: All endpoints require JWT authentication. Supervisor ID is extracted from the token, no need to pass in payload.

- `GET /api/supervisor/events` - Get all events for supervisor's members
  - Query params: `?status=scheduled&member_id=xxx&event_type=training&start_date=2024-01-01&end_date=2024-12-31&page=1&limit=20`
- `GET /api/supervisor/events/{id}` - Get event details
  - Path param: `id` - Event ID
- `PUT /api/supervisor/events/{id}` - Update event
  - Path param: `id` - Event ID
  - Body: Event update data
- `DELETE /api/supervisor/events/{id}` - Cancel/delete event
  - Path param: `id` - Event ID
- `GET /api/supervisor/events/search` - Search events
  - Query params: `?q=search_term&field=name/description`
- `POST /api/supervisor/events` - Create new event (if permitted)
  - Body: Event creation data
