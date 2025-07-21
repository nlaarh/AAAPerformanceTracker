# AAAPerformanceTracker API Documentation
## Complete System API Reference
**Version:** 3.0.0  
**Date:** July 20, 2025  
**Base URL:** https://your-domain.com

---

## Table of Contents
1. [Authentication](#authentication)
2. [Core Endpoints](#core-endpoints)
3. [Assessment Management](#assessment-management)
4. [User Management](#user-management)
5. [Assessment Forms](#assessment-forms)
6. [Reports & Analytics](#reports--analytics)
7. [AI Integration](#ai-integration)
8. [Data Models](#data-models)
9. [Error Handling](#error-handling)
10. [Rate Limiting](#rate-limiting)

---

## Authentication

### Login
**POST** `/login`

Authenticate user and create session.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "user@example.com",
    "role": "admin"
  },
  "redirect_url": "/dashboard"
}
```

### Logout
**POST** `/logout`

Destroy user session.

**Response:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

### Health Check
**GET** `/health`

System health status (no authentication required).

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-07-20T00:00:00Z"
}
```

---

## Core Endpoints

### Dashboard
**GET** `/dashboard`

Role-based dashboard view.

**Authentication:** Required  
**Roles:** admin, board_member, officer

**Response Structure:**
- **Admin:** System overview, user counts, assessment statistics
- **Board Member:** Assigned reviews, completion status  
- **Officer:** Self-assessment status, results access

### My Assignments
**GET** `/my_assignments`

User's current assessment tasks.

**Authentication:** Required  
**Query Parameters:**
- `status` (optional): `pending`, `completed`, `overdue`
- `period_id` (optional): Filter by assessment period

**Response:**
```json
{
  "assignments": [
    {
      "id": 1,
      "period_name": "2025 Annual Review",
      "officer_name": "Emily Davis",
      "reviewer_name": "John Doe",
      "is_self_assessment": false,
      "status": "pending",
      "due_date": "2025-02-15",
      "submitted_at": null,
      "is_admin_approved": false
    }
  ],
  "pending_count": 3,
  "completed_count": 5
}
```

---

## Assessment Management

### Assessment Periods

#### List Assessment Periods
**GET** `/admin/assessment_periods`

**Authentication:** Required (Admin only)

**Response:**
```json
{
  "periods": [
    {
      "id": 1,
      "name": "2025 Annual Executive Review",
      "description": "Annual performance review...",
      "start_date": "2025-01-01",
      "end_date": "2025-12-31",
      "due_date": "2025-02-15",
      "is_active": true,
      "completion_rate": 75.5,
      "total_assignments": 20,
      "completed_assignments": 15
    }
  ]
}
```

#### Create Assessment Period
**POST** `/admin/assessment_periods`

**Request Body:**
```json
{
  "name": "Q2 2025 Performance Review",
  "description": "Quarterly performance check-in",
  "start_date": "2025-04-01",
  "end_date": "2025-06-30",
  "due_date": "2025-07-15",
  "reviewer_form_ids": [1, 2],
  "self_review_form_ids": [3]
}
```

#### Update Assessment Period
**PUT** `/admin/assessment_periods/{period_id}`

**Path Parameters:**
- `period_id`: Assessment period ID

#### Delete Assessment Period
**DELETE** `/admin/assessment_periods/{period_id}`

**Response:**
```json
{
  "success": true,
  "message": "Assessment period deleted successfully",
  "deleted_dependencies": {
    "assignments": 15,
    "responses": 45,
    "activity_logs": 30
  }
}
```

### Assessment Assignments

#### Assignment Matrix
**GET** `/admin/assignment_matrix/{period_id}`

**Path Parameters:**
- `period_id`: Assessment period ID

**Response:**
```json
{
  "matrix": {
    "reviewees": [
      {"id": 6, "name": "Emily Davis", "role": "officer"}
    ],
    "reviewers": [
      {"id": 2, "name": "Jennifer Rodriguez", "role": "board_member"}
    ],
    "assignments": [
      {
        "officer_id": 6,
        "reviewer_id": 2,
        "exists": true,
        "is_completed": false,
        "assignment_id": 1
      }
    ]
  }
}
```

#### Create/Update Assignments
**POST** `/admin/create_assignments/{period_id}`

**Request Body:**
```json
{
  "assignments": [
    {
      "officer_id": 6,
      "reviewer_id": 2,
      "selected": true
    }
  ]
}
```

### Assessment Execution

#### Start Assessment
**GET** `/assessment/{assignment_id}/start`

**Path Parameters:**
- `assignment_id`: Assessment assignment ID

**Response:**
```json
{
  "assignment": {
    "id": 1,
    "officer_name": "Emily Davis",
    "reviewer_name": "John Doe",
    "is_self_assessment": false,
    "form": {
      "id": 1,
      "title": "Executive Performance Review",
      "questions": [
        {
          "id": 1,
          "question_name": "Financial Performance",
          "question_text": "How effectively...",
          "question_type": "rating",
          "is_required": true,
          "settings": {"min_rating": 1, "max_rating": 5}
        }
      ]
    }
  }
}
```

#### Submit Assessment
**POST** `/assessment/{assignment_id}/submit`

**Request Body:**
```json
{
  "responses": [
    {
      "question_id": 1,
      "response_number": 4
    },
    {
      "question_id": 2,
      "response_text": "Excellent financial leadership..."
    }
  ],
  "is_final_submission": true
}
```

#### Assessment Progress
**GET** `/assessment/{assignment_id}/progress`

**Response:**
```json
{
  "progress": {
    "total_questions": 10,
    "answered_questions": 7,
    "required_questions": 8,
    "required_answered": 6,
    "completion_percentage": 70,
    "can_submit": false
  }
}
```

---

## User Management

### List Users
**GET** `/admin/users`

**Authentication:** Required (Admin only)  
**Query Parameters:**
- `role` (optional): Filter by role
- `active` (optional): Filter by active status
- `search` (optional): Search by name or email

**Response:**
```json
{
  "users": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "role": "admin",
      "is_active": true,
      "created_at": "2025-01-01T00:00:00Z",
      "last_login": "2025-07-20T10:00:00Z"
    }
  ],
  "total": 25,
  "page": 1,
  "per_page": 50
}
```

### Create User
**POST** `/admin/users`

**Request Body:**
```json
{
  "name": "Jane Smith",
  "email": "jane@example.com",
  "role": "board_member",
  "password": "secure_password_here"
}
```

### Update User
**PUT** `/admin/users/{user_id}`

### Activate/Deactivate User
**POST** `/admin/users/{user_id}/toggle_active`

### Reset User Password
**POST** `/admin/users/{user_id}/reset_password`

**Request Body:**
```json
{
  "new_password": "new_secure_password"
}
```

---

## Assessment Forms

### List Assessment Forms
**GET** `/admin/assessment_forms`

**Response:**
```json
{
  "forms": [
    {
      "id": 1,
      "title": "Executive Performance Review",
      "description": "Comprehensive performance evaluation...",
      "is_active": true,
      "is_template": false,
      "question_count": 10,
      "created_by": "Admin User",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

### Create Assessment Form
**POST** `/admin/assessment_forms`

**Request Body:**
```json
{
  "title": "New Assessment Form",
  "description": "Description of the form",
  "is_template": false,
  "questions": [
    {
      "question_name": "Performance Rating",
      "question_text": "Rate overall performance",
      "question_type": "rating",
      "order": 1,
      "is_required": true,
      "settings": {
        "min_rating": 1,
        "max_rating": 5,
        "labels": ["Poor", "Fair", "Good", "Very Good", "Excellent"]
      }
    }
  ]
}
```

### Form Questions Management

#### Add Question
**POST** `/admin/assessment_forms/{form_id}/questions`

#### Update Question
**PUT** `/admin/assessment_forms/{form_id}/questions/{question_id}`

#### Delete Question
**DELETE** `/admin/assessment_forms/{form_id}/questions/{question_id}`

#### Reorder Questions
**POST** `/admin/assessment_forms/{form_id}/questions/reorder`

**Request Body:**
```json
{
  "question_orders": [
    {"question_id": 1, "order": 1},
    {"question_id": 2, "order": 2}
  ]
}
```

---

## Reports & Analytics

### Assessment Matrix
**GET** `/officer_reviews/{officer_id}/{period_id}`

**Response:**
```json
{
  "officer": {
    "id": 6,
    "name": "Emily Davis",
    "role": "officer"
  },
  "period": {
    "id": 1,
    "name": "2025 Annual Review"
  },
  "matrix": {
    "questions": [
      {
        "id": 1,
        "question_name": "Financial Performance",
        "category": "Financial Strategy"
      }
    ],
    "reviewers": [
      {
        "id": 2,
        "name": "Jennifer Rodriguez",
        "is_self": false
      }
    ],
    "responses": [
      {
        "question_id": 1,
        "reviewer_id": 2,
        "response_number": 4,
        "response_text": "Excellent performance..."
      }
    ],
    "averages": {
      "question_averages": [
        {"question_id": 1, "average": 4.2, "count": 5}
      ],
      "reviewer_averages": [
        {"reviewer_id": 2, "average": 4.0, "count": 10}
      ],
      "overall_average": 4.1
    }
  }
}
```

### Excel Export
**GET** `/export/assessment_matrix/{officer_id}/{period_id}`

**Response:** Excel file download

**Headers:**
```
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="Emily_Davis_Assessment_Matrix_2025.xlsx"
```

### Activity Logs
**GET** `/admin/activity_logs`

**Query Parameters:**
- `user_id` (optional): Filter by user
- `action` (optional): Filter by action type
- `start_date` (optional): Start date filter
- `end_date` (optional): End date filter
- `page` (optional): Page number
- `per_page` (optional): Items per page

**Response:**
```json
{
  "logs": [
    {
      "id": 1,
      "user_name": "John Doe",
      "action": "submit_assessment",
      "description": "Submitted assessment for Emily Davis",
      "ip_address": "192.168.1.100",
      "timestamp": "2025-07-20T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 250,
    "pages": 5
  }
}
```

---

## AI Integration

### Generate AI Report
**POST** `/admin/generate_ai_report/{officer_id}/{period_id}`

**Authentication:** Required (Admin only)

**Response:**
```json
{
  "success": true,
  "message": "AI report generation started",
  "report_id": 1,
  "estimated_completion": "2025-07-20T10:05:00Z"
}
```

### AI Report Status
**GET** `/admin/ai_report_status/{officer_id}/{period_id}`

**Response:**
```json
{
  "status": "completed",
  "progress": 100,
  "report": {
    "id": 1,
    "title": "AI Performance Analysis - Emily Davis",
    "generated_at": "2025-07-20T10:05:00Z",
    "total_reviewers": 4,
    "average_rating": 4.2,
    "total_questions": 10
  }
}
```

### Download AI Report
**GET** `/admin/download_ai_report/{report_id}`

**Response:** PDF file download

### AI Chatbot
**POST** `/admin/ai_chatbot`

**Request Body:**
```json
{
  "message": "Show me average ratings for Emily Davis"
}
```

**Response:**
```json
{
  "response": "Emily Davis has an average rating of 4.2 across all categories in the 2025 Annual Review, based on 4 reviewer assessments.",
  "sql_query": "SELECT AVG(response_number) FROM assessment_response WHERE...",
  "data": [
    {"category": "Financial Strategy", "average": 4.4},
    {"category": "Operations", "average": 4.0}
  ]
}
```

---

## Data Models

### User Model
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "role": "admin|board_member|officer",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z"
}
```

### Assessment Period Model
```json
{
  "id": 1,
  "name": "2025 Annual Review",
  "description": "Annual performance review...",
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "due_date": "2025-02-15",
  "is_active": true,
  "created_by": 1,
  "created_at": "2025-01-01T00:00:00Z"
}
```

### Assessment Assignment Model
```json
{
  "id": 1,
  "period_id": 1,
  "officer_id": 6,
  "reviewer_id": 2,
  "is_completed": false,
  "is_submitted": false,
  "is_admin_approved": false,
  "completed_at": null,
  "submitted_at": null,
  "admin_approved_at": null,
  "admin_notes": null,
  "created_at": "2025-01-01T00:00:00Z"
}
```

### Assessment Form Model
```json
{
  "id": 1,
  "title": "Executive Performance Review",
  "description": "Comprehensive evaluation form",
  "is_active": true,
  "is_template": false,
  "created_by": 1,
  "created_at": "2025-01-01T00:00:00Z",
  "questions": [
    {
      "id": 1,
      "question_name": "Financial Performance",
      "question_text": "Rate financial performance...",
      "question_type": "rating",
      "order": 1,
      "is_required": true,
      "settings": {"min_rating": 1, "max_rating": 5}
    }
  ]
}
```

### Assessment Response Model
```json
{
  "id": 1,
  "assessment_assignment_id": 1,
  "question_id": 1,
  "response_text": "Excellent performance...",
  "response_number": 4,
  "response_boolean": null,
  "response_date": null,
  "response_json": null,
  "created_at": "2025-07-20T10:00:00Z"
}
```

---

## Error Handling

### Standard Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "reason": "Email format is invalid"
    }
  },
  "timestamp": "2025-07-20T10:00:00Z"
}
```

### HTTP Status Codes
- **200** - Success
- **201** - Created
- **400** - Bad Request (validation errors)
- **401** - Unauthorized (not logged in)
- **403** - Forbidden (insufficient permissions)
- **404** - Not Found
- **409** - Conflict (duplicate data)
- **422** - Unprocessable Entity (business logic error)
- **500** - Internal Server Error

### Error Categories

#### Authentication Errors
```json
{
  "error": {
    "code": "AUTH_REQUIRED",
    "message": "Authentication required"
  }
}
```

#### Permission Errors
```json
{
  "error": {
    "code": "INSUFFICIENT_PERMISSIONS",
    "message": "Admin privileges required"
  }
}
```

#### Validation Errors
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "email": ["Email is required"],
      "password": ["Password must be at least 8 characters"]
    }
  }
}
```

#### Business Logic Errors
```json
{
  "error": {
    "code": "BUSINESS_RULE_VIOLATION",
    "message": "Cannot delete period with active assignments"
  }
}
```

---

## Rate Limiting

### Default Limits
- **General API calls:** 1000 requests per hour per user
- **Login attempts:** 5 attempts per 15 minutes per IP
- **AI operations:** 10 requests per hour per user
- **Report generation:** 5 reports per hour per user

### Rate Limit Headers
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1642678800
```

### Rate Limit Exceeded Response
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Try again in 15 minutes.",
    "retry_after": 900
  }
}
```

---

## Webhooks (Future Feature)

### Assessment Completion Webhook
```json
{
  "event": "assessment_completed",
  "data": {
    "assignment_id": 1,
    "officer_id": 6,
    "reviewer_id": 2,
    "period_id": 1,
    "completed_at": "2025-07-20T10:00:00Z"
  },
  "timestamp": "2025-07-20T10:00:00Z"
}
```

---

## SDK Examples

### Python SDK Usage
```python
import requests

class AAAPerformanceClient:
    def __init__(self, base_url, session_cookie):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.cookies.set('session', session_cookie)
    
    def get_assignments(self, status=None):
        params = {'status': status} if status else {}
        response = self.session.get(
            f"{self.base_url}/my_assignments",
            params=params
        )
        return response.json()
    
    def submit_assessment(self, assignment_id, responses):
        data = {
            'responses': responses,
            'is_final_submission': True
        }
        response = self.session.post(
            f"{self.base_url}/assessment/{assignment_id}/submit",
            json=data
        )
        return response.json()

# Usage
client = AAAPerformanceClient('https://your-domain.com', 'session_cookie')
assignments = client.get_assignments(status='pending')
```

### JavaScript SDK Usage
```javascript
class AAAPerformanceAPI {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }
    
    async getAssignments(status = null) {
        const params = status ? `?status=${status}` : '';
        const response = await fetch(`${this.baseUrl}/my_assignments${params}`, {
            credentials: 'include'
        });
        return response.json();
    }
    
    async submitAssessment(assignmentId, responses) {
        const response = await fetch(`${this.baseUrl}/assessment/${assignmentId}/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                responses: responses,
                is_final_submission: true
            })
        });
        return response.json();
    }
}

// Usage
const api = new AAAPerformanceAPI('https://your-domain.com');
const assignments = await api.getAssignments('pending');
```

---

**API Support:**
- **Documentation:** This API reference
- **Postman Collection:** Available on request
- **Interactive API Explorer:** Available at `/docs` (if enabled)
- **Rate Limits:** See Rate Limiting section
- **Authentication:** Session-based authentication required for most endpoints

---

*This API documentation covers all available endpoints and functionality in the AAAPerformanceTracker system. Use this reference for integration and development purposes.*