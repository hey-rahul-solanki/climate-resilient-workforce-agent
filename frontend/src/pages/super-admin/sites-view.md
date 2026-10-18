# Super Admin - Sites View

## Overview
Manage all sites in the system. Sites are master data used to assign to members/supervisors for work assignments and weather monitoring.

## Layout
- Tab navigation at the top (Users, Sites, Action Log)
- Main content area with a data table
- Map view option for site visualization

## Table Columns

### Site Information
| Column | Description | Data Type |
|--------|-------------|-----------|
| Site ID | Unique identifier | String |
| Site Name | Name of the site | String |
| Site Code | Short code/abbreviation | String |
| Address | Full street address | String |
| City | City name | String |
| State/Province | State or province | String |
| Country | Country name | String |
| Zip/Postal Code | Postal code | String |
| Coordinates | Latitude, Longitude | Object {lat, lng} |
| Timezone | Site timezone | String |
| Status | Active/Inactive/Under Construction/Decommissioned | Enum |
| Site Type | Office/Field/Warehouse/Construction/Other | Enum |
| Area Size | Area in square meters | Number |
| Capacity | Maximum personnel capacity | Number |
| Current Occupancy | Current number of personnel | Number |
| Region | Administrative region | String |
| Zone | Zone classification | String |
| Manager | Site manager name | String |
| Manager ID | Site manager user ID | String |
| Contact Phone | Site contact number | String |
| Contact Email | Site contact email | String |
| Emergency Contact | Emergency contact information | String |
| Operating Hours | Operating hours (e.g., 8AM-6PM) | String |
| Working Days | Days of operation (e.g., Mon-Fri) | Array(String) |
| Safety Rating | Safety rating score | Number (1-5) |
| Last Inspection | Last safety inspection date | Date |
| Next Inspection | Next scheduled inspection date | Date |
| Assigned Users | Number of users assigned to site | Number |
| Active Assignments | Number of active assignments | Number |
| Created Date | When site was created | DateTime |
| Updated Date | Last update timestamp | DateTime |

### Weather Info Column
| Column | Description | Data Type |
|--------|-------------|-----------|
| Current Weather | Current weather condition | String |
| Temperature | Current temperature | Number (°C/°F) |
| Weather Alert | Active weather alerts | String/Array |
| Last Weather Update | Last weather data update | DateTime |

### Actions Column
| Action | Description |
|---------|-------------|
| View Details | Opens modal with full site details |
| Edit | Edit site information |
| View Map | Opens map showing site location |
| View Assigned Users | View all users assigned to this site |
| View Assignments | View all assignments at this site |
| View Weather | View detailed weather information |
| Deactivate | Deactivate site |
| Delete | Delete site (if no dependencies) |

## View Options
- **Table View**: Default tabular display
- **Map View**: Visual map with site markers
- **Grid View**: Card-based view with site details

## Map View Features
- Interactive map with site markers
- Color-coded markers by status
- Cluster markers for dense areas
- Filter by status, site type, region
- Click marker to view site details
- Search by site name or location
- Show/hide inactive sites
- Weather overlay option

## Site Details Modal

### Information Section
- Full site profile
- Location details with map
- Contact information
- Operating schedule
- Capacity and occupancy
- Safety information
- Inspection history

### Location Section
- Address with map
- Coordinates
- Timezone
- Nearby landmarks
- Access routes
- Parking information

### Weather Section
- Current weather conditions
- Weather forecast
- Historical weather data
- Weather alerts
- Climate information

### Assignments Section
- List of all assignments at this site
- Currently assigned users
- Upcoming events
- Active tasks
- Assignment history

### Personnel Section
- Assigned supervisors
- Assigned employees
- Current occupancy
- Capacity utilization
- Personnel schedule

### Safety Section
- Safety rating
- Last inspection details
- Safety guidelines
- Emergency procedures
- PPE requirements
- Hazard information

### History Section
- Creation history
- Status change history
- Assignment history
- Inspection history
- Manager change history

## Edit Site Modal

### Form Fields
- **Site Name**: Text input
- **Site Code**: Text input (unique)
- **Address**: Text input
- **City**: Text input
- **State/Province**: Text input
- **Country**: Dropdown
- **Zip/Postal Code**: Text input
- **Coordinates**: Lat/Lng picker or auto-fill from address
- **Timezone**: Dropdown
- **Status**: Dropdown (Active/Inactive/Under Construction/Decommissioned)
- **Site Type**: Dropdown (Office/Field/Warehouse/Construction/Other)
- **Area Size**: Number input
- **Capacity**: Number input
- **Region**: Text input
- **Zone**: Text input
- **Manager**: User search/dropdown
- **Contact Phone**: Text input
- **Contact Email**: Email input
- **Emergency Contact**: Text input
- **Operating Hours**: Text input
- **Working Days**: Multi-select (Mon-Sun)
- **Safety Rating**: Number input (1-5)
- **Next Inspection**: Date picker

### Validation
- Site code uniqueness
- Required fields
- Valid coordinates
- Valid email
- Valid phone number
- Manager must be active user

## View Assigned Users Modal
- List of all users assigned to this site
- Filter by role
- Filter by status
- User information with hierarchy
- Assignment dates
- Bulk unassign option

## View Assignments Modal
- List of all assignments at this site
- Filter by status
- Filter by date range
- Assignment details
- Assigned users
- Timeline view option

## Filtering Options
- Filter by status
- Filter by site type
- Filter by region
- Filter by zone
- Filter by manager
- Filter by weather alert status
- Filter by capacity utilization
- Filter by date range

## Search Options
- Search by site name
- Search by site code
- Search by address
- Search by city
- Search by manager name

## Bulk Actions
- Select multiple sites
- Bulk deactivate
- Bulk change manager
- Bulk update status
- Export selected sites
- Import sites from CSV

## Site Status Workflow
- **Active** → **Under Construction** (maintenance)
- **Under Construction** → **Active** (completion)
- **Active** → **Inactive** (temporary closure)
- **Inactive** → **Active** (reopening)
- **Active/Inactive** → **Decommissioned** (permanent closure)

## UI Components
- Tab navigation
- Data table with sorting and filtering
- Map component with markers
- Grid view cards
- Search bar
- Filter dropdowns
- Modal for site details
- Modal for edit site
- Modal for assigned users
- Modal for assignments
- Bulk action menu
- Pagination
- Export/Import buttons
- Status badges
- Site type badges
- Weather alert badges
- Coordinate picker
- Map integration

## Notifications
- New site created notification
- Site status change notification
- Manager change notification
- Inspection due reminder
- Weather alert for site

## API Endpoints (Tentative)

**Authentication**: All endpoints require JWT authentication with Super Admin role. No user ID needed in payload as Super Admin has full access.

- `GET /api/super-admin/sites` - Get all sites
  - Query params: `?status=active&site_type=field&region=North&manager_id=xxx&weather_alert=warning&page=1&limit=20`
- `GET /api/super-admin/sites/{id}` - Get site details
  - Path param: `id` - Site ID
- `GET /api/super-admin/sites/{id}/users` - Get users assigned to site
  - Path param: `id` - Site ID
  - Query params: `?role=supervisor&status=active`
- `GET /api/super-admin/sites/{id}/assignments` - Get assignments at site
  - Path param: `id` - Site ID
  - Query params: `?status=in_progress&start_date=2024-01-01&end_date=2024-12-31`
- `GET /api/super-admin/sites/{id}/weather` - Get site weather
  - Path param: `id` - Site ID
  - Query params: `?unit=celsius|fahrenheit`
- `POST /api/super-admin/sites` - Create new site
  - Body: Site creation data (name, address, coordinates, manager, etc.)
- `PUT /api/super-admin/sites/{id}` - Update site
  - Path param: `id` - Site ID
  - Body: Site update data
- `DELETE /api/super-admin/sites/{id}` - Delete site
  - Path param: `id` - Site ID
- `PUT /api/super-admin/sites/{id}/status` - Change site status
  - Path param: `id` - Site ID
  - Body: `{ status: "inactive|under_construction|decommissioned", reason: "..." }`
- `PUT /api/super-admin/sites/{id}/manager` - Change site manager
  - Path param: `id` - Site ID
  - Body: `{ manager_id: "new_manager_id", reason: "..." }`
- `GET /api/super-admin/sites/search` - Search sites
  - Query params: `?q=search_term&field=name/code/address/city`
- `GET /api/super-admin/sites/export` - Export sites
  - Query params: `?format=csv|json&status=active&site_type=field`
- `POST /api/super-admin/sites/import` - Import sites from CSV
  - Body: FormData with CSV file
- `GET /api/super-admin/sites/map-data` - Get sites for map view
  - Query params: `?status=active&weather_overlay=true`
