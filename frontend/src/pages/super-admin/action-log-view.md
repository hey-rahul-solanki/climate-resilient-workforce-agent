# Super Admin - Action Log View

## Overview
Display comprehensive action logs for all users in the system including supervisor logs, member logs, system events, and administrative actions. This provides full audit trail and activity monitoring.

## Layout
- Tab navigation at the top (Users, Sites, Action Log)
- Filter panel at the top
- Main content area with a data table
- Log details modal

## Table Columns

### Log Information
| Column | Description | Data Type |
|--------|-------------|-----------|
| Log ID | Unique identifier | String |
| Timestamp | When the action occurred | DateTime |
| User | Name of user who performed action | String |
| User ID | User ID of actor | String |
| User Role | Role of the user (Super Admin/Admin/Supervisor/Employee) | Enum |
| Action Type | Created/Updated/Deleted/Viewed/Approved/Rejected/Assigned/etc. | Enum |
| Action Category | User/Site/Assignment/Event/Request/Weather/System/Security | Enum |
| Entity Type | What was affected (User/Site/Assignment/Event/Request/etc.) | String |
| Entity ID | ID of affected entity | String |
| Entity Name | Name of affected entity | String |
| Description | Human-readable description of action | String |
| Details | Additional details (JSON or structured data) | Object/JSON |
| IP Address | IP address of user | String |
| User Agent | Browser/device information | String |
| Status | Success/Failure/Warning | Enum |
| Error Message | Error details if action failed | String |
| Impact Level | Low/Medium/High/Critical | Enum |
| Related Logs | IDs of related log entries | Array(String) |
| Session ID | Session identifier | String |

### Actions Column
| Action | Description |
|---------|-------------|
| View Details | Opens modal with full log details |
| View Related Logs | View logs related to this action |
| Export Log | Export this log entry |
| Investigate | Flag for investigation (if suspicious) |

## Action Categories

### User Actions
- User creation
- User updates
- User deletion
- Supervisor assignment
- Role changes
- Status changes
- Login/Logout
- Password changes

### Site Actions
- Site creation
- Site updates
- Site deletion
- Site status changes
- Manager changes
- Site assignments

### Assignment Actions
- Assignment creation
- Assignment updates
- Assignment deletion
- Assignment status changes
- Member assignment to site
- Schedule changes

### Event Actions
- Event creation
- Event updates
- Event cancellation
- Event attendance
- Event notifications

### Request Actions
- Request submission
- Request approval
- Request rejection
- Request assignment
- Request comments
- Request status changes

### Weather Actions
- Weather alerts sent
- Weather-based schedule changes
- Weather concern shared
- Weather notifications

### System Actions
- Configuration changes
- System updates
- Backup operations
- Data exports
- Data imports

### Security Actions
- Failed login attempts
- Permission changes
- Access denied events
- Suspicious activity
- Data access

## Filtering Options

### Time Filters
- Date range picker
- Quick selects (Today, Yesterday, Last 7 days, Last 30 days, Custom)
- Time range (Hour of day)

### User Filters
- Filter by user
- Filter by user role
- Filter by department
- Filter by supervisor

### Action Filters
- Filter by action type
- Filter by action category
- Filter by entity type
- Filter by status (Success/Failure/Warning)
- Filter by impact level

### Advanced Filters
- Filter by IP address
- Filter by error message
- Filter by impact level
- Filter by related entity
- Filter by session ID

## Search Options
- Search by user name
- Search by action description
- Search by entity name
- Search by error message
- Search by IP address

## Log Details Modal

### Information Section
- Full log entry details
- Timestamp with timezone
- User information with profile link
- Action type and category
- Entity information with link
- Status and impact level

### Details Section
- Full action description
- Before/after values (for updates)
- Changed fields
- Additional metadata
- Related entities

### Technical Section
- IP address
- User agent
- Session ID
- Request details (if applicable)
- Response details (if applicable)

### Context Section
- Related logs
- User's recent actions
- Entity's recent changes
- Timeline view

### Investigation Section
- Flag for investigation
- Add investigation notes
- Assign to investigator
- Set investigation priority
- Mark as resolved

## Related Logs View
- Shows all logs related to the selected action
- Grouped by entity or session
- Timeline visualization
- Chain of events
- Cause and effect analysis

## Impact Levels
| Level | Description | Examples |
|-------|-------------|----------|
| Low | Routine operations | Viewing data, minor updates |
| Medium | Moderate changes | Creating users, updating assignments |
| High | Significant changes | Deleting users, site status changes |
| Critical | Security or system-critical | Failed logins, permission changes, data deletion |

## Status Indicators
- **Success**: Green indicator
- **Failure**: Red indicator
- **Warning**: Yellow indicator

## Bulk Actions
- Select multiple logs
- Bulk export
- Bulk flag for investigation
- Bulk mark as resolved
- Bulk delete (admin only)

## Export Options
- Export to CSV
- Export to JSON
- Export to PDF
- Custom date range
- Filter applied export

## Analytics/Statistics
- Total actions count
- Actions by category (chart)
- Actions by user role (chart)
- Actions over time (timeline)
- Success/failure rate
- Most active users
- Most affected entities
- Failed actions by type

## Retention Policy
- Configurable retention period (e.g., 90 days, 1 year)
- Archive old logs
- Purge very old logs
- Compliance requirements

## Security Features
- Read-only access for most users
- Admin can edit investigation notes
- Cannot delete logs (except by super admin with confirmation)
- Audit trail for log deletions
- Encryption for sensitive data

## UI Components
- Tab navigation
- Data table with sorting and filtering
- Advanced filter panel
- Search bar
- Date range picker
- Modal for log details
- Modal for related logs
- Bulk action menu
- Pagination
- Export buttons
- Analytics dashboard
- Status badges
- Impact level badges
- Action category badges
- Timeline view
- Charts for statistics

## Real-time Updates
- Auto-refresh for new logs
- Live feed option
- WebSocket updates for critical events
- Notification for high-impact actions
- Alert for security events

## Notifications
- High-impact action notification
- Security event alert
- Failed action alert
- Investigation assignment notification

## API Endpoints (Tentative)

**Authentication**: All endpoints require JWT authentication with Super Admin role. No user ID needed in payload as Super Admin has full access.

- `GET /api/super-admin/action-logs` - Get all action logs
  - Query params: `?start_date=2024-01-01&end_date=2024-12-31&user_id=xxx&user_role=supervisor&action_category=user&status=success&impact_level=high&page=1&limit=20`
- `GET /api/super-admin/action-logs/{id}` - Get log details
  - Path param: `id` - Log ID
- `GET /api/super-admin/action-logs/{id}/related` - Get related logs
  - Path param: `id` - Log ID
  - Query params: `?group_by=session|entity`
- `GET /api/super-admin/action-logs/search` - Search logs
  - Query params: `?q=search_term&field=description/entity_name/error_message`
- `GET /api/super-admin/action-logs/export` - Export logs
  - Query params: `?format=csv|json|pdf&start_date=2024-01-01&end_date=2024-12-31&user_role=supervisor&action_category=user`
- `GET /api/super-admin/action-logs/statistics` - Get log statistics
  - Query params: `?start_date=2024-01-01&end_date=2024-12-31&group_by=category|role|user`
- `PUT /api/super-admin/action-logs/{id}/investigate` - Flag for investigation
  - Path param: `id` - Log ID
  - Body: `{ investigation_notes: "Notes", assigned_to: "investigator_id", priority: "high" }`
- `PUT /api/super-admin/action-logs/{id}/resolve` - Mark investigation as resolved
  - Path param: `id` - Log ID
  - Body: `{ resolution_notes: "Resolution details" }`
- `DELETE /api/super-admin/action-logs/{id}` - Delete log (super admin only with confirmation)
  - Path param: `id` - Log ID
- `GET /api/super-admin/action-logs/live-feed` - Real-time log feed (WebSocket or SSE)
  - Query params: `?filter_impact=high|critical`
