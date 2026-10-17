# Super Admin - Users View

## Overview
Manage all users in the system with proper hierarchy management. Users can be assigned to supervisors, and supervisors can have their own supervisors, creating a multi-level organizational hierarchy.

## Layout
- Tab navigation at the top (Users, Sites, Action Log)
- Main content area with hierarchical data table
- Tree view or nested table for hierarchy visualization

## Hierarchy Structure

### User Roles
| Role | Description | Can Manage |
|------|-------------|------------|
| Super Admin | Full system access | All users, sites, settings |
| Admin | Organization-level access | Users in their org, sites |
| Supervisor | Manages team members | Assigned members, their assignments |
| Employee | No management rights | Own assignments, requests |

### Hierarchy Levels
```
Super Admin
├── Admin 1
│   ├── Supervisor 1
│   │   ├── Supervisor 1.1
│   │   │   ├── Employee 1
│   │   │   ├── Employee 2
│   │   ├── Employee 3
│   │   └── Employee 4
│   ├── Supervisor 2
│   │   └── Employee 5
│   └── Employee 6
└── Admin 2
    └── Supervisor 3
        └── Employee 7
```

## Table Columns

### User Information
| Column | Description | Data Type |
|--------|-------------|-----------|
| User ID | Unique identifier | String |
| Name | Full name of user | String |
| Email | Email address | String |
| Role | Super Admin/Admin/Supervisor/Employee | Enum |
| Status | Active/Inactive/Suspended/Pending | Enum |
| Department | Department assignment | String |
| Position | Job title | String |
| Employee ID | HR employee identifier | String |
| Hire Date | Date of joining | Date |
| Phone | Contact number | String |
| Location | Base location | String |
| Last Login | Last login timestamp | DateTime |
| Reports To | Direct supervisor (user ID) | String (Foreign Key) |
| Hierarchy Level | Level in hierarchy (1, 2, 3, etc.) | Number |
| Direct Reports Count | Number of users reporting to this user | Number |
| Total Team Size | Total users in subtree | Number |
| Assigned Sites | Sites user can access | Array(String) |
| Skills | List of skills (for employees) | Array(String) |
| Certifications | Professional certifications | Array(String) |

### Actions Column
| Action | Description |
|---------|-------------|
| View Details | Opens modal with full user details |
| Edit | Edit user information |
| Assign Supervisor | Change/assign supervisor |
| Assign Sites | Assign sites to user |
| Add Subordinate | Add user under this user |
| View Hierarchy | View full hierarchy tree for this user |
| Deactivate | Deactivate user account |
| Delete | Delete user (if no dependencies) |

## View Options
- **Table View**: Flat table with hierarchy indicators
- **Tree View**: Expandable tree structure
- **Org Chart View**: Visual organizational chart

## Tree View Features
- Expandable/collapsible nodes
- Indentation based on hierarchy level
- Visual indicators for hierarchy depth
- Filter by role, status, department
- Search by name, email, employee ID
- Show/hide inactive users
- Show/hierarchy depth control

## User Details Modal

### Information Section
- Full user profile
- Contact information
- Employment details
- Assigned sites
- Skills and certifications (for employees)
- Performance metrics (if available)

### Hierarchy Section
- Direct supervisor information
- All direct reports with details
- Full hierarchy tree visualization
- Hierarchy path (breadcrumbs)

### Permissions Section
- Role-based permissions
- Site access permissions
- Data access scope
- Action permissions

### Activity Section
- Recent activity log
- Login history
- Last actions performed
- Assigned tasks/events

### History Section
- Role change history
- Supervisor assignment history
- Site assignment history
- Status change history

## Assign Supervisor Modal

### Form Fields
- **User**: Pre-selected user
- **Current Supervisor**: Display current supervisor
- **New Supervisor**: Dropdown/search for new supervisor
- **Effective Date**: When the change takes effect
- **Reason**: Text area for justification
- **Notify User**: Checkbox to send notification
- **Notify Old Supervisor**: Checkbox to send notification
- **Notify New Supervisor**: Checkbox to send notification

### Validation
- Cannot assign to own subordinate (circular reference)
- Cannot assign to inactive supervisor
- Must maintain valid hierarchy depth
- Supervisor must have compatible role

## Assign Sites Modal

### Form Fields
- **User**: Pre-selected user
- **Available Sites**: Multi-select from all sites
- **Currently Assigned**: Display current assignments
- **Access Level**: Full access/Read only (if applicable)
- **Effective Date**: When assignment takes effect
- **Reason**: Text area for justification

### Validation
- Cannot assign inactive sites
- Supervisor must have access to sites of their subordinates
- Site-specific role requirements

## Add Subordinate Modal

### Form Fields
- **Parent User**: Pre-selected supervisor
- **Subordinate Role**: Dropdown (Supervisor/Employee)
- **Name**: Full name
- **Email**: Email address
- **Employee ID**: HR identifier
- **Department**: Department assignment
- **Position**: Job title
- **Initial Sites**: Site assignments
- **Contact Information**: Phone, etc.
- **Additional Fields**: Based on role

### Validation
- Email uniqueness
- Employee ID uniqueness
- Required fields based on role
- Hierarchy depth limits

## Bulk Actions
- Select multiple users
- Bulk assign supervisor
- Bulk assign sites
- Bulk deactivate
- Bulk change role
- Export selected users
- Import users from CSV

## Filtering Options
- Filter by role
- Filter by status
- Filter by department
- Filter by hierarchy level
- Filter by supervisor
- Filter by site access
- Filter by date range (hire date)

## Search Options
- Search by name
- Search by email
- Search by employee ID
- Search by phone

## Hierarchy Validation Rules
1. **No Circular References**: A user cannot be their own supervisor at any level
2. **Role Compatibility**: Only supervisors can have subordinates
3. **Hierarchy Depth**: Maximum depth limit (configurable, e.g., 5 levels)
4. **Active Supervisor**: Cannot assign to inactive supervisor
5. **Site Access**: Supervisor must have access to all sites of their subordinates
6. **Same Organization**: Users must be in same organization tree

## UI Components
- Tab navigation
- Data table with sorting and filtering
- Tree view component with expand/collapse
- Org chart visualization
- Search bar
- Filter dropdowns
- Modal for user details
- Modal for assign supervisor
- Modal for assign sites
- Modal for add subordinate
- Bulk action menu
- Pagination
- Export/Import buttons
- Hierarchy depth indicator
- Status badges
- Role badges

## Notifications
- New user added notification
- Supervisor change notification
- Site assignment notification
- User deactivation notification
- Role change notification

## API Endpoints (Tentative)

**Authentication**: All endpoints require JWT authentication with Super Admin role. No user ID needed in payload as Super Admin has full access.

- `GET /api/super-admin/users` - Get all users with hierarchy
  - Query params: `?role=supervisor&status=active&department=IT&supervisor_id=xxx&site_id=yyy&hierarchy_level=2&page=1&limit=20`
- `GET /api/super-admin/users/{id}` - Get user details
  - Path param: `id` - User ID
- `GET /api/super-admin/users/{id}/hierarchy` - Get user hierarchy tree (full subtree)
  - Path param: `id` - User ID
  - Query params: `?depth=5&include_inactive=false`
- `GET /api/super-admin/users/{id}/subordinates` - Get direct reports only
  - Path param: `id` - User ID
  - Query params: `?status=active&role=employee`
- `POST /api/super-admin/users` - Create new user
  - Body: User creation data (name, email, role, supervisor_id, sites, etc.)
- `PUT /api/super-admin/users/{id}` - Update user
  - Path param: `id` - User ID
  - Body: User update data
- `DELETE /api/super-admin/users/{id}` - Delete user
  - Path param: `id` - User ID
- `PUT /api/super-admin/users/{id}/supervisor` - Assign/change supervisor
  - Path param: `id` - User ID
  - Body: `{ supervisor_id: "new_supervisor_id", effective_date: "2024-01-15", reason: "..." }`
- `PUT /api/super-admin/users/{id}/sites` - Assign sites to user
  - Path param: `id` - User ID
  - Body: `{ site_ids: ["site1", "site2"], access_level: "full", effective_date: "2024-01-15", reason: "..." }`
- `POST /api/super-admin/users/{id}/subordinate` - Add subordinate under user
  - Path param: `id` - Parent User ID
  - Body: Subordinate creation data
- `PUT /api/super-admin/users/{id}/status` - Change user status
  - Path param: `id` - User ID
  - Body: `{ status: "inactive|suspended", reason: "..." }`
- `GET /api/super-admin/users/search` - Search users
  - Query params: `?q=search_term&field=name/email/employee_id`
- `GET /api/super-admin/users/export` - Export users
  - Query params: `?format=csv|json&role=supervisor&status=active`
- `POST /api/super-admin/users/import` - Import users from CSV
  - Body: FormData with CSV file
