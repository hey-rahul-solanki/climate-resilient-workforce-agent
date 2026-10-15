# API Documentation

## Overview

This document provides comprehensive API specifications for the Climate-Resilient Workforce Agent platform. All APIs follow RESTful conventions and require JWT authentication.

## Base URL
```
http://localhost:8000/api
```

## Authentication

All endpoints require JWT authentication in the `Authorization` header:
```
Authorization: Bearer <jwt_token>
```

The JWT token contains:
- `user_id`: UUID of the authenticated user
- `role`: User role (super_admin, admin, supervisor, employee)
- `exp`: Token expiration timestamp

## Response Format

All API responses follow this structure:

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful"
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error description",
    "details": { ... }
  }
}
```

### Pagination Response
```json
{
  "success": true,
  "data": { ... },
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

---

## Table of Contents

1. [Authentication APIs](#authentication-apis)
2. [Supervisor APIs](#supervisor-apis)
3. [Employee APIs](#employee-apis)
4. [Super Admin APIs](#super-admin-apis)
5. [Weather APIs](#weather-apis)
6. [Common APIs](#common-apis)

---

## Authentication APIs

### POST /api/auth/login
Login user and return JWT token.

**Request Body:**
```json
{
  "username": "johndoe",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "uuid",
      "username": "johndoe",
      "full_name": "John Doe",
      "email": "john@example.com",
      "role": "supervisor",
      "department": "Operations"
    }
  }
}
```

### POST /api/auth/logout
Logout user (invalidate token on server if using token blacklist).

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

### POST /api/auth/refresh
Refresh JWT token.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

---

## Supervisor APIs

### Members

#### GET /api/supervisor/members
Get all members under the authenticated supervisor.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `status` (optional): Filter by status (active, inactive, on_leave)
- `site` (optional): Filter by site ID
- `search` (optional): Search by name, email, or employee_id
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "full_name": "John Doe",
      "employee_id": "EMP001",
      "email": "john@example.com",
      "position": "Technician",
      "department": "Operations",
      "phone_number": "+1234567890",
      "assigned_site": "Site A",
      "shift": "morning",
      "status": "active",
      "skills": ["welding", "electrical"],
      "certifications": [{"name": "Safety Certificate", "expiry": "2024-12-31"}],
      "last_activity": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 50,
    "total_pages": 3
  }
}
```

#### GET /api/supervisor/members/{id}/assignments
Get assignments for a specific member.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Member UUID

**Query Parameters:**
- `status` (optional): Filter by status (scheduled, in_progress, completed)
- `start_date` (optional): Filter by start date (ISO 8601)
- `end_date` (optional): Filter by end date (ISO 8601)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "project": "Site Maintenance",
      "site": "Site A",
      "start_date": "2024-01-15",
      "end_date": "2024-01-20",
      "status": "in_progress",
      "priority": "high",
      "hours_allocated": 40,
      "hours_completed": 20,
      "shift": "morning"
    }
  ]
}
```

#### GET /api/supervisor/members/search
Search members under supervisor.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `q`: Search query
- `field`: Search field (name, email, employee_id)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "full_name": "John Doe",
      "employee_id": "EMP001",
      "email": "john@example.com"
    }
  ]
}
```

### Events

#### GET /api/supervisor/events
Get all events for supervisor's members.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `status` (optional): Filter by status (scheduled, in_progress, completed, cancelled)
- `member_id` (optional): Filter by member UUID
- `event_type` (optional): Filter by type (training, meeting, inspection, emergency_drill)
- `start_date` (optional): Filter by start date (ISO 8601)
- `end_date` (optional): Filter by end date (ISO 8601)
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "event_name": "Safety Training",
      "event_type": "training",
      "start_time": "2024-01-15T09:00:00Z",
      "end_time": "2024-01-15T17:00:00Z",
      "location": "Conference Room A",
      "site": "Site A",
      "status": "scheduled",
      "priority": "high",
      "member": "John Doe",
      "member_id": "uuid",
      "attendance": {
        "expected": 10,
        "actual": 8
      },
      "created_by": "Jane Smith",
      "created_date": "2024-01-10T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 30,
    "total_pages": 2
  }
}
```

#### GET /api/supervisor/events/{id}
Get event details.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Event UUID

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "event_name": "Safety Training",
    "event_type": "training",
    "start_time": "2024-01-15T09:00:00Z",
    "end_time": "2024-01-15T17:00:00Z",
    "location": "Conference Room A",
    "site": "Site A",
    "status": "scheduled",
    "priority": "high",
    "description": "Full safety training session",
    "attendee_ids": ["uuid1", "uuid2"],
    "attendees": [
      {"id": "uuid1", "name": "John Doe"},
      {"id": "uuid2", "name": "Jane Smith"}
    ],
    "created_by": "uuid",
    "created_date": "2024-01-10T10:00:00Z"
  }
}
```

#### POST /api/supervisor/events
Create new event.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
  "event_name": "Safety Training",
  "event_type": "training",
  "start_time": "2024-01-15T09:00:00Z",
  "end_time": "2024-01-15T17:00:00Z",
  "location": "Conference Room A",
  "site_id": "uuid",
  "priority": "high",
  "description": "Full safety training session",
  "attendee_ids": ["uuid1", "uuid2"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "event_name": "Safety Training",
    "event_type": "training",
    "start_time": "2024-01-15T09:00:00Z",
    "end_time": "2024-01-15T17:00:00Z",
    "status": "scheduled"
  }
}
```

#### PUT /api/supervisor/events/{id}
Update event.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Event UUID

**Request Body:**
```json
{
  "event_name": "Updated Safety Training",
  "start_time": "2024-01-16T09:00:00Z",
  "end_time": "2024-01-16T17:00:00Z",
  "priority": "medium"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "event_name": "Updated Safety Training",
    "start_time": "2024-01-16T09:00:00Z",
    "end_time": "2024-01-16T17:00:00Z"
  }
}
```

#### DELETE /api/supervisor/events/{id}
Cancel/delete event.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Event UUID

**Response:**
```json
{
  "success": true,
  "message": "Event cancelled successfully"
}
```

#### GET /api/supervisor/events/search
Search events.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `q`: Search query
- `field`: Search field (name, description)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "event_name": "Safety Training",
      "event_type": "training",
      "start_time": "2024-01-15T09:00:00Z"
    }
  ]
}
```

### Weather

#### GET /api/supervisor/weather/sites
Get weather for sites assigned to supervisor's members.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `alert_level` (optional): Filter by alert level (normal, caution, warning, severe)
- `sort` (optional): Sort by field (temperature, humidity)
- `unit` (optional): Temperature unit (celsius, fahrenheit, default: celsius)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "site_name": "Site A",
      "location": "Vadodara, Gujarat, India",
      "coordinates": {
        "lat": 22.3072,
        "lng": 73.1812
      },
      "current_temp": 28,
      "feels_like": 30,
      "weather_condition": "Partly Cloudy",
      "humidity": 65,
      "wind_speed": 12,
      "wind_direction": "NE",
      "visibility": 8,
      "uv_index": 6,
      "air_quality": "Moderate",
      "precipitation": 0,
      "forecast": "Light rain expected in evening",
      "last_updated": "2024-01-15T10:00:00Z",
      "alert": null
    }
  ]
}
```

#### GET /api/supervisor/weather/location
Get weather for specific location.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `lat` (optional): Latitude
- `lng` (optional): Longitude
- `city` (optional): City name
- `zip` (optional): Zip/postal code
- `unit` (optional): Temperature unit (celsius, fahrenheit)

**Response:**
```json
{
  "success": true,
  "data": {
    "location": "Vadodara, Gujarat, India",
    "coordinates": {
      "lat": 22.3072,
      "lng": 73.1812
    },
    "current_temp": 28,
    "feels_like": 30,
    "weather_condition": "Partly Cloudy",
    "humidity": 65,
    "wind_speed": 12,
    "forecast": "Light rain expected in evening",
    "hourly_forecast": [...],
    "daily_forecast": [...]
  }
}
```

#### GET /api/supervisor/weather/search
Search locations for weather.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `q`: Search query (city name, zip code)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "location": "Vadodara, Gujarat, India",
      "coordinates": {
        "lat": 22.3072,
        "lng": 73.1812
      },
      "current_temp": 28,
      "weather_condition": "Partly Cloudy"
    }
  ]
}
```

#### POST /api/supervisor/weather/alert
Send weather alert to members at location.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
  "location": "Site A",
  "alert_type": "warning",
  "message": "Heavy rain expected, take necessary precautions",
  "urgency": "high"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Weather alert sent to 10 members"
}
```

#### POST /api/supervisor/weather/action
Take quick action based on weather.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
  "action_type": "schedule_adjustment",
  "location": "Site A",
  "details": "Reschedule outdoor work to tomorrow"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Action completed successfully"
}
```

### Requests

#### GET /api/supervisor/requests
Get all requests from members under supervisor.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `status` (optional): Filter by status (pending, in_progress, approved, rejected, completed)
- `priority` (optional): Filter by priority (urgent, high, medium, low)
- `member_id` (optional): Filter by member UUID
- `request_type` (optional): Filter by type (leave, shift_change, resource, equipment, training)
- `start_date` (optional): Filter by submitted date (ISO 8601)
- `end_date` (optional): Filter by submitted date (ISO 8601)
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "member_name": "John Doe",
      "member_id": "uuid",
      "request_type": "leave",
      "request_title": "Sick Leave",
      "description": "Need sick leave for 2 days",
      "priority": "high",
      "status": "pending",
      "submitted_date": "2024-01-15T10:00:00Z",
      "due_date": "2024-01-17",
      "assigned_to": "Jane Smith",
      "site": "Site A",
      "category": "hr",
      "attachments_count": 1,
      "comments_count": 2
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 25,
    "total_pages": 2
  }
}
```

#### GET /api/supervisor/requests/{id}
Get request details.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Request UUID

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "member_name": "John Doe",
    "member_id": "uuid",
    "request_type": "leave",
    "request_title": "Sick Leave",
    "description": "Need sick leave for 2 days",
    "priority": "high",
    "status": "pending",
    "submitted_date": "2024-01-15T10:00:00Z",
    "due_date": "2024-01-17",
    "assigned_to": "uuid",
    "site": "Site A",
    "category": "hr",
    "attachments": [
      {
        "name": "medical_certificate.pdf",
        "url": "https://s3..."
      }
    ],
    "comments": [
      {
        "id": "uuid",
        "user_id": "uuid",
        "user_name": "Jane Smith",
        "comment": "Please provide medical certificate",
        "created_at": "2024-01-15T11:00:00Z"
      }
    ],
    "history": [
      {
        "status": "pending",
        "changed_by": "John Doe",
        "changed_at": "2024-01-15T10:00:00Z",
        "reason": "Request submitted"
      }
    ]
  }
}
```

#### PUT /api/supervisor/requests/{id}/status
Update request status.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Request UUID

**Request Body:**
```json
{
  "status": "in_progress",
  "assigned_to": "uuid"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "status": "in_progress",
    "assigned_to": "uuid"
  }
}
```

#### POST /api/supervisor/requests/{id}/approve
Approve request.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Request UUID

**Request Body:**
```json
{
  "reason": "Leave approved as per company policy"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "status": "approved",
    "approved_by": "uuid",
    "approved_at": "2024-01-15T12:00:00Z"
  }
}
```

#### POST /api/supervisor/requests/{id}/reject
Reject request.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Request UUID

**Request Body:**
```json
{
  "reason": "Insufficient notice period"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "status": "rejected",
    "rejected_by": "uuid",
    "rejected_at": "2024-01-15T12:00:00Z"
  }
}
```

#### POST /api/supervisor/requests/{id}/comment
Add comment to request.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Request UUID

**Request Body:**
```json
{
  "comment": "Please provide additional documentation"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "comment": "Please provide additional documentation",
    "user_id": "uuid",
    "created_at": "2024-01-15T12:00:00Z"
  }
}
```

#### POST /api/supervisor/requests/{id}/assign
Assign request to someone.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Request UUID

**Request Body:**
```json
{
  "assigned_to": "uuid"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "assigned_to": "uuid",
    "assigned_at": "2024-01-15T12:00:00Z"
  }
}
```

#### GET /api/supervisor/requests/search
Search requests.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `q`: Search query
- `field`: Search field (title, description)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "request_title": "Sick Leave",
      "request_type": "leave",
      "status": "pending"
    }
  ]
}
```

#### GET /api/supervisor/requests/export
Export requests.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `format`: Export format (csv, json)
- `status`: Filter by status
- `start_date`: Filter by start date (ISO 8601)
- `end_date`: Filter by end date (ISO 8601)

**Response:**
```json
{
  "success": true,
  "data": {
    "download_url": "https://s3.../requests_export.csv",
    "expires_at": "2024-01-16T12:00:00Z"
  }
}
```

---

## Employee APIs

### Assignments

#### GET /api/employee/assignments
Get all assignments for the authenticated employee.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `status` (optional): Filter by status (scheduled, in_progress, completed, cancelled)
- `site` (optional): Filter by site ID
- `priority` (optional): Filter by priority (high, medium, low)
- `start_date` (optional): Filter by start date (ISO 8601)
- `end_date` (optional): Filter by end date (ISO 8601)
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "project": "Site Maintenance",
      "site": "Site A",
      "start_date": "2024-01-15",
      "end_date": "2024-01-20",
      "shift": "morning",
      "status": "in_progress",
      "priority": "high",
      "hours_allocated": 40,
      "hours_completed": 20,
      "supervisor": "Jane Smith",
      "team_members": ["John Doe", "Bob Smith"],
      "description": "Maintenance task",
      "notes": "Bring safety equipment",
      "weather": {
        "condition": "Partly Cloudy",
        "temperature": 28,
        "advisory": "Normal working conditions",
        "forecast": "Light rain expected",
        "alert_level": "normal"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 15,
    "total_pages": 1
  }
}
```

#### GET /api/employee/assignments/{id}
Get assignment details.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Assignment UUID

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "project": "Site Maintenance",
    "site": "Site A",
    "start_date": "2024-01-15",
    "end_date": "2024-01-20",
    "shift": "morning",
    "status": "in_progress",
    "priority": "high",
    "hours_allocated": 40,
    "hours_completed": 20,
    "supervisor": "Jane Smith",
    "team_members": [
      {"id": "uuid", "name": "John Doe"},
      {"id": "uuid", "name": "Bob Smith"}
    ],
    "description": "Maintenance task",
    "notes": "Bring safety equipment",
    "site_location": {
      "address": "123 Main St",
      "coordinates": {"lat": 22.3072, "lng": 73.1812}
    },
    "weather": {
      "condition": "Partly Cloudy",
      "temperature": 28,
      "advisory": "Normal working conditions",
      "forecast": "Light rain expected",
      "alert_level": "normal"
    },
    "safety_guidelines": "Wear PPE at all times",
    "equipment_requirements": ["Helmet", "Safety boots", "Gloves"]
  }
}
```

#### GET /api/employee/assignments/{id}/weather
Get weather for assignment site.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Assignment UUID

**Query Parameters:**
- `unit`: Temperature unit (celsius, fahrenheit, default: celsius)

**Response:**
```json
{
  "success": true,
  "data": {
    "site": "Site A",
    "location": "Vadodara, Gujarat, India",
    "current_temp": 28,
    "feels_like": 30,
    "weather_condition": "Partly Cloudy",
    "humidity": 65,
    "wind_speed": 12,
    "forecast": "Light rain expected in evening",
    "hourly_forecast": [...],
    "daily_forecast": [...]
  }
}
```

#### GET /api/employee/assignments/{id}/best-times
Get optimal work times based on weather.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Assignment UUID

**Query Parameters:**
- `date`: Date for analysis (ISO 8601, default: today)

**Response:**
```json
{
  "success": true,
  "data": {
    "date": "2024-01-15",
    "time_slots": [
      {
        "start": "06:00",
        "end": "09:00",
        "weather": "Sunny",
        "temp": 22,
        "precipitation": 0,
        "wind": 5,
        "recommendation": "Excellent"
      },
      {
        "start": "09:00",
        "end": "12:00",
        "weather": "Partly Cloudy",
        "temp": 25,
        "precipitation": 10,
        "wind": 8,
        "recommendation": "Good"
      }
    ]
  }
}
```

#### POST /api/employee/assignments/{id}/share
Share weather concern with supervisor.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Assignment UUID

**Request Body:**
```json
{
  "concern_type": "too_hot",
  "message": "Temperature is too high for outdoor work",
  "suggested_alternative": "2024-01-16 09:00",
  "urgency": "high"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "request_id": "uuid",
    "message": "Concern shared with supervisor"
  }
}
```

#### POST /api/employee/assignments/{id}/request-change
Request schedule/assignment change.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Assignment UUID

**Request Body:**
```json
{
  "change_type": "reschedule",
  "reason": "Weather conditions are unfavorable",
  "preferred_date_time": "2024-01-16T09:00:00Z",
  "alternative_assignment": null,
  "urgency": "high"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "request_id": "uuid",
    "message": "Change request submitted"
  }
}
```

#### GET /api/employee/assignments/search
Search assignments.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `q`: Search query
- `field`: Search field (project, site, description)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "project": "Site Maintenance",
      "site": "Site A",
      "start_date": "2024-01-15"
    }
  ]
}
```

### Weather

#### GET /api/employee/weather/sites
Get weather for sites assigned to employee.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `alert_level` (optional): Filter by alert level (normal, caution, warning, severe)
- `work_suitability` (optional): Filter by suitability (good, acceptable, poor, unsafe)
- `sort` (optional): Sort by field (temperature, humidity)
- `unit` (optional): Temperature unit (celsius, fahrenheit, default: celsius)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "site_name": "Site A",
      "location": "Vadodara, Gujarat, India",
      "assignment_id": "uuid",
      "current_temp": 28,
      "feels_like": 30,
      "weather_condition": "Partly Cloudy",
      "humidity": 65,
      "wind_speed": 12,
      "advisory": "Normal working conditions",
      "alert_level": "normal",
      "work_suitability": "good",
      "last_updated": "2024-01-15T10:00:00Z"
    }
  ]
}
```

#### GET /api/employee/weather/location
Get weather for specific location.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `lat` (optional): Latitude
- `lng` (optional): Longitude
- `city` (optional): City name
- `zip` (optional): Zip/postal code
- `unit` (optional): Temperature unit (celsius, fahrenheit)

**Response:**
```json
{
  "success": true,
  "data": {
    "location": "Vadodara, Gujarat, India",
    "coordinates": {
      "lat": 22.3072,
      "lng": 73.1812
    },
    "current_temp": 28,
    "feels_like": 30,
    "weather_condition": "Partly Cloudy",
    "humidity": 65,
    "wind_speed": 12,
    "forecast": "Light rain expected in evening",
    "hourly_forecast": [...],
    "daily_forecast": [...]
  }
}
```

#### GET /api/employee/weather/search
Search locations for weather.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `q`: Search query (city name, zip code)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "location": "Vadodara, Gujarat, India",
      "coordinates": {
        "lat": 22.3072,
        "lng": 73.1812
      },
      "current_temp": 28,
      "weather_condition": "Partly Cloudy"
    }
  ]
}
```

#### GET /api/employee/weather/location/best-times
Get optimal work times for a location.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `lat` (optional): Latitude
- `lng` (optional): Longitude
- `city` (optional): City name
- `zip` (optional): Zip/postal code
- `date`: Date for analysis (ISO 8601, default: today)

**Response:**
```json
{
  "success": true,
  "data": {
    "location": "Vadodara, Gujarat, India",
    "date": "2024-01-15",
    "time_slots": [
      {
        "start": "06:00",
        "end": "09:00",
        "weather": "Sunny",
        "temp": 22,
        "precipitation": 0,
        "wind": 5,
        "recommendation": "Excellent"
      }
    ]
  }
}
```

#### POST /api/employee/weather/share-concern
Share weather concern with supervisor.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
  "location": "Site A",
  "weather_condition": "Heavy rain",
  "concern_type": "rain_expected",
  "message": "Heavy rain expected, unsafe for outdoor work",
  "affected_assignment": "uuid",
  "suggested_action": "reschedule",
  "urgency": "high"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "request_id": "uuid",
    "message": "Concern shared with supervisor"
  }
}
```

#### GET /api/employee/weather/safety-guidelines
Get safety guidelines for current weather conditions.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `temperature`: Current temperature
- `wind_speed`: Wind speed in km/h
- `precipitation`: Precipitation percentage
- `visibility`: Visibility in km

**Response:**
```json
{
  "success": true,
  "data": {
    "ppe_requirements": ["Waterproof jacket", "Non-slip boots"],
    "work_duration_limits": "Max 4 hours continuous work",
    "break_frequency": "15-minute break every hour",
    "hydration_guidelines": "Drink 500ml water every hour",
    "emergency_procedures": "Seek shelter immediately if conditions worsen",
    "contact_information": {
      "site_supervisor": "Jane Smith",
      "phone": "+1234567890"
    }
  }
}
```

---

## Super Admin APIs

### Users

#### GET /api/super-admin/users
Get all users with hierarchy.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `role` (optional): Filter by role (super_admin, admin, supervisor, employee)
- `status` (optional): Filter by status (active, inactive, suspended, pending, on_leave)
- `department` (optional): Filter by department
- `supervisor_id` (optional): Filter by supervisor UUID
- `site_id` (optional): Filter by site access
- `hierarchy_level` (optional): Filter by hierarchy level
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "full_name": "John Doe",
      "email": "john@example.com",
      "employee_id": "EMP001",
      "role": "supervisor",
      "status": "active",
      "department": "Operations",
      "position": "Safety Manager",
      "phone_number": "+1234567890",
      "location": "Vadodara",
      "last_login": "2024-01-15T10:00:00Z",
      "reports_to": "Jane Smith",
      "hierarchy_level": 2,
      "direct_reports_count": 5,
      "total_team_size": 15,
      "assigned_sites": ["Site A", "Site B"],
      "skills": ["safety", "management"],
      "certifications": [{"name": "Safety Certificate", "expiry": "2024-12-31"}]
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

#### GET /api/super-admin/users/{id}
Get user details.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: User UUID

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "full_name": "John Doe",
    "email": "john@example.com",
    "employee_id": "EMP001",
    "role": "supervisor",
    "status": "active",
    "department": "Operations",
    "position": "Safety Manager",
    "phone_number": "+1234567890",
    "dob": "1990-01-01",
    "join_date": "2020-01-15",
    "exit_date": null,
    "full_address": "123 Main St",
    "location_id": "uuid",
    "location": "Vadodara",
    "supervisor_id": "uuid",
    "supervisor": "Jane Smith",
    "assigned_sites": ["Site A", "Site B"],
    "hierarchy_level": 2,
    "last_login": "2024-01-15T10:00:00Z",
    "skills": ["safety", "management"],
    "certifications": [{"name": "Safety Certificate", "expiry": "2024-12-31"}],
    "max_shift_minutes": 480,
    "profile_picture": "https://s3...",
    "attachments": [
      {"name": "contract.pdf", "url": "https://s3..."}
    ]
  }
}
```

#### GET /api/super-admin/users/{id}/hierarchy
Get user hierarchy tree (full subtree).

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: User UUID

**Query Parameters:**
- `depth` (optional): Maximum depth to return (default: 5)
- `include_inactive` (optional): Include inactive users (default: false)

**Response:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "full_name": "John Doe",
      "role": "supervisor",
      "hierarchy_level": 2
    },
    "subordinates": [
      {
        "id": "uuid",
        "full_name": "Jane Smith",
        "role": "employee",
        "hierarchy_level": 3,
        "subordinates": []
      }
    ]
  }
}
```

#### GET /api/super-admin/users/{id}/subordinates
Get direct reports only.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: User UUID

**Query Parameters:**
- `status` (optional): Filter by status (active, inactive)
- `role` (optional): Filter by role (supervisor, employee)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "full_name": "Jane Smith",
      "role": "employee",
      "status": "active",
      "position": "Technician"
    }
  ]
}
```

#### POST /api/super-admin/users
Create new user.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
  "full_name": "John Doe",
  "username": "johndoe",
  "email": "john@example.com",
  "employee_id": "EMP001",
  "password": "secure_password",
  "phone_number": "+1234567890",
  "position": "Safety Manager",
  "role": "supervisor",
  "department": "Operations",
  "dob": "1990-01-01",
  "full_address": "123 Main St",
  "location_id": "uuid",
  "supervisor_id": "uuid",
  "assigned_sites": ["Site A", "Site B"],
  "skills": ["safety", "management"],
  "certifications": [{"name": "Safety Certificate", "expiry": "2024-12-31"}]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "full_name": "John Doe",
    "username": "johndoe",
    "email": "john@example.com",
    "employee_id": "EMP001",
    "role": "supervisor"
  }
}
```

#### PUT /api/super-admin/users/{id}
Update user.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: User UUID

**Request Body:**
```json
{
  "full_name": "John Doe",
  "email": "john.doe@example.com",
  "phone_number": "+1234567890",
  "position": "Senior Safety Manager",
  "department": "Safety",
  "status": "active"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "full_name": "John Doe",
    "email": "john.doe@example.com",
    "position": "Senior Safety Manager"
  }
}
```

#### DELETE /api/super-admin/users/{id}
Delete user.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: User UUID

**Response:**
```json
{
  "success": true,
  "message": "User deleted successfully"
}
```

#### PUT /api/super-admin/users/{id}/supervisor
Assign/change supervisor.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: User UUID

**Request Body:**
```json
{
  "supervisor_id": "uuid",
  "effective_date": "2024-01-20",
  "reason": "Organizational restructuring"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "supervisor_id": "uuid",
    "effective_date": "2024-01-20"
  }
}
```

#### PUT /api/super-admin/users/{id}/sites
Assign sites to user.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: User UUID

**Request Body:**
```json
{
  "site_ids": ["site_uuid_1", "site_uuid_2"],
  "access_level": "full",
  "effective_date": "2024-01-20",
  "reason": "Site access required for new role"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "assigned_sites": ["Site A", "Site B"]
  }
}
```

#### POST /api/super-admin/users/{id}/subordinate
Add subordinate under user.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Parent User UUID

**Request Body:**
```json
{
  "full_name": "Jane Smith",
  "username": "janesmith",
  "email": "jane@example.com",
  "employee_id": "EMP002",
  "password": "secure_password",
  "role": "employee",
  "position": "Technician",
  "department": "Operations",
  "assigned_sites": ["Site A"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "full_name": "Jane Smith",
    "role": "employee",
    "supervisor_id": "uuid"
  }
}
```

#### PUT /api/super-admin/users/{id}/status
Change user status.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: User UUID

**Request Body:**
```json
{
  "status": "suspended",
  "reason": "Policy violation"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "status": "suspended"
  }
}
```

#### GET /api/super-admin/users/search
Search users.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `q`: Search query
- `field`: Search field (name, email, employee_id)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "full_name": "John Doe",
      "email": "john@example.com",
      "employee_id": "EMP001"
    }
  ]
}
```

#### GET /api/super-admin/users/export
Export users.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `format`: Export format (csv, json)
- `role`: Filter by role
- `status`: Filter by status

**Response:**
```json
{
  "success": true,
  "data": {
    "download_url": "https://s3.../users_export.csv",
    "expires_at": "2024-01-16T12:00:00Z"
  }
}
```

#### POST /api/super-admin/users/import
Import users from CSV.

**Headers:**
```
Authorization: Bearer <jwt_token>
Content-Type: multipart/form-data
```

**Request Body:**
- `file`: CSV file

**Response:**
```json
{
  "success": true,
  "data": {
    "imported_count": 50,
    "failed_count": 2,
    "failed_rows": [
      {"row": 3, "error": "Invalid email format"},
      {"row": 7, "error": "Duplicate employee_id"}
    ]
  }
}
```

### Sites

#### GET /api/super-admin/sites
Get all sites.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `status` (optional): Filter by status (active, inactive, under_construction, decommissioned)
- `site_type` (optional): Filter by type (office, field, warehouse, construction, other)
- `region` (optional): Filter by region
- `manager_id` (optional): Filter by manager UUID
- `weather_alert` (optional): Filter by weather alert (warning, severe)
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "site_id": "VAD-PLANT-01",
      "name": "Vadodara Process Plant",
      "city": "Vadodara",
      "state": "Gujarat",
      "country": "India",
      "status": "active",
      "site_type": "field",
      "area_size": 5000,
      "capacity": 100,
      "current_occupancy": 45,
      "region": "West",
      "zone": "Zone A",
      "manager": "Jane Smith",
      "manager_id": "uuid",
      "contact_phone": "+1234567890",
      "contact_email": "site@example.com",
      "emergency_contact": "Emergency: +9876543210",
      "operating_hours": "08:00-18:00",
      "safety_rating": 4,
      "last_inspection": "2024-01-01",
      "next_inspection": "2024-07-01",
      "assigned_users": 45,
      "active_assignments": 20,
      "weather": {
        "current_weather": "Partly Cloudy",
        "temperature": 28,
        "weather_alert": null
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 30,
    "total_pages": 2
  }
}
```

#### GET /api/super-admin/sites/{id}
Get site details.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Site UUID

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "site_id": "VAD-PLANT-01",
    "name": "Vadodara Process Plant",
    "description": "Main processing plant",
    "city": "Vadodara",
    "state": "Gujarat",
    "country": "India",
    "latitude": 22.3072,
    "longitude": 73.1812,
    "full_address": "123 Industrial Area",
    "location_id": "uuid",
    "timezone": "Asia/Kolkata",
    "status": "active",
    "site_type": "field",
    "area_size": 5000,
    "capacity": 100,
    "current_occupancy": 45,
    "region": "West",
    "zone": "Zone A",
    "manager_id": "uuid",
    "manager": "Jane Smith",
    "contact_phone": "+1234567890",
    "contact_email": "site@example.com",
    "emergency_contact": "Emergency: +9876543210",
    "operating_hours": "08:00-18:00",
    "working_days": ["Mon", "Tue", "Wed", "Thu", "Fri"],
    "safety_rating": 4,
    "last_inspection": "2024-01-01",
    "next_inspection": "2024-07-01",
    "attachments": [
      {"name": "blueprint.pdf", "url": "https://s3..."}
    ],
    "hazards": ["extreme_heat", "chemical"]
  }
}
```

#### GET /api/super-admin/sites/{id}/users
Get users assigned to site.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Site UUID

**Query Parameters:**
- `role` (optional): Filter by role (supervisor, employee)
- `status` (optional): Filter by status (active, inactive)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "full_name": "John Doe",
      "role": "supervisor",
      "status": "active",
      "position": "Safety Manager",
      "assignment_date": "2020-01-15"
    }
  ]
}
```

#### GET /api/super-admin/sites/{id}/assignments
Get assignments at site.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Site UUID

**Query Parameters:**
- `status` (optional): Filter by status (scheduled, in_progress, completed)
- `start_date` (optional): Filter by start date (ISO 8601)
- `end_date` (optional): Filter by end date (ISO 8601)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "user": "John Doe",
      "user_id": "uuid",
      "status": "in_progress",
      "start_time": "2024-01-15T08:00:00Z",
      "end_time": "2024-01-15T17:00:00Z"
    }
  ]
}
```

#### GET /api/super-admin/sites/{id}/weather
Get site weather.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Site UUID

**Query Parameters:**
- `unit`: Temperature unit (celsius, fahrenheit, default: celsius)

**Response:**
```json
{
  "success": true,
  "data": {
    "site": "Vadodara Process Plant",
    "location": "Vadodara, Gujarat, India",
    "current_temp": 28,
    "feels_like": 30,
    "weather_condition": "Partly Cloudy",
    "humidity": 65,
    "wind_speed": 12,
    "forecast": "Light rain expected in evening",
    "hourly_forecast": [...],
    "daily_forecast": [...]
  }
}
```

#### POST /api/super-admin/sites
Create new site.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
  "site_id": "VAD-PLANT-02",
  "name": "Vadodara Warehouse",
  "description": "Storage facility",
  "city": "Vadodara",
  "state": "Gujarat",
  "country": "India",
  "latitude": 22.3072,
  "longitude": 73.1812,
  "full_address": "456 Warehouse Road",
  "location_id": "uuid",
  "timezone": "Asia/Kolkata",
  "site_type": "warehouse",
  "area_size": 3000,
  "capacity": 50,
  "region": "West",
  "zone": "Zone B",
  "manager_id": "uuid",
  "contact_phone": "+1234567890",
  "contact_email": "warehouse@example.com",
  "emergency_contact": "Emergency: +9876543210",
  "operating_hours": "08:00-18:00",
  "safety_rating": 5
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "site_id": "VAD-PLANT-02",
    "name": "Vadodara Warehouse"
  }
}
```

#### PUT /api/super-admin/sites/{id}
Update site.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Site UUID

**Request Body:**
```json
{
  "name": "Updated Site Name",
  "status": "active",
  "capacity": 60,
  "safety_rating": 5
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "Updated Site Name"
  }
}
```

#### DELETE /api/super-admin/sites/{id}
Delete site.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Site UUID

**Response:**
```json
{
  "success": true,
  "message": "Site deleted successfully"
}
```

#### PUT /api/super-admin/sites/{id}/status
Change site status.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Site UUID

**Request Body:**
```json
{
  "status": "under_construction",
  "reason": "Maintenance work"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "status": "under_construction"
  }
}
```

#### PUT /api/super-admin/sites/{id}/manager
Change site manager.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Site UUID

**Request Body:**
```json
{
  "manager_id": "uuid",
  "reason": "Manager changed due to promotion"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "manager_id": "uuid"
  }
}
```

#### GET /api/super-admin/sites/search
Search sites.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `q`: Search query
- `field`: Search field (name, code, address, city)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "site_id": "VAD-PLANT-01",
      "name": "Vadodara Process Plant",
      "city": "Vadodara"
    }
  ]
}
```

#### GET /api/super-admin/sites/export
Export sites.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `format`: Export format (csv, json)
- `status`: Filter by status
- `site_type`: Filter by type

**Response:**
```json
{
  "success": true,
  "data": {
    "download_url": "https://s3.../sites_export.csv",
    "expires_at": "2024-01-16T12:00:00Z"
  }
}
```

#### POST /api/super-admin/sites/import
Import sites from CSV.

**Headers:**
```
Authorization: Bearer <jwt_token>
Content-Type: multipart/form-data
```

**Request Body:**
- `file`: CSV file

**Response:**
```json
{
  "success": true,
  "data": {
    "imported_count": 10,
    "failed_count": 1,
    "failed_rows": [
      {"row": 2, "error": "Invalid coordinates"}
    ]
  }
}
```

#### GET /api/super-admin/sites/map-data
Get sites for map view.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `status`: Filter by status (default: active)
- `weather_overlay`: Include weather data (default: false)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "Vadodara Process Plant",
      "latitude": 22.3072,
      "longitude": 73.1812,
      "status": "active",
      "weather": {
        "temperature": 28,
        "condition": "Partly Cloudy"
      }
    }
  ]
}
```

### Action Logs

#### GET /api/super-admin/action-logs
Get all action logs.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `start_date` (optional): Filter by start date (ISO 8601)
- `end_date` (optional): Filter by end date (ISO 8601)
- `user_id` (optional): Filter by user UUID
- `user_role` (optional): Filter by user role
- `action_category` (optional): Filter by category (user, site, assignment, event, request, weather, system, security)
- `status` (optional): Filter by status (success, failure, warning)
- `impact_level` (optional): Filter by impact level (low, medium, high, critical)
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "timestamp": "2024-01-15T10:00:00Z",
      "user": "John Doe",
      "user_id": "uuid",
      "user_role": "supervisor",
      "action_type": "created",
      "action_category": "assignment",
      "entity_type": "Assignment",
      "entity_id": "uuid",
      "entity_name": "Site Maintenance",
      "description": "Created new assignment for John Doe",
      "details": {
        "before": null,
        "after": {...},
        "changed_fields": []
      },
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0...",
      "status": "success",
      "error_message": null,
      "impact_level": "medium",
      "session_id": "uuid"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1000,
    "total_pages": 50
  }
}
```

#### GET /api/super-admin/action-logs/{id}
Get log details.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Log UUID

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "timestamp": "2024-01-15T10:00:00Z",
    "user": "John Doe",
    "user_id": "uuid",
    "user_role": "supervisor",
    "action_type": "created",
    "action_category": "assignment",
    "entity_type": "Assignment",
    "entity_id": "uuid",
    "entity_name": "Site Maintenance",
    "description": "Created new assignment for John Doe",
    "details": {
      "before": null,
      "after": {
        "user_id": "uuid",
        "site_id": "uuid",
        "status": "scheduled"
      },
      "changed_fields": []
    },
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0...",
    "status": "success",
    "error_message": null,
    "impact_level": "medium",
    "session_id": "uuid"
  }
}
```

#### GET /api/super-admin/action-logs/{id}/related
Get related logs.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Log UUID

**Query Parameters:**
- `group_by`: Group by (session, entity)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "timestamp": "2024-01-15T10:01:00Z",
      "action_type": "updated",
      "description": "Updated assignment"
    }
  ]
}
```

#### GET /api/super-admin/action-logs/search
Search logs.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `q`: Search query
- `field`: Search field (description, entity_name, error_message)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "timestamp": "2024-01-15T10:00:00Z",
      "action_type": "created",
      "description": "Created new assignment"
    }
  ]
}
```

#### GET /api/super-admin/action-logs/export
Export logs.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `format`: Export format (csv, json, pdf)
- `start_date`: Filter by start date (ISO 8601)
- `end_date`: Filter by end date (ISO 8601)
- `user_role`: Filter by user role
- `action_category`: Filter by category

**Response:**
```json
{
  "success": true,
  "data": {
    "download_url": "https://s3.../logs_export.csv",
    "expires_at": "2024-01-16T12:00:00Z"
  }
}
```

#### GET /api/super-admin/action-logs/statistics
Get log statistics.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `start_date`: Filter by start date (ISO 8601)
- `end_date`: Filter by end date (ISO 8601)
- `group_by`: Group by (category, role, user)

**Response:**
```json
{
  "success": true,
  "data": {
    "total_actions": 1000,
    "actions_by_category": {
      "user": 200,
      "site": 150,
      "assignment": 300,
      "event": 100,
      "request": 150,
      "weather": 50,
      "system": 30,
      "security": 20
    },
    "actions_by_role": {
      "super_admin": 100,
      "admin": 200,
      "supervisor": 400,
      "employee": 300
    },
    "success_rate": 95.5,
    "failure_rate": 4.5,
    "most_active_users": [
      {"user_id": "uuid", "name": "John Doe", "action_count": 150}
    ],
    "most_affected_entities": [
      {"entity_type": "Assignment", "entity_id": "uuid", "action_count": 50}
    ]
  }
}
```

#### PUT /api/super-admin/action-logs/{id}/investigate
Flag for investigation.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Log UUID

**Request Body:**
```json
{
  "investigation_notes": "Suspicious activity detected",
  "assigned_to": "uuid",
  "priority": "high"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "investigation_status": "pending",
    "assigned_to": "uuid"
  }
}
```

#### PUT /api/super-admin/action-logs/{id}/resolve
Mark investigation as resolved.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Log UUID

**Request Body:**
```json
{
  "resolution_notes": "Investigation completed, no issues found"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "investigation_status": "resolved"
  }
}
```

#### DELETE /api/super-admin/action-logs/{id}
Delete log (super admin only with confirmation).

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Log UUID

**Response:**
```json
{
  "success": true,
  "message": "Log deleted successfully"
}
```

#### GET /api/super-admin/action-logs/live-feed
Real-time log feed (WebSocket or SSE).

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `filter_impact`: Filter by impact level (high, critical)

**Response:**
Server-Sent Events stream or WebSocket connection.

---

## Weather APIs

### GET /api/weather/current
Get current weather for location.

**Query Parameters:**
- `lat`: Latitude
- `lng`: Longitude
- `unit`: Temperature unit (celsius, fahrenheit, default: celsius)

**Response:**
```json
{
  "success": true,
  "data": {
    "location": "Vadodara, Gujarat, India",
    "coordinates": {
      "lat": 22.3072,
      "lng": 73.1812
    },
    "current_temp": 28,
    "feels_like": 30,
    "weather_condition": "Partly Cloudy",
    "humidity": 65,
    "wind_speed": 12,
    "wind_direction": "NE",
    "visibility": 8,
    "uv_index": 6,
    "air_quality": "Moderate",
    "precipitation": 0
  }
}
```

### GET /api/weather/forecast
Get weather forecast.

**Query Parameters:**
- `lat`: Latitude
- `lng`: Longitude
- `days`: Number of days (default: 7)
- `unit`: Temperature unit (celsius, fahrenheit, default: celsius)

**Response:**
```json
{
  "success": true,
  "data": {
    "location": "Vadodara, Gujarat, India",
    "daily_forecast": [
      {
        "date": "2024-01-15",
        "temp_max": 30,
        "temp_min": 22,
        "weather_condition": "Partly Cloudy",
        "precipitation_chance": 20
      }
    ],
    "hourly_forecast": [...]
  }
}
```

### GET /api/weather/alerts
Get weather alerts for location.

**Query Parameters:**
- `lat`: Latitude
- `lng`: Longitude

**Response:**
```json
{
  "success": true,
  "data": {
    "location": "Vadodara, Gujarat, India",
    "alerts": [
      {
        "type": "heavy_rain",
        "severity": "warning",
        "start_time": "2024-01-15T18:00:00Z",
        "end_time": "2024-01-16T06:00:00Z",
        "description": "Heavy rain expected"
      }
    ]
  }
}
```

---

## Common APIs

### GET /api/locations
Get all locations.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `active`: Filter by active status (default: true)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "location_code": "vadodara-gujarat",
      "display_name": "Vadodara, Gujarat",
      "city": "Vadodara",
      "state": "Gujarat",
      "country": "India",
      "country_code": "IN",
      "zip_code": "390001",
      "timezone": "Asia/Kolkata"
    }
  ]
}
```

### GET /api/notifications
Get notifications for authenticated user.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `read`: Filter by read status (true, false)
- `type`: Filter by notification type
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "title": "Extreme Heat Advisory",
      "message": "30-min break required",
      "notification_type": "heat_alert",
      "priority": "high",
      "read": false,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 50,
    "total_pages": 3
  }
}
```

### PUT /api/notifications/{id}/read
Mark notification as read.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Path Parameters:**
- `id`: Notification UUID

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "read": true,
    "read_at": "2024-01-15T10:30:00Z"
  }
}
```

### GET /api/user/profile
Get authenticated user profile.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "full_name": "John Doe",
    "username": "johndoe",
    "email": "john@example.com",
    "employee_id": "EMP001",
    "role": "supervisor",
    "department": "Operations",
    "position": "Safety Manager",
    "phone_number": "+1234567890",
    "profile_picture": "https://s3...",
    "skills": ["safety", "management"],
    "certifications": [{"name": "Safety Certificate", "expiry": "2024-12-31"}]
  }
}
```

### PUT /api/user/profile
Update authenticated user profile.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
  "full_name": "John Doe",
  "phone_number": "+1234567890",
  "profile_picture": "https://s3..."
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "full_name": "John Doe",
    "phone_number": "+1234567890"
  }
}
```

---

## Error Codes

| Error Code | Description |
|------------|-------------|
| `AUTH_INVALID_TOKEN` | Invalid or expired JWT token |
| `AUTH_INSUFFICIENT_PERMISSIONS` | User does not have required permissions |
| `VALIDATION_ERROR` | Request validation failed |
| `NOT_FOUND` | Resource not found |
| `CONFLICT` | Resource conflict (e.g., duplicate) |
| `INTERNAL_ERROR` | Internal server error |
| `SERVICE_UNAVAILABLE` | External service unavailable (e.g., weather API) |

---

## Rate Limiting

API endpoints are rate-limited to prevent abuse:
- Standard rate: 100 requests per minute per user
- Burst rate: 200 requests per minute per user

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642245600
```

---

## Versioning

API version is included in the URL path:
```
/api/v1/...
```

Current version: v1

---

## Changelog

### v1.0.0 (2024-01-15)
- Initial API release
- Authentication endpoints
- Supervisor APIs (members, events, weather, requests)
- Employee APIs (assignments, weather)
- Super Admin APIs (users, sites, action logs)
- Weather APIs
- Common APIs
