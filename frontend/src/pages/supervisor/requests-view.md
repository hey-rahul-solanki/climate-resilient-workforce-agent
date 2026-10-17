# Supervisor - Requests View

## Overview
Display all requests submitted by members working under the supervisor in a tabular format.

## Layout
- Tab navigation at the top (Members, Events, Weather, Requests)
- Main content area with a data table
- Filter and search options

## Table Columns

### Request Information
| Column | Description | Data Type |
|--------|-------------|-----------|
| Request ID | Unique identifier | String |
| Member Name | Name of member who submitted | String |
| Member ID | Employee ID of member | String |
| Request Type | Leave/Shift Change/Resource/Equipment/Training/Other | Enum |
| Request Title | Short title of request | String |
| Description | Detailed description | String |
| Priority | Urgent/High/Medium/Low | Enum |
| Status | Pending/Approved/Rejected/In Progress/Completed | Enum |
| Submitted Date | Date request was submitted | DateTime |
| Due Date | Expected resolution date | Date |
| Assigned To | Who is handling the request | String |
| Site | Associated site | String |
| Category | HR/Operations/Safety/Equipment | Enum |
| Attachments | Number of attachments | Number |
| Comments | Number of comments | Number |

### Actions Column
| Action | Description |
|---------|-------------|
| View Details | Opens modal with full request details |
| Approve | Approve request (if permitted) |
| Reject | Reject request (if permitted) |
| Assign | Assign to someone for resolution |
| Add Comment | Add comment to request |

## Filtering Options
- Filter by member
- Filter by request type
- Filter by status
- Filter by priority
- Filter by category
- Filter by date range
- Filter by site

## Request Details Modal

### Information Section
- Full request details
- Member information
- Submission timestamp
- All attachments with download links
- Related assignments or events (if any)

### Action Section
- Approve/Reject buttons (with reason field)
- Assign to dropdown
- Add comment input
- Update status dropdown
- Escalate option (for urgent requests)

### Comments Section
- Thread of comments
- Timestamped responses
- Member and supervisor comments distinguished
- Add new comment

### History Section
- Timeline of status changes
- Who made changes and when
- Approval/rejection reasons

## Bulk Actions
- Select multiple requests
- Bulk approve (same type)
- Bulk reject (same type)
- Bulk assign
- Export selected requests

## Status Workflow
1. **Pending** → **In Progress** (when assigned)
2. **In Progress** → **Completed** (when resolved)
3. **Pending** → **Approved** (for approval requests)
4. **Pending** → **Rejected** (for rejection)
5. Any status → **Escalated** (if escalated)

## Priority Indicators
- Color-coded badges:
  - Red: Urgent
  - Orange: High
  - Yellow: Medium
  - Green: Low

## UI Components
- Tab navigation
- Data table with sorting and filtering
- Search bar
- Filter dropdowns
- Date range picker
- Modal for request details
- Comment thread component
- Status badge
- Priority badge
- Bulk action menu
- Pagination
- Export button

## Notifications
- New request notification
- Request status change notification
- Comment on request notification
- Due date approaching notification

## API Endpoints (Tentative)

**Authentication**: All endpoints require JWT authentication. Supervisor ID is extracted from the token, no need to pass in payload.

- `GET /api/supervisor/requests` - Get all requests from members under supervisor
  - Query params: `?status=pending&priority=high&member_id=xxx&request_type=leave&start_date=2024-01-01&end_date=2024-12-31&page=1&limit=20`
- `GET /api/supervisor/requests/{id}` - Get request details
  - Path param: `id` - Request ID
- `PUT /api/supervisor/requests/{id}/status` - Update request status
  - Path param: `id` - Request ID
  - Body: `{ status: "in_progress|completed", assigned_to: "user_id" }`
- `POST /api/supervisor/requests/{id}/approve` - Approve request
  - Path param: `id` - Request ID
  - Body: `{ reason: "Approval reason" }`
- `POST /api/supervisor/requests/{id}/reject` - Reject request
  - Path param: `id` - Request ID
  - Body: `{ reason: "Rejection reason" }`
- `POST /api/supervisor/requests/{id}/comment` - Add comment to request
  - Path param: `id` - Request ID
  - Body: `{ comment: "Comment text" }`
- `POST /api/supervisor/requests/{id}/assign` - Assign request to someone
  - Path param: `id` - Request ID
  - Body: `{ assigned_to: "user_id" }`
- `GET /api/supervisor/requests/search` - Search requests
  - Query params: `?q=search_term&field=title/description`
- `GET /api/supervisor/requests/export` - Export requests
  - Query params: `?format=csv|json&status=pending&start_date=2024-01-01&end_date=2024-12-31`
