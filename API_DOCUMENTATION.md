# VMS REST API Documentation

Base URL: `http://localhost:5000/api`

All API endpoints require an authenticated session (Flask-Login cookie). Send requests from the same browser session or include session cookies.

## Response Format

```json
{
  "success": true,
  "message": "Optional message",
  "data": { }
}
```

HTTP status codes: `200` OK, `201` Created, `400` Bad Request, `401` Unauthorized, `403` Forbidden, `404` Not Found

---

## Authentication

### GET /api/auth/me

Returns the currently logged-in user.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "admin",
    "email": "admin@vms.local",
    "role": "admin",
    "is_active": 1
  }
}
```

---

## Dashboard

### GET /api/dashboard/stats

Returns analytics data for the dashboard.

**Roles:** All authenticated users

**Response:**
```json
{
  "success": true,
  "data": {
    "visitors_today": 5,
    "checked_in_now": 2,
    "employees": 10,
    "departments": 5,
    "status_breakdown": [{"status": "pending", "count": 3}],
    "daily_stats": [{"date": "2025-06-13", "total": 5}],
    "monthly_stats": [{"month": "2025-06", "total": 42}]
  }
}
```

---

## Visitors

### GET /api/visitors

List visitors with search and pagination.

**Query Parameters:**

| Parameter       | Type   | Description                    |
|----------------|--------|--------------------------------|
| page           | int    | Page number (default: 1)       |
| per_page       | int    | Items per page (default: 15)   |
| search         | string | Search name, phone, code, etc. |
| status         | string | pending, approved, checked_in  |
| department_id  | int    | Filter by department           |
| date_from      | date   | YYYY-MM-DD                     |
| date_to        | date   | YYYY-MM-DD                     |

**Roles:** All authenticated (employees see only their hosted visitors)

---

### GET /api/visitors/{id}

Get visitor details with approval info.

---

### POST /api/visitors

Register a new visitor.

**Roles:** admin, receptionist

**Request Body:**
```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "phone": "9876543210",
  "email": "jane@company.com",
  "company": "Acme Corp",
  "purpose": "Business meeting",
  "host_employee_id": 1,
  "id_proof_type": "Passport",
  "notes": "Optional notes"
}
```

---

### POST /api/visitors/{id}/approve

Approve a pending visitor. Generates QR pass.

**Roles:** admin, employee

**Request Body:**
```json
{ "comments": "Approved for 2pm meeting" }
```

---

### POST /api/visitors/{id}/reject

Reject a pending visitor.

**Roles:** admin, employee

**Request Body:**
```json
{ "comments": "Not available today" }
```

---

### POST /api/visitors/{id}/check-in

Check in an approved visitor.

**Roles:** admin, receptionist

**Request Body:**
```json
{ "badge_number": "BDG-001" }
```

---

### POST /api/visitors/{id}/check-out

Check out a checked-in visitor.

**Roles:** admin, receptionist

---

### GET /api/visitors/active

List all currently checked-in visitors.

---

### GET /api/visitors/code/{visitor_code}

Lookup visitor by code (for QR scan integration).

---

## Employees & Departments

### GET /api/employees

List all active employees.

### GET /api/departments

List all active departments.

---

## Reports

### GET /api/reports

Get report data for a date range.

**Roles:** admin, receptionist

**Query Parameters:**

| Parameter  | Type   | Description                          |
|-----------|--------|--------------------------------------|
| period    | string | daily, weekly, monthly               |
| date_from | date   | Custom start (YYYY-MM-DD)            |
| date_to   | date   | Custom end (YYYY-MM-DD)              |

---

## Web Export Endpoints (Browser)

These are HTML routes (not under `/api`) but useful for integrations:

- `GET /reports/export?format=csv&period=monthly`
- `GET /reports/export?format=excel&period=weekly`

---

## Error Examples

**401 Unauthorized:**
```json
{ "success": false, "message": "Authentication required" }
```

**403 Forbidden:**
```json
{ "success": false, "message": "Access denied" }
```

**400 Bad Request:**
```json
{ "success": false, "message": "Missing fields: phone, purpose" }
```

---

## Example: cURL with Session

```bash
# Login via browser first, then use session cookie, or test with Flask test client.

curl -X GET http://localhost:5000/api/visitors \
  -H "Cookie: session=YOUR_SESSION_COOKIE"

curl -X POST http://localhost:5000/api/visitors \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -d '{"first_name":"John","last_name":"Doe","phone":"1234567890","purpose":"Meeting","host_employee_id":1}'
```
