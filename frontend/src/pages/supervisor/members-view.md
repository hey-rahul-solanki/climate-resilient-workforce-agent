# Supervisor - Members View

## Overview
Display all workers/members working under the supervisor in a tabular format.

## Layout
- Tab navigation at the top (Members, Events, Weather, Requests)
- Main content area with a data table

## Table Columns

### Core Member Information
| Column | Description | Data Type |
|--------|-------------|-----------|
| Name | Full name of the member | String |
| Employee ID | Unique identifier | String |
| Position | Job title/role | String |
| Department | Department assignment | String |
| Hire Date | Date of joining | Date |
| Status | Active/Inactive/On Leave | Enum |
| Contact Number | Phone number | String |
| Email | Email address | String |
| Assigned Site | Current site location | String |
| Shift | Morning/Evening/Night | Enum |
| Skills | List of relevant skills | Array(String) |
| Certification | Professional certifications | Array(String) |
| Last Activity | Timestamp of last activity | DateTime |

### Actions Column
| Action | Description |
|---------|-------------|
| View Assignments | Opens modal with member's assignments |

## Assignments Modal

### Toggle Views
- **Table View**: Display assignments in tabular format
- **Calendar View**: Display assignments on a calendar

### Assignment Table Columns
| Column | Description | Data Type |
|--------|-------------|-----------|
| Assignment ID | Unique identifier | String |
| Project/Task | Name of project or task | String |
| Site | Location of assignment | String |
| Start Date | Assignment start date | Date |
| End Date | Assignment end date | Date |
| Status | In Progress/Completed/Pending | Enum |
| Priority | High/Medium/Low | Enum |
| Hours Allocated | Total hours assigned | Number |
| Hours Completed | Hours worked so far | Number |
| Notes | Additional information | String |

### Calendar View Features
- Monthly/Weekly/Daily view toggle
- Color-coded assignments by status or priority
- Click on assignment to view details
- Filter by status, priority, or project

## UI Components
- Tab navigation
- Data table with sorting and filtering
- Search bar for members
- Modal for assignments
- Toggle switch for table/calendar view
- Pagination for large datasets

## API Endpoints (Tentative)

**Authentication**: All endpoints require JWT authentication. Supervisor ID is extracted from the token, no need to pass in payload.

- `GET /api/supervisor/members` - Get all members under the authenticated supervisor
  - Query params: `?status=active&site=site_id&search=query&page=1&limit=20`
- `GET /api/supervisor/members/{id}/assignments` - Get assignments for a specific member
  - Path param: `id` - Member ID
  - Query params: `?status=in_progress&start_date=2024-01-01&end_date=2024-12-31`
- `GET /api/supervisor/members/search` - Search members under supervisor
  - Query params: `?q=search_term&field=name/email/employee_id`
