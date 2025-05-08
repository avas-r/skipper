    "queue_id": "123e4567-e89b-12d3-a456-426614174019",
    "name": "Customer Onboarding Queue",
    "job_id": "123e4567-e89b-12d3-a456-426614174020",
    "job": {
      "name": "Process Customer Onboarding"
    },
    "status": "active",
    "item_count": 15,
    "created_at": "2023-06-20T10:30:45Z"
  }
]
```

#### `POST /queues`

Create a new queue.

**Request:**
```json
{
  "name": "Invoice Processing Queue",
  "description": "Queue for processing invoices",
  "job_id": "123e4567-e89b-12d3-a456-426614174011",
  "max_retries": 3,
  "retry_delay_seconds": 600,
  "timeout_seconds": 1800
}
```

**Response:**
```json
{
  "queue_id": "123e4567-e89b-12d3-a456-426614174021",
  "name": "Invoice Processing Queue",
  "description": "Queue for processing invoices",
  "job_id": "123e4567-e89b-12d3-a456-426614174011",
  "max_retries": 3,
  "retry_delay_seconds": 600,
  "timeout_seconds": 1800,
  "status": "active",
  "created_at": "2023-07-15T15:40:45Z"
}
```

#### `GET /queues/{queue_id}`

Get queue details.

**Response:**
```json
{
  "queue_id": "123e4567-e89b-12d3-a456-426614174019",
  "name": "Customer Onboarding Queue",
  "description": "Queue for customer onboarding requests",
  "job_id": "123e4567-e89b-12d3-a456-426614174020",
  "job": {
    "name": "Process Customer Onboarding",
    "parameters": {
      "notification_template": "onboarding_welcome"
    }
  },
  "max_retries": 3,
  "retry_delay_seconds": 300,
  "timeout_seconds": 3600,
  "status": "active",
  "item_count": 15,
  "processing_count": 2,
  "failed_count": 1,
  "created_at": "2023-06-20T10:30:45Z",
  "updated_at": "2023-07-15T10:15:30Z"
}
```

#### `PUT /queues/{queue_id}`

Update a queue.

**Request:**
```json
{
  "description": "Updated description for customer onboarding queue",
  "max_retries": 5,
  "retry_delay_seconds": 900
}
```

**Response:**
```json
{
  "queue_id": "123e4567-e89b-12d3-a456-426614174019",
  "name": "Customer Onboarding Queue",
  "description": "Updated description for customer onboarding queue",
  "max_retries": 5,
  "retry_delay_seconds": 900,
  "updated_at": "2023-07-15T15:45:45Z"
}
```

#### `DELETE /queues/{queue_id}`

Delete a queue.

**Response Status Code:** 204 No Content

#### `POST /queues/{queue_id}/pause`

Pause a queue.

**Response:**
```json
{
  "queue_id": "123e4567-e89b-12d3-a456-426614174019",
  "name": "Customer Onboarding Queue",
  "status": "paused",
  "updated_at": "2023-07-15T15:50:45Z"
}
```

#### `POST /queues/{queue_id}/resume`

Resume a paused queue.

**Response:**
```json
{
  "queue_id": "123e4567-e89b-12d3-a456-426614174019",
  "name": "Customer Onboarding Queue",
  "status": "active",
  "updated_at": "2023-07-15T15:55:45Z"
}
```

#### `GET /queues/{queue_id}/items`

Get queue items.

**Query Parameters:**
- `status` (optional): Filter by item status
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum records to return (default: 100)

**Response:**
```json
[
  {
    "item_id": "123e4567-e89b-12d3-a456-426614174022",
    "queue_id": "123e4567-e89b-12d3-a456-426614174019",
    "status": "new",
    "priority": 2,
    "reference_id": "CUST-1234",
    "specific_data": {
      "customer_name": "Acme Corp",
      "customer_email": "contact@acmecorp.com",
      "plan_type": "enterprise"
    },
    "created_at": "2023-07-15T14:30:45Z"
  }
]
```

#### `POST /queues/{queue_id}/items`

Add an item to a queue.

**Request:**
```json
{
  "priority": 3,
  "reference_id": "CUST-1235",
  "specific_data": {
    "customer_name": "Globex Corporation",
    "customer_email": "info@globex.com",
    "plan_type": "professional"
  }
}
```

**Response:**
```json
{
  "item_id": "123e4567-e89b-12d3-a456-426614174023",
  "queue_id": "123e4567-e89b-12d3-a456-426614174019",
  "status": "new",
  "priority": 3,
  "reference_id": "CUST-1235",
  "specific_data": {
    "customer_name": "Globex Corporation",
    "customer_email": "info@globex.com",
    "plan_type": "professional"
  },
  "created_at": "2023-07-15T16:00:45Z"
}
```

#### `POST /queues/{queue_id}/items/bulk`

Add multiple items to a queue.

**Request:**
```json
{
  "items": [
    {
      "priority": 2,
      "reference_id": "INV-1001",
      "specific_data": {
        "invoice_number": "INV-1001",
        "amount": 1250.75,
        "customer_id": "CUST-1234"
      }
    },
    {
      "priority": 1,
      "reference_id": "INV-1002",
      "specific_data": {
        "invoice_number": "INV-1002",
        "amount": 2345.50,
        "customer_id": "CUST-1235"
      }
    }
  ]
}
```

**Response:**
```json
{
  "added_count": 2,
  "failed_count": 0,
  "items": [
    {
      "item_id": "123e4567-e89b-12d3-a456-426614174024",
      "reference_id": "INV-1001",
      "status": "new"
    },
    {
      "item_id": "123e4567-e89b-12d3-a456-426614174025",
      "reference_id": "INV-1002",
      "status": "new"
    }
  ]
}
```

#### `GET /queues/{queue_id}/items/{item_id}`

Get queue item details.

**Response:**
```json
{
  "item_id": "123e4567-e89b-12d3-a456-426614174022",
  "queue_id": "123e4567-e89b-12d3-a456-426614174019",
  "status": "processing",
  "priority": 2,
  "reference_id": "CUST-1234",
  "specific_data": {
    "customer_name": "Acme Corp",
    "customer_email": "contact@acmecorp.com",
    "plan_type": "enterprise"
  },
  "processing_attempts": 1,
  "last_processing_time": "2023-07-15T16:05:45Z",
  "execution_id": "123e4567-e89b-12d3-a456-426614174026",
  "created_at": "2023-07-15T14:30:45Z",
  "updated_at": "2023-07-15T16:05:45Z"
}
```

#### `PUT /queues/{queue_id}/items/{item_id}`

Update a queue item.

**Request:**
```json
{
  "priority": 5,
  "specific_data": {
    "customer_name": "Acme Corporation",
    "customer_email": "contact@acmecorp.com",
    "plan_type": "enterprise",
    "additional_notes": "VIP customer"
  }
}
```

**Response:**
```json
{
  "item_id": "123e4567-e89b-12d3-a456-426614174022",
  "priority": 5,
  "specific_data": {
    "customer_name": "Acme Corporation",
    "customer_email": "contact@acmecorp.com",
    "plan_type": "enterprise",
    "additional_notes": "VIP customer"
  },
  "updated_at": "2023-07-15T16:10:45Z"
}
```

#### `DELETE /queues/{queue_id}/items/{item_id}`

Delete a queue item.

**Response Status Code:** 204 No Content

## Asset Management

### Endpoints

#### `GET /asset-types`

Get list of asset types.

**Response:**
```json
[
  {
    "type_id": "123e4567-e89b-12d3-a456-426614174027",
    "name": "credential",
    "description": "Username and password credential",
    "encryption_required": true,
    "schema": {
      "type": "object",
      "properties": {
        "username": {
          "type": "string"
        },
        "password": {
          "type": "string"
        },
        "domain": {
          "type": "string"
        }
      },
      "required": ["username", "password"]
    }
  },
  {
    "type_id": "123e4567-e89b-12d3-a456-426614174028",
    "name": "api_key",
    "description": "API key credential",
    "encryption_required": true,
    "schema": {
      "type": "object",
      "properties": {
        "api_key": {
          "type": "string"
        },
        "api_secret": {
          "type": "string"
        }
      },
      "required": ["api_key"]
    }
  }
]
```

#### `GET /asset-folders`

Get list of asset folders.

**Response:**
```json
[
  {
    "folder_id": "123e4567-e89b-12d3-a456-426614174029",
    "name": "Finance",
    "description": "Finance system credentials",
    "parent_folder_id": null,
    "created_at": "2023-06-15T09:30:45Z"
  },
  {
    "folder_id": "123e4567-e89b-12d3-a456-426614174030",
    "name": "HR",
    "description": "HR system credentials",
    "parent_folder_id": null,
    "created_at": "2023-06-15T09:35:45Z"
  }
]
```

#### `POST /asset-folders`

Create a new asset folder.

**Request:**
```json
{
  "name": "API Keys",
  "description": "External API credentials",
  "parent_folder_id": null
}
```

**Response:**
```json
{
  "folder_id": "123e4567-e89b-12d3-a456-426614174031",
  "name": "API Keys",
  "description": "External API credentials",
  "parent_folder_id": null,
  "created_at": "2023-07-15T16:15:45Z"
}
```

#### `GET /assets`

Get list of assets.

**Query Parameters:**
- `folder_id` (optional): Filter by folder ID
- `type_id` (optional): Filter by asset type
- `search` (optional): Search term
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum records to return (default: 100)

**Response:**
```json
[
  {
    "asset_id": "123e4567-e89b-12d3-a456-426614174032",
    "name": "Finance System Login",
    "description": "Credentials for finance system",
    "folder_id": "123e4567-e89b-12d3-a456-426614174029",
    "folder": {
      "name": "Finance"
    },
    "type_id": "123e4567-e89b-12d3-a456-426614174027",
    "type": {
      "name": "credential"
    },
    "is_shared": false,
    "created_at": "2023-06-15T10:30:45Z",
    "updated_at": "2023-07-10T08:15:30Z"
  }
]
```

#### `POST /assets`

Create a new asset.

**Request:**
```json
{
  "name": "CRM API Key",
  "description": "API key for CRM integration",
  "folder_id": "123e4567-e89b-12d3-a456-426614174031",
  "type_id": "123e4567-e89b-12d3-a456-426614174028",
  "value_encrypted": {
    "api_key": "API_KEY_VALUE",
    "api_secret": "API_SECRET_VALUE"
  },
  "value_json": {
    "api_url": "https://api.example.com/v1",
    "api_version": "1.0"
  },
  "is_shared": false
}
```

**Response:**
```json
{
  "asset_id": "123e4567-e89b-12d3-a456-426614174033",
  "name": "CRM API Key",
  "description": "API key for CRM integration",
  "folder_id": "123e4567-e89b-12d3-a456-426614174031",
  "folder": {
    "name": "API Keys"
  },
  "type_id": "123e4567-e89b-12d3-a456-426614174028",
  "type": {
    "name": "api_key"
  },
  "value_json": {
    "api_url": "https://api.example.com/v1",
    "api_version": "1.0"
  },
  "is_shared": false,
  "created_at": "2023-07-15T16:20:45Z"
}
```

#### `GET /assets/{asset_id}`

Get asset details.

**Response:**
```json
{
  "asset_id": "123e4567-e89b-12d3-a456-426614174032",
  "name": "Finance System Login",
  "description": "Credentials for finance system",
  "folder_id": "123e4567-e89b-12d3-a456-426614174029",
  "folder": {
    "name": "Finance"
  },
  "type_id": "123e4567-e89b-12d3-a456-426614174027",
  "type": {
    "name": "credential"
  },
  "value_json": {
    "domain": "finance.example.com"
  },
  "is_shared": false,
  "created_at": "2023-06-15T10:30:45Z",
  "updated_at": "2023-07-10T08:15:30Z",
  "created_by": {
    "user_id": "123e4567-e89b-12d3-a456-426614174034",
    "full_name": "John Doe"
  },
  "updated_by": {
    "user_id": "123e4567-e89b-12d3-a456-426614174034",
    "full_name": "John Doe"
  }
}
```

#### `GET /assets/{asset_id}/value`

Get asset encrypted value. This endpoint requires special permissions.

**Response:**
```json
{
  "asset_id": "123e4567-e89b-12d3-a456-426614174032",
  "name": "Finance System Login",
  "value_encrypted": {
    "username": "finance_admin",
    "password": "secure_password_123"
  },
  "value_json": {
    "domain": "finance.example.com"
  }
}
```

#### `PUT /assets/{asset_id}`

Update an asset.

**Request:**
```json
{
  "description": "Updated credentials for finance system",
  "value_encrypted": {
    "username": "finance_admin",
    "password": "new_secure_password_456"
  }
}
```

**Response:**
```json
{
  "asset_id": "123e4567-e89b-12d3-a456-426614174032",
  "name": "Finance System Login",
  "description": "Updated credentials for finance system",
  "updated_at": "2023-07-15T16:25:45Z"
}
```

#### `DELETE /assets/{asset_id}`

Delete an asset.

**Response Status Code:** 204 No Content

## Notification Management

### Endpoints

#### `GET /notification-channels`

Get list of notification channels.

**Response:**
```json
[
  {
    "channel_id": "123e4567-e89b-12d3-a456-426614174035",
    "name": "Admin Email",
    "type": "email",
    "configuration": {
      "recipients": ["admin@example.com", "manager@example.com"],
      "cc": ["notifications@example.com"],
      "from_name": "Automation System"
    },
    "is_enabled": true,
    "created_at": "2023-06-15T10:30:45Z"
  },
  {
    "channel_id": "123e4567-e89b-12d3-a456-426614174036",
    "name": "DevOps Slack",
    "type": "slack",
    "configuration": {
      "webhook_url": "https://hooks.slack.com/services/XXX/YYY/ZZZ",
      "channel": "#devops-alerts"
    },
    "is_enabled": true,
    "created_at": "2023-06-15T10:35:45Z"
  }
]
```

#### `POST /notification-channels`

Create a new notification channel.

**Request:**
```json
{
  "name": "Technical Team Email",
  "type": "email",
  "configuration": {
    "recipients": ["tech@example.com", "support@example.com"],
    "from_name": "Automation System"
  }
}
```

**Response:**
```json
{
  "channel_id": "123e4567-e89b-12d3-a456-426614174037",
  "name": "Technical Team Email",
  "type": "email",
  "configuration": {
    "recipients": ["tech@example.com", "support@example.com"],
    "from_name": "Automation System"
  },
  "is_enabled": true,
  "created_at": "2023-07-15T16:30:45Z"
}
```

#### `GET /notification-rules`

Get list of notification rules.

**Response:**
```json
[
  {
    "rule_id": "123e4567-e89b-12d3-a456-426614174038",
    "name": "Job Failure Alert",
    "description": "Alert on job failures",
    "type_id": "123e4567-e89b-12d3-a456-426614174039",
    "type": {
      "name": "job_failure"
    },
    "condition": {
      "job_ids": ["*"],
      "retry_count": ">= 2"
    },
    "is_enabled": true,
    "channels": [
      {
        "channel_id": "123e4567-e89b-12d3-a456-426614174035",
        "name": "Admin Email"
      },
      {
        "channel_id": "123e4567-e89b-12d3-a456-426614174036",
        "name": "DevOps Slack"
      }
    ],
    "created_at": "2023-06-15T11:30:45Z"
  }
]
```

#### `POST /notification-rules`

Create a new notification rule.

**Request:**
```json
{
  "name": "Agent Offline Alert",
  "description": "Alert when an agent goes offline",
  "type_id": "123e4567-e89b-12d3-a456-426614174040",
  "condition": {
    "agent_ids": ["*"],
    "status_change": "online -> offline",
    "duration_minutes": "> 5"
  },
  "is_enabled": true,
  "channels": ["123e4567-e89b-12d3-a456-426614174035", "123e4567-e89b-12d3-a456-426614174036"]
}
```

**Response:**
```json
{
  "rule_id": "123e4567-e89b-12d3-a456-426614174041",
  "name": "Agent Offline Alert",
  "description": "Alert when an agent goes offline",
  "type_id": "123e4567-e89b-12d3-a456-426614174040",
  "condition": {
    "agent_ids": ["*"],
    "status_change": "online -> offline",
    "duration_minutes": "> 5"
  },
  "is_enabled": true,
  "channels": [
    {
      "channel_id": "123e4567-e89b-12d3-a456-426614174035",
      "name": "Admin Email"
    },
    {
      "channel_id": "123e4567-e89b-12d3-a456-426614174036",
      "name": "DevOps Slack"
    }
  ],
  "created_at": "2023-07-15T16:35:45Z"
}
```

#### `GET /notifications`

Get list of notifications.

**Query Parameters:**
- `is_read` (optional): Filter by read status
- `severity` (optional): Filter by severity
- `from_date` (optional): Filter by start date
- `to_date` (optional): Filter by end date
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum records to return (default: 100)

**Response:**
```json
[
  {
    "notification_id": "123e4567-e89b-12d3-a456-426614174042",
    "title": "Job Failed: Daily Invoice Processing",
    "message": "The job 'Daily Invoice Processing' has failed with error: File not found.",
    "severity": "error",
    "entity_type": "job_execution",
    "entity_id": "123e4567-e89b-12d3-a456-426614174043",
    "is_read": false,
    "created_at": "2023-07-15T14:05:45Z"
  }
]
```

#### `GET /notifications/{notification_id}`

Get notification details.

**Response:**
```json
{
  "notification_id": "123e4567-e89b-12d3-a456-426614174042",
  "title": "Job Failed: Daily Invoice Processing",
  "message": "The job 'Daily Invoice Processing' has failed with error: File not found.",
  "severity": "error",
  "entity_type": "job_execution",
  "entity_id": "123e4567-e89b-12d3-a456-426614174043",
  "metadata": {
    "job_id": "123e4567-e89b-12d3-a456-426614174011",
    "job_name": "Daily Invoice Processing",
    "agent_id": "123e4567-e89b-12d3-a456-426614174002",
    "agent_name": "Production Agent 1",
    "error_details": {
      "path": "/invoices/new",
      "error_code": "ENOENT"
    }
  },
  "is_read": false,
  "created_at": "2023-07-15T14:05:45Z"
}
```

#### `POST /notifications/{notification_id}/mark-read`

Mark a notification as read.

**Response:**
```json
{
  "notification_id": "123e4567-e89b-12d3-a456-426614174042",
  "is_read": true,
  "read_at": "2023-07-15T16:40:45Z",
  "read_by": {
    "user_id": "123e4567-e89b-12d3-a456-426614174034",
    "full_name": "John Doe"
  }
}
```

#### `POST /notifications/mark-all-read`

Mark all notifications as read.

**Response:**
```json
{
  "marked_count": 5,
  "read_at": "2023-07-15T16:45:45Z"
}
```

## Tenant Management

### Endpoints

#### `GET /tenants`

Get list of tenants (for superusers only).

**Response:**
```json
[
  {
    "tenant_id": "123e4567-e89b-12d3-a456-426614174001",
    "name": "Acme Corporation",
    "status": "active",
    "subscription_tier": "professional",
    "max_agents": 50,
    "max_concurrent_jobs": 100,
    "created_at": "2023-05-15T09:30:45Z"
  }
]
```

#### `GET /tenants/current`

Get current tenant details.

**Response:**
```json
{
  "tenant_id": "123e4567-e89b-12d3-a456-426614174001",
  "name": "Acme Corporation",
  "status": "active",
  "subscription_tier": "professional",
  "max_agents": 50,
  "max_concurrent_jobs": 100,
  "created_at": "2023-05-15T09:30:45Z",
  "updated_at": "2023-07-10T08:15:30Z",
  "settings": {
    "custom_branding": {
      "logo_url": "https://example.com/acme_logo.png",
      "primary_color": "#336699"
    },
    "default_timezone": "America/New_York"
  },
  "subscription": {
    "tier_name": "professional",
    "tier_display_name": "Professional",
    "status": "active",
    "billing_cycle": "monthly",
    "price": 199.99,
    "next_billing_date": "2023-08-15T00:00:00Z",
    "features": {
      "api_access": true,
      "schedules": true,
      "queues": true,
      "analytics": true,
      "custom_branding": true,
      "sla_support": false,
      "audit_logs": true
    }
  },
  "usage": {
    "agents": {
      "count": 15,
      "limit": 50,
      "usage_percentage": 30
    },
    "jobs": {
      "active_count": 25,
      "running_count": 8,
      "concurrent_limit": 100,
      "usage_percentage": 8
    }
  }
}
```

#### `PUT /tenants/current`

Update current tenant settings.

**Request:**
```json
{
  "settings": {
    "custom_branding": {
      "logo_url": "https://example.com/acme_new_logo.png",
      "primary_color": "#003366"
    },
    "default_timezone": "America/Chicago"
  }
}
```

**Response:**
```json
{
  "tenant_id": "123e4567-e89b-12d3-a456-426614174001",
  "name": "Acme Corporation",
  "settings": {
    "custom_branding": {
      "logo_url": "https://example.com/acme_new_logo.png",
      "primary_color": "#003366"
    },
    "default_timezone": "America/Chicago"
  },
  "updated_at": "2023-07-15T16:50:45Z"
}
```

## User Management

### Endpoints

#### `GET /users`

Get list of users.

**Query Parameters:**
- `status` (optional): Filter by user status
- `search` (optional): Search term
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum records to return (default: 100)

**Response:**
```json
[
  {
    "user_id": "123e4567-e89b-12d3-a456-426614174034",
    "email": "john.doe@example.com",
    "full_name": "John Doe",
    "status": "active",
    "roles": ["admin"],
    "created_at": "2023-05-15T10:30:45Z",
    "last_login": "2023-07-15T08:30:45Z"
  }
]
```

#### `POST /users`

Create a new user.

**Request:**
```json
{
  "email": "jane.smith@example.com",
  "full_name": "Jane Smith",
  "password": "SecurePassword123!",
  "roles": ["user"]
}
```

**Response:**
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174044",
  "email": "jane.smith@example.com",
  "full_name": "Jane Smith",
  "status": "active",
  "roles": ["user"],
  "created_at": "2023-07-15T16:55:45Z"
}
```

#### `GET /users/{user_id}`

Get user details.

**Response:**
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174034",
  "email": "john.doe@example.com",
  "full_name": "John Doe",
  "status": "active",
  "roles": ["admin"],
  "permissions": ["job:read", "job:write", "job:execute", "agent:read", "agent:write"],
  "created_at": "2023-05-15T10:30:45Z",
  "updated_at": "2023-07-10T08:15:30Z",
  "last_login": "2023-07-15T08:30:45Z"
}
```

#### `PUT /users/{user_id}`

Update a user.

**Request:**
```json
{
  "full_name": "John M. Doe",
  "status": "active",
  "roles": ["admin", "user"]
}
```

**Response:**
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174034",
  "email": "john.doe@example.com",
  "full_name": "John M. Doe",
  "status": "active",
  "roles": ["admin", "user"],
  "updated_at": "2023-07-15T17:00:45Z"
}
```

#### `PUT /users/{user_id}/password`

Update a user's password.

**Request:**
```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewSecurePassword456!"
}
```

**Response:**
```json
{
  "message": "Password updated successfully",
  "updated_at": "2023-07-15T17:05:45Z"
}
```

#### `DELETE /users/{user_id}`

Delete a user.

**Response Status Code:** 204 No Content

## Role Management

### Endpoints

#### `GET /roles`

Get list of roles.

**Response:**
```json
[
  {
    "role_id": "123e4567-e89b-12d3-a456-426614174045",
    "name": "admin",
    "description": "Administrator with full access",
    "created_at": "2023-05-15T10:00:45Z"
  },
  {
    "role_id": "123e4567-e89b-12d3-a456-426614174046",
    "name": "user",
    "description": "Standard user with limited access",
    "created_at": "2023-05-15T10:00:45Z"
  }
]
```

#### `POST /roles`

Create a new role.

**Request:**
```json
{
  "name": "developer",
  "description": "Developer with specific permissions",
  "permissions": ["job:read", "job:write", "job:execute", "package:read", "package:write"]
}
```

**Response:**
```json
{
  "role_id": "123e4567-e89b-12d3-a456-426614174047",
  "name": "developer",
  "description": "Developer with specific permissions",
  "permissions": ["job:read", "job:write", "job:execute", "package:read", "package:write"],
  "created_at": "2023-07-15T17:10:45Z"
}
```

#### `GET /roles/{role_id}`

Get role details.

**Response:**
```json
{
  "role_id": "123e4567-e89b-12d3-a456-426614174045",
  "name": "admin",
  "description": "Administrator with full access",
  "permissions": [
    "job:read",
    "job:write",
    "job:execute",
    "job:delete",
    "agent:read",
    "agent:write",
    "agent:delete",
    "package:read",
    "package:write",
    "package:delete",
    "schedule:read",
    "schedule:write",
    "schedule:delete",
    "queue:read",
    "queue:write",
    "queue:delete",
    "asset:read",
    "asset:write",
    "asset:delete",
    "user:read",
    "user:write",
    "user:delete",
    "role:read",
    "role:write",
    "role:delete",
    "tenant:read",
    "tenant:write"
  ],
  "created_at": "2023-05-15T10:00:45Z",
  "updated_at": "2023-05-15T10:00:45Z"
}
```

#### `PUT /roles/{role_id}`

Update a role.

**Request:**
```json
{
  "description": "Administrator with full system access",
  "permissions": ["job:read", "job:write", "job:execute", "job:delete", "agent:read", "agent:write"]
}
```

**Response:**
```json
{
  "role_id": "123e4567-e89b-12d3-a456-426614174045",
  "name": "admin",
  "description": "Administrator with full system access",
  "permissions": ["job:read", "job:write", "job:execute", "job:delete", "agent:read", "agent:write"],
  "updated_at": "2023-07-15T17:15:45Z"
}
```

#### `DELETE /roles/{role_id}`

Delete a role.

**Response Status Code:** 204 No Content

## Permission Management

### Endpoints

#### `GET /permissions`

Get list of all available permissions.

**Response:**
```json
[
  {
    "permission_id": "123e4567-e89b-12d3-a456-426614174048",
    "name": "job:read",
    "description": "View jobs",
    "resource": "job",
    "action": "read"
  },
  {
    "permission_id": "123e4567-e89b-12d3-a456-426614174049",
    "name": "job:write",
    "description": "Create/modify jobs",
    "resource": "job",
    "action": "write"
  },
  {
    "permission_id": "123e4567-e89b-12d3-a456-426614174050",
    "name": "job:execute",
    "description": "Execute jobs",
    "resource": "job",
    "action": "execute"
  }
]
```

## Audit Logs

### Endpoints

#### `GET /audit-logs`

Get audit logs.

**Query Parameters:**
- `action` (optional): Filter by action
- `entity_type` (optional): Filter by entity type
- `entity_id` (optional): Filter by entity ID
- `user_id` (optional): Filter by user ID
- `from_date` (optional): Filter by start date
- `to_date` (optional): Filter by end date
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum records to return (default: 100)

**Response:**
```json
[
  {
    "log_id": "123e4567-e89b-12d3-a456-426614174051",
    "tenant_id": "123e4567-e89b-12d3-a456-426614174001",
    "user_id": "123e4567-e89b-12d3-a456-426614174034",
    "user": {
      "email": "john.doe@example.com",
      "full_name": "John Doe"
    },
    "action": "create_job",
    "entity_type": "job",
    "entity_id": "123e4567-e89b-12d3-a456-426614174011",
    "details": {
      "name": "Daily Invoice Processing",
      "package_id": "123e4567-e89b-12d3-a456-426614174008"
    },
    "ip_address": "192.168.1.100",
    "created_at": "2023-06-15T09:30:45Z"
  }
]
```

## Analytics

### Endpoints

#### `GET /analytics/dashboard`

Get dashboard analytics.

**Response:**
```json
{
  "jobs": {
    "total_count": 25,
    "active_count": 20,
    "paused_count": 5,
    "execution_stats": {
      "total_executions": 1250,
      "success_count": 1150,
      "failed_count": 100,
      "success_rate": 92
    },
    "execution_trend": [
      {"date": "2023-07-09", "successful": 145, "failed": 12},
      {"date": "2023-07-10", "successful": 156, "failed": 8},
      {"date": "2023-07-11", "successful": 162, "failed": 10},
      {"date": "2023-07-12", "successful": 158, "failed": 15},
      {"date": "2023-07-13", "successful": 165, "failed": 5},
      {"date": "2023-07-14", "successful": 170, "failed": 3},
      {"date": "2023-07-15", "successful": 150, "failed": 8}
    ]
  },
  "agents": {
    "total_count": 15,
    "online_count": 12,
    "offline_count": 3,
    "utilization": 65,
    "status_trend": [
      {"date": "2023-07-09", "online": 13, "offline": 2},
      {"date": "2023-07-10", "online": 14, "offline": 1},
      {"date": "2023-07-11", "online": 15, "offline": 0},
      {"date": "2023-07-12", "online": 14, "offline": 1},
      {"date": "2023-07-13", "online": 13, "offline": 2},
      {"date": "2023-07-14", "online": 14, "offline": 1},
      {"date": "2023-07-15", "online": 12, "offline": 3}
    ]
  },
  "queues": {
    "total_count": 8,
    "active_count": 7,
    "paused_count": 1,
    "item_stats": {
      "total_items": 350,
      "new_items": 125,
      "processing_items": 75,
      "completed_items": 125,
      "failed_items": 25
    }
  },
  "top_jobs": [
    {
      "job_id": "123e4567-e89b-12d3-a456-426614174011",
      "name": "Daily Invoice Processing",
      "execution_count": 150,
      "success_rate": 95,
      "avg_duration_seconds": 185
    },
    {
      "job_id": "123e4567-e89b-12d3-a456-426614174012",
      "name": "Weekly Sales Report",
      "execution_count": 25,
      "success_rate": 96,
      "avg_duration_seconds": 450
    }
  ],
  "recent_failures": [
    {
      "execution_id": "123e4567-e89b-12d3-a456-426614174043",
      "job_name": "Daily Invoice Processing",
      "agent_name": "Production Agent 1",
      "error_message": "File not found",
      "failed_at": "2023-07-15T14:05:45Z"
    }
  ]
}
```

#### `GET /analytics/jobs`

Get job analytics.

**Query Parameters:**
- `job_id` (optional): Filter by job ID
- `from_date` (optional): Filter by start date
- `to_date` (optional): Filter by end date

**Response:**
```json
{
  "summary": {
    "total_executions": 150,
    "successful_executions": 142,
    "failed_executions": 8,
    "success_rate": 94.67,
    "avg_duration_seconds": 185,
    "min_duration_seconds": 120,
    "max_duration_seconds": 350
  },
  "trend": [
    {"date": "2023-07-09", "successful": 20, "failed": 1, "avg_duration": 180},
    {"date": "2023-07-10", "successful": 21, "failed": 0, "avg_duration": 175},
    {"date": "2023-07-11", "successful": 20, "failed": 2, "avg_duration": 190},
    {"date": "2023-07-12", "successful": 22, "failed": 0, "avg_duration": 185},
    {"date": "2023-07-13", "successful": 20, "failed": 1, "avg_duration": 182},
    {"date": "2023-07-14", "successful": 21, "failed": 0, "avg_duration": 180},
    {"date": "2023-07-15", "successful": 18, "failed": 4, "avg_duration": 195}
  ],
  "by_agent": [
    {
      "agent_id": "123e4567-e89b-12d3-a456-426614174002",
      "agent_name": "Production Agent 1",
      "total_executions": 60,
      "successful_executions": 56,
      "failed_executions": 4,
      "success_rate": 93.33,
      "avg_duration_seconds": 190
    },
    {
      "agent_id": "123e4567-e89b-12d3-a456-426614174006",
      "agent_name": "Production Agent 3",
      "total_executions": 90,
      "successful_executions": 86,
      "failed_executions": 4,
      "success_rate": 95.56,
      "avg_duration_seconds": 182
    }
  ],
  "error_categories": [
    {
      "category": "File Access",
      "count": 5,
      "percentage": 62.5
    },
    {
      "category": "Network",
      "count": 2,
      "percentage": 25
    },
    {
      "category": "Timeout",
      "count": 1,
      "percentage": 12.5
    }
  ]
}
```

#### `GET /analytics/agents`

Get agent analytics.

**Query Parameters:**
- `agent_id` (optional): Filter by agent ID
- `from_date` (optional): Filter by start date
- `to_date` (optional): Filter by end date

**Response:**
```json
{
  "summary": {
    "total_agents": 15,
    "online_agents": 12,
    "offline_agents": 3,
    "busy_agents": 6,
    "idle_agents": 6,
    "avg_uptime_percentage": 95.2
  },
  "trend": [
    {"date": "2023-07-09", "online": 13, "offline": 2, "busy": 7, "idle": 6},
    {"date": "2023-07-10", "online": 14, "offline": 1, "busy": 8, "idle": 6},
    {"date": "2023-07-11", "online": 15, "offline": 0, "busy": 9, "idle": 6},
    {"date": "2023-07-12", "online": 14, "offline": 1, "busy": 7, "idle": 7},
    {"date": "2023-07-13", "online": 13, "offline": 2, "busy": 8, "idle": 5},
    {"date": "2023-07-14", "online": 14, "offline": 1, "busy": 8, "idle": 6},
    {"date": "2023-07-15", "online": 12, "offline": 3, "busy": 6, "idle": 6}
  ],
  "by_agent": [
    {
      "agent_id": "123e4567-e89b-12d3-a456-426614174002",
      "agent_name": "Production Agent 1",
      "status": "online",
      "uptime_percentage": 98.5,
      "jobs_executed": 60,
      "success_rate": 93.33,
      "avg_cpu_usage": 45.2,
      "avg_memory_usage": 62.8
    },
    {
      "agent_id": "123e4567-e89b-12d3-a456-426614174006",
      "agent_name": "Production Agent 3",
      "status": "online",
      "uptime_percentage": 99.2,
      "jobs_executed": 90,
      "success_rate": 95.56,
      "avg_cpu_usage": 52.3,
      "avg_memory_usage": 68.5
    }
  ]
}
```

## Health Check

### Endpoints

#### `GET /health`

Get system health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "api": {
      "status": "healthy",
      "version": "1.0.0"
    },
    "database": {
      "status": "healthy",
      "response_time_ms": 15
    },
    "message_broker": {
      "status": "healthy",
      "response_time_ms": 8
    },
    "object_storage": {
      "status": "healthy",
      "response_time_ms": 25
    }
  },
  "uptime_seconds": 1234567,
  "timestamp": "2023-07-15T17:30:45Z"
}
```

## Error Handling

All error responses follow a consistent format:

```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2023-07-15T17:35:45Z",
  "path": "/api/v1/jobs/123e4567-e89b-12d3-a456-426614174011",
  "status_code": 404,
  "validation_errors": [
    {
      "field": "name",
      "message": "Field is required"
    }
  ]
}
```

Common error codes:

- `UNAUTHORIZED`: Authentication failed
- `FORBIDDEN`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `VALIDATION_ERROR`: Invalid input data
- `CONFLICT`: Resource already exists
- `INTERNAL_ERROR`: Server error
- `SERVICE_UNAVAILABLE`: Service not available

## API Rate Limiting

The API implements rate limiting to prevent abuse. The current limits are:

- 100 requests per minute per user for standard operations
- 300 requests per minute per user for read-only operations
- 10 requests per minute per user for resource-intensive operations

Rate limit headers are included in all responses:

- `X-RateLimit-Limit`: The maximum number of requests allowed per minute
- `X-RateLimit-Remaining`: The number of requests remaining in the current window
- `X-RateLimit-Reset`: The time at which the current rate limit window resets in UTC epoch seconds

When a rate limit is exceeded, a 429 Too Many Requests response is returned.:write", "job# API Specification

## Overview

The Python Automation Orchestrator API is designed as a RESTful API that follows standard REST conventions. The API is versioned to ensure backward compatibility as the system evolves.

Base URL: `https://{hostname}/api/v1`

## Authentication

The API uses OAuth2 with JWT (JSON Web Tokens) for authentication.

### Authentication Endpoints

#### `POST /auth/login`

Authenticate and get access token.

**Request:**
```json
{
  "username": "user@example.com",
  "password": "password123",
  "grant_type": "password"
}
```

## Queue Management

### Endpoints

#### `GET /queues`

Get list of queues.

**Query Parameters:**
- `status` (optional): Filter by queue status
- `search` (optional): Search term
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum records to return (default: 100)

**Response:**
```json
[
  {
    "queue_id": "123

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### `POST /auth/refresh`

Refresh access token.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "grant_type": "refresh_token"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### `GET /auth/me`

Get current user information.

**Response:**
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "tenant_id": "123e4567-e89b-12d3-a456-426614174001",
  "roles": ["admin", "user"],
  "permissions": ["job:read", "job:write", "job:execute"]
}
```

## Agent Management

### Endpoints

#### `GET /agents`

Get list of agents.

**Query Parameters:**
- `status` (optional): Filter by agent status
- `search` (optional): Search term
- `tags` (optional): Filter by tags
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum records to return (default: 100)

**Response:**
```json
[
  {
    "agent_id": "123e4567-e89b-12d3-a456-426614174002",
    "name": "Production Agent 1",
    "machine_id": "PROD-MACHINE-001",
    "ip_address": "192.168.1.100",
    "status": "online",
    "last_heartbeat": "2023-07-15T14:30:45Z",
    "version": "1.2.3",
    "capabilities": {
      "python_version": "3.9.5",
      "os": "Windows",
      "memory_mb": 8192,
      "cpu_cores": 4
    },
    "tags": ["production", "finance"],
    "auto_login_enabled": true,
    "service_account": {
      "account_id": "123e4567-e89b-12d3-a456-426614174003",
      "username": "robot_account",
      "display_name": "Finance Robot"
    }
  }
]
```

#### `POST /agents`

Create a new agent.

**Request:**
```json
{
  "name": "Production Agent 2",
  "machine_id": "PROD-MACHINE-002",
  "tags": ["production", "hr"]
}
```

**Response:**
```json
{
  "agent_id": "123e4567-e89b-12d3-a456-426614174004",
  "name": "Production Agent 2",
  "machine_id": "PROD-MACHINE-002",
  "status": "offline",
  "tags": ["production", "hr"],
  "api_key": "YOUR_API_KEY"
}
```

#### `GET /agents/{agent_id}`

Get agent details.

**Response:**
```json
{
  "agent_id": "123e4567-e89b-12d3-a456-426614174002",
  "name": "Production Agent 1",
  "machine_id": "PROD-MACHINE-001",
  "ip_address": "192.168.1.100",
  "status": "online",
  "last_heartbeat": "2023-07-15T14:30:45Z",
  "version": "1.2.3",
  "capabilities": {
    "python_version": "3.9.5",
    "os": "Windows",
    "memory_mb": 8192,
    "cpu_cores": 4
  },
  "tags": ["production", "finance"],
  "auto_login_enabled": true,
  "service_account": {
    "account_id": "123e4567-e89b-12d3-a456-426614174003",
    "username": "robot_account",
    "display_name": "Finance Robot"
  }
}
```

#### `PUT /agents/{agent_id}`

Update an agent.

**Request:**
```json
{
  "name": "Production Agent 1 - Finance",
  "tags": ["production", "finance", "accounting"]
}
```

**Response:**
```json
{
  "agent_id": "123e4567-e89b-12d3-a456-426614174002",
  "name": "Production Agent 1 - Finance",
  "machine_id": "PROD-MACHINE-001",
  "tags": ["production", "finance", "accounting"],
  "status": "online",
  "last_heartbeat": "2023-07-15T14:30:45Z"
}
```

#### `DELETE /agents/{agent_id}`

Delete an agent.

**Response Status Code:** 204 No Content

#### `GET /agents/{agent_id}/logs`

Get agent logs.

**Query Parameters:**
- `log_level` (optional): Filter by log level
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum records to return (default: 100)

**Response:**
```json
[
  {
    "log_id": "123e4567-e89b-12d3-a456-426614174005",
    "agent_id": "123e4567-e89b-12d3-a456-426614174002",
    "log_level": "info",
    "message": "Agent started successfully",
    "metadata": {
      "ip_address": "192.168.1.100",
      "version": "1.2.3"
    },
    "created_at": "2023-07-15T14:29:45Z"
  }
]
```

#### `POST /agents/{agent_id}/command`

Send a command to an agent.

**Request:**
```json
{
  "command_type": "start",
  "parameters": {
    "force": false
  }
}
```

**Response:**
```json
{
  "agent_id": "123e4567-e89b-12d3-a456-426614174002",
  "name": "Production Agent 1",
  "status": "online",
  "last_heartbeat": "2023-07-15T14:30:45Z"
}
```

#### `POST /agents/{agent_id}/auto-login/enable`

Enable auto-login for an agent.

**Query Parameters:**
- `service_account_id`: Service account ID to use for auto-login
- `session_type` (optional): Session type (default: windows)

**Response:**
```json
{
  "agent_id": "123e4567-e89b-12d3-a456-426614174002",
  "name": "Production Agent 1",
  "auto_login_enabled": true,
  "service_account_id": "123e4567-e89b-12d3-a456-426614174003",
  "session_type": "windows"
}
```

#### `POST /agents/{agent_id}/auto-login/disable`

Disable auto-login for an agent.

**Response:**
```json
{
  "agent_id": "123e4567-e89b-12d3-a456-426614174002",
  "name": "Production Agent 1",
  "auto_login_enabled": false
}
```

#### `POST /agents/register`

Register a new agent (used by agents themselves).

**Request:**
```json
{
  "machine_id": "PROD-MACHINE-003",
  "name": "Production Agent 3",
  "ip_address": "192.168.1.102",
  "version": "1.2.3",
  "capabilities": {
    "python_version": "3.9.5",
    "os": "Windows",
    "memory_mb": 8192,
    "cpu_cores": 4
  },
  "tenant_id": "123e4567-e89b-12d3-a456-426614174001"
}
```

**Response:**
```json
{
  "agent_id": "123e4567-e89b-12d3-a456-426614174006",
  "name": "Production Agent 3",
  "machine_id": "PROD-MACHINE-003",
  "status": "online",
  "api_key": "YOUR_API_KEY"
}
```

#### `POST /agents/{agent_id}/heartbeat`

Update agent heartbeat (used by agents themselves).

**Request:**
```json
{
  "status": "online",
  "ip_address": "192.168.1.102",
  "capabilities": {
    "python_version": "3.9.5",
    "os": "Windows",
    "memory_mb": 8192,
    "cpu_cores": 4,
    "cpu_usage": 25.5,
    "memory_usage": 4096
  },
  "tenant_id": "123e4567-e89b-12d3-a456-426614174001"
}
```

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2023-07-15T14:31:45Z",
  "agent_id": "123e4567-e89b-12d3-a456-426614174006"
}
```

## Service Account Management

### Endpoints

#### `GET /service-accounts`

Get list of service accounts.

**Query Parameters:**
- `status` (optional): Filter by account status
- `search` (optional): Search term
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum records to return (default: 100)

**Response:**
```json
[
  {
    "account_id": "123e4567-e89b-12d3-a456-426614174003",
    "username": "robot_account",
    "display_name": "Finance Robot",
    "description": "Service account for finance automations",
    "account_type": "robot",
    "status": "active",
    "created_at": "2023-06-15T10:30:45Z",
    "last_used": "2023-07-15T14:30:45Z"
  }
]
```

#### `POST /service-accounts`

Create a new service account.

**Request:**
```json
{
  "username": "hr_robot",
  "display_name": "HR Robot",
  "description": "Service account for HR automations",
  "account_type": "robot",
  "password": "StrongPassword123!"
}
```

**Response:**
```json
{
  "account_id": "123e4567-e89b-12d3-a456-426614174007",
  "username": "hr_robot",
  "display_name": "HR Robot",
  "description": "Service account for HR automations",
  "account_type": "robot",
  "status": "active",
  "created_at": "2023-07-15T14:35:45Z",
  "password": "StrongPassword123!" // Only returned once
}
```

#### `GET /service-accounts/{account_id}`

Get service account details.

**Response:**
```json
{
  "account_id": "123e4567-e89b-12d3-a456-426614174003",
  "username": "robot_account",
  "display_name": "Finance Robot",
  "description": "Service account for finance automations",
  "account_type": "robot",
  "status": "active",
  "created_at": "2023-06-15T10:30:45Z",
  "last_used": "2023-07-15T14:30:45Z"
}
```

#### `PUT /service-accounts/{account_id}`

Update a service account.

**Request:**
```json
{
  "display_name": "Finance Robot Updated",
  "description": "Updated description for finance automations",
  "password": "NewPassword456!" // Optional, leave blank to keep current password
}
```

**Response:**
```json
{
  "account_id": "123e4567-e89b-12d3-a456-426614174003",
  "username": "robot_account",
  "display_name": "Finance Robot Updated",
  "description": "Updated description for finance automations",
  "account_type": "robot",
  "status": "active",
  "updated_at": "2023-07-15T14:40:45Z"
}
```

#### `DELETE /service-accounts/{account_id}`

Delete a service account.

**Response Status Code:** 204 No Content

## Package Management

### Endpoints

#### `GET /packages`

Get list of packages.

**Query Parameters:**
- `status` (optional): Filter by package status
- `search` (optional): Search term
- `tags` (optional): Filter by tags
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum records to return (default: 100)

**Response:**
```json
{
  "total": 25,
  "items": [
    {
      "package_id": "123e4567-e89b-12d3-a456-426614174008",
      "name": "Invoice Processing",
      "description": "Automated invoice processing package",
      "version": "1.0.0",
      "main_file_path": "main.py",
      "entry_point": "main.py",
      "status": "production",
      "tags": ["finance", "invoices"],
      "created_at": "2023-06-10T10:30:45Z",
      "updated_at": "2023-07-10T08:15:30Z"
    }
  ]
}
```

#### `POST /packages`

Create a new package definition.

**Request:**
```json
{
  "name": "Customer Onboarding",
  "description": "Customer onboarding automation",
  "version": "1.0.0",
  "main_file_path": "main.py",
  "entry_point": "main.py",
  "status": "development",
  "tags": ["customer", "onboarding"]
}
```

**Response:**
```json
{
  "package_id": "123e4567-e89b-12d3-a456-426614174009",
  "name": "Customer Onboarding",
  "description": "Customer onboarding automation",
  "version": "1.0.0",
  "main_file_path": "main.py",
  "entry_point": "main.py",
  "status": "development",
  "tags": ["customer", "onboarding"],
  "storage_path": "tenants/123e4567-e89b-12d3-a456-426614174001/packages/Customer Onboarding/1.0.0",
  "created_at": "2023-07-15T14:45:45Z"
}
```

#### `GET /packages/{package_id}`

Get package details.

**Response:**
```json
{
  "package_id": "123e4567-e89b-12d3-a456-426614174008",
  "name": "Invoice Processing",
  "description": "Automated invoice processing package",
  "version": "1.0.0",
  "main_file_path": "main.py",
  "entry_point": "main.py",
  "status": "production",
  "tags": ["finance", "invoices"],
  "storage_path": "tenants/123e4567-e89b-12d3-a456-426614174001/packages/Invoice Processing/1.0.0",
  "created_at": "2023-06-10T10:30:45Z",
  "updated_at": "2023-07-10T08:15:30Z",
  "dependencies": {
    "pandas": ">=1.3.0",
    "numpy": ">=1.20.0"
  }
}
```

#### `PUT /packages/{package_id}`

Update a package.

**Request:**
```json
{
  "description": "Updated invoice processing package",
  "status": "testing",
  "tags": ["finance", "invoices", "accounting"]
}
```

**Response:**
```json
{
  "package_id": "123e4567-e89b-12d3-a456-426614174008",
  "name": "Invoice Processing",
  "description": "Updated invoice processing package",
  "version": "1.0.0",
  "status": "testing",
  "tags": ["finance", "invoices", "accounting"],
  "updated_at": "2023-07-15T14:50:45Z"
}
```

#### `DELETE /packages/{package_id}`

Delete a package.

**Response Status Code:** 204 No Content

#### `POST /packages/upload`

Upload a package file.

**Form Data:**
- `file`: Package zip file
- `name`: Package name
- `version`: Package version
- `description` (optional): Package description
- `entry_point`: Entry point file
- `overwrite` (optional): Whether to overwrite existing package

**Response:**
```json
{
  "package_id": "123e4567-e89b-12d3-a456-426614174010",
  "name": "Data Export",
  "version": "1.2.0",
  "description": "Data export automation",
  "entry_point": "main.py",
  "md5_hash": "5a73d5d8c8cdc05b5dfa075c8e7a79db",
  "status": "development",
  "created_at": "2023-07-15T14:55:45Z"
}
```

#### `GET /packages/{package_id}/download`

Download a package file.

**Response:** Package zip file with appropriate Content-Type and Content-Disposition headers.

#### `POST /packages/{package_id}/deploy`

Deploy a package to agents.

**Request:**
```json
{
  "target_environment": "production",
  "agent_ids": ["123e4567-e89b-12d3-a456-426614174002", "123e4567-e89b-12d3-a456-426614174006"],
  "deploy_to_all_agents": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Deployed to 2 agents, 0 failed",
  "deployed_count": 2,
  "failed_count": 0
}
```

## Job Management

### Endpoints

#### `GET /jobs`

Get list of jobs.

**Query Parameters:**
- `status` (optional): Filter by job status
- `search` (optional): Search term
- `tags` (optional): Filter by tags
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum records to return (default: 100)

**Response:**
```json
[
  {
    "job_id": "123e4567-e89b-12d3-a456-426614174011",
    "name": "Daily Invoice Processing",
    "description": "Process invoices daily at 8 AM",
    "package_id": "123e4567-e89b-12d3-a456-426614174008",
    "package": {
      "name": "Invoice Processing",
      "version": "1.0.0"
    },
    "parameters": {
      "source_folder": "invoices/incoming",
      "destination_folder": "invoices/processed"
    },
    "status": "active",
    "tags": ["daily", "finance"],
    "created_at": "2023-06-15T09:30:45Z"
  }
]
```

#### `POST /jobs`

Create a new job.

**Request:**
```json
{
  "name": "Weekly Sales Report",
  "description": "Generate weekly sales report",
  "package_id": "123e4567-e89b-12d3-a456-426614174010",
  "parameters": {
    "report_type": "sales",
    "output_format": "xlsx"
  },
  "timeout_seconds": 1800,
  "retry_count": 3,
  "retry_delay_seconds": 600,
  "priority": 2,
  "tags": ["weekly", "sales", "report"]
}
```

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174012",
  "name": "Weekly Sales Report",
  "description": "Generate weekly sales report",
  "package_id": "123e4567-e89b-12d3-a456-426614174010",
  "parameters": {
    "report_type": "sales",
    "output_format": "xlsx"
  },
  "timeout_seconds": 1800,
  "retry_count": 3,
  "retry_delay_seconds": 600,
  "priority": 2,
  "status": "active",
  "tags": ["weekly", "sales", "report"],
  "created_at": "2023-07-15T15:00:45Z"
}
```

#### `GET /jobs/{job_id}`

Get job details.

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174011",
  "name": "Daily Invoice Processing",
  "description": "Process invoices daily at 8 AM",
  "package_id": "123e4567-e89b-12d3-a456-426614174008",
  "package": {
    "name": "Invoice Processing",
    "version": "1.0.0"
  },
  "parameters": {
    "source_folder": "invoices/incoming",
    "destination_folder": "invoices/processed"
  },
  "timeout_seconds": 3600,
  "retry_count": 3,
  "retry_delay_seconds": 300,
  "priority": 1,
  "status": "active",
  "tags": ["daily", "finance"],
  "created_at": "2023-06-15T09:30:45Z",
  "updated_at": "2023-07-10T08:15:30Z",
  "dependencies": [
    {
      "job_id": "123e4567-e89b-12d3-a456-426614174013",
      "name": "Download Invoices"
    }
  ],
  "schedules": [
    {
      "schedule_id": "123e4567-e89b-12d3-a456-426614174014",
      "name": "Daily 8 AM",
      "cron_expression": "0 8 * * *",
      "timezone": "UTC"
    }
  ]
}
```

#### `PUT /jobs/{job_id}`

Update a job.

**Request:**
```json
{
  "description": "Updated description for daily invoice processing",
  "parameters": {
    "source_folder": "invoices/new",
    "destination_folder": "invoices/processed"
  },
  "tags": ["daily", "finance", "invoices"]
}
```

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174011",
  "name": "Daily Invoice Processing",
  "description": "Updated description for daily invoice processing",
  "parameters": {
    "source_folder": "invoices/new",
    "destination_folder": "invoices/processed"
  },
  "tags": ["daily", "finance", "invoices"],
  "updated_at": "2023-07-15T15:05:45Z"
}
```

#### `DELETE /jobs/{job_id}`

Delete a job.

**Response Status Code:** 204 No Content

#### `POST /jobs/{job_id}/execute`

Execute a job immediately.

**Request:**
```json
{
  "agent_id": "123e4567-e89b-12d3-a456-426614174002", // Optional, if not provided a suitable agent will be selected
  "parameters": { // Optional, override job parameters
    "report_date": "2023-07-15"
  }
}
```

**Response:**
```json
{
  "execution_id": "123e4567-e89b-12d3-a456-426614174015",
  "job_id": "123e4567-e89b-12d3-a456-426614174011",
  "status": "queued",
  "agent_id": "123e4567-e89b-12d3-a456-426614174002",
  "created_at": "2023-07-15T15:10:45Z"
}
```

## Job Execution Management

### Endpoints

#### `GET /job-executions`

Get list of job executions.

**Query Parameters:**
- `job_id` (optional): Filter by job ID
- `agent_id` (optional): Filter by agent ID
- `status` (optional): Filter by execution status
- `from_date` (optional): Filter by start date
- `to_date` (optional): Filter by end date
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum records to return (default: 100)

**Response:**
```json
[
  {
    "execution_id": "123e4567-e89b-12d3-a456-426614174015",
    "job_id": "123e4567-e89b-12d3-a456-426614174011",
    "job": {
      "name": "Daily Invoice Processing"
    },
    "agent_id": "123e4567-e89b-12d3-a456-426614174002",
    "agent": {
      "name": "Production Agent 1"
    },
    "status": "completed",
    "start_time": "2023-07-15T15:10:45Z",
    "end_time": "2023-07-15T15:15:30Z",
    "triggered_by": "manual"
  }
]
```

#### `GET /job-executions/{execution_id}`

Get job execution details.

**Response:**
```json
{
  "execution_id": "123e4567-e89b-12d3-a456-426614174015",
  "job_id": "123e4567-e89b-12d3-a456-426614174011",
  "job": {
    "name": "Daily Invoice Processing",
    "parameters": {
      "source_folder": "invoices/new",
      "destination_folder": "invoices/processed"
    }
  },
  "agent_id": "123e4567-e89b-12d3-a456-426614174002",
  "agent": {
    "name": "Production Agent 1"
  },
  "status": "completed",
  "start_time": "2023-07-15T15:10:45Z",
  "end_time": "2023-07-15T15:15:30Z",
  "parameters": {
    "source_folder": "invoices/new",
    "destination_folder": "invoices/processed",
    "report_date": "2023-07-15"
  },
  "result_data": {
    "processed_count": 15,
    "error_count": 0,
    "total_amount": 25150.75
  },
  "result_files": [
    {
      "name": "processing_report.xlsx",
      "size": 25600,
      "url": "/api/v1/job-executions/123e4567-e89b-12d3-a456-426614174015/files/processing_report.xlsx"
    }
  ],
  "triggered_by": "manual",
  "retry_count": 0
}
```

#### `GET /job-executions/{execution_id}/logs`

Get job execution logs.

**Query Parameters:**
- `log_level` (optional): Filter by log level
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum records to return (default: 100)

**Response:**
```json
[
  {
    "log_id": "123e4567-e89b-12d3-a456-426614174016",
    "execution_id": "123e4567-e89b-12d3-a456-426614174015",
    "log_level": "info",
    "timestamp": "2023-07-15T15:10:50Z",
    "message": "Starting invoice processing",
    "metadata": {
      "source_folder": "invoices/new"
    }
  },
  {
    "log_id": "123e4567-e89b-12d3-a456-426614174017",
    "execution_id": "123e4567-e89b-12d3-a456-426614174015",
    "log_level": "info",
    "timestamp": "2023-07-15T15:15:25Z",
    "message": "Invoice processing completed",
    "metadata": {
      "processed_count": 15,
      "error_count": 0
    }
  }
]
```

#### `GET /job-executions/{execution_id}/files/{file_name}`

Download a job execution result file.

**Response:** File with appropriate Content-Type and Content-Disposition headers.

#### `POST /job-executions/{execution_id}/cancel`

Cancel a running job execution.

**Response:**
```json
{
  "execution_id": "123e4567-e89b-12d3-a456-426614174015",
  "job_id": "123e4567-e89b-12d3-a456-426614174011",
  "status": "canceled",
  "updated_at": "2023-07-15T15:12:45Z"
}
```

## Schedule Management

### Endpoints

#### `GET /schedules`

Get list of schedules.

**Query Parameters:**
- `job_id` (optional): Filter by job ID
- `status` (optional): Filter by schedule status
- `search` (optional): Search term
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum records to return (default: 100)

**Response:**
```json
[
  {
    "schedule_id": "123e4567-e89b-12d3-a456-426614174014",
    "name": "Daily 8 AM",
    "job_id": "123e4567-e89b-12d3-a456-426614174011",
    "job": {
      "name": "Daily Invoice Processing"
    },
    "cron_expression": "0 8 * * *",
    "timezone": "UTC",
    "status": "active",
    "last_run_time": "2023-07-15T08:00:00Z",
    "next_run_time": "2023-07-16T08:00:00Z"
  }
]
```

#### `POST /schedules`

Create a new schedule.

**Request:**
```json
{
  "name": "Weekly Monday 9 AM",
  "description": "Run every Monday at 9 AM",
  "job_id": "123e4567-e89b-12d3-a456-426614174012",
  "cron_expression": "0 9 * * 1",
  "timezone": "America/New_York",
  "parameters": {
    "report_week": "previous"
  },
  "start_date": "2023-07-17T00:00:00Z"
}
```

**Response:**
```json
{
  "schedule_id": "123e4567-e89b-12d3-a456-426614174018",
  "name": "Weekly Monday 9 AM",
  "description": "Run every Monday at 9 AM",
  "job_id": "123e4567-e89b-12d3-a456-426614174012",
  "cron_expression": "0 9 * * 1",
  "timezone": "America/New_York",
  "parameters": {
    "report_week": "previous"
  },
  "start_date": "2023-07-17T00:00:00Z",
  "status": "active",
  "next_run_time": "2023-07-17T13:00:00Z", // UTC time
  "created_at": "2023-07-15T15:20:45Z"
}
```

#### `GET /schedules/{schedule_id}`

Get schedule details.

**Response:**
```json
{
  "schedule_id": "123e4567-e89b-12d3-a456-426614174014",
  "name": "Daily 8 AM",
  "description": "Run invoice processing daily at 8 AM",
  "job_id": "123e4567-e89b-12d3-a456-426614174011",
  "job": {
    "name": "Daily Invoice Processing",
    "parameters": {
      "source_folder": "invoices/new",
      "destination_folder": "invoices/processed"
    }
  },
  "cron_expression": "0 8 * * *",
  "timezone": "UTC",
  "parameters": {},
  "start_date": "2023-06-15T00:00:00Z",
  "status": "active",
  "last_run_time": "2023-07-15T08:00:00Z",
  "next_run_time": "2023-07-16T08:00:00Z",
  "created_at": "2023-06-15T09:35:45Z",
  "updated_at": "2023-07-15T08:00:05Z"
}
```

#### `PUT /schedules/{schedule_id}`

Update a schedule.

**Request:**
```json
{
  "name": "Daily 9 AM",
  "cron_expression": "0 9 * * *",
  "parameters": {
    "process_previous_day": true
  }
}
```

**Response:**
```json
{
  "schedule_id": "123e4567-e89b-12d3-a456-426614174014",
  "name": "Daily 9 AM",
  "cron_expression": "0 9 * * *",
  "parameters": {
    "process_previous_day": true
  },
  "next_run_time": "2023-07-16T09:00:00Z",
  "updated_at": "2023-07-15T15:25:45Z"
}
```

#### `DELETE /schedules/{schedule_id}`

Delete a schedule.

**Response Status Code:** 204 No Content

#### `POST /schedules/{schedule_id}/pause`

Pause a schedule.

**Response:**
```json
{
  "schedule_id": "123e4567-e89b-12d3-a456-426614174014",
  "name": "Daily 9 AM",
  "status": "paused",
  "updated_at": "2023-07-15T15:30:45Z"
}
```

#### `POST /schedules/{schedule_id}/resume`

Resume a paused schedule.

**Response:**
```json
{
  "schedule_id": "123e4567-e89b-12d3-a456-426614174014",
  "name": "Daily 9 AM",
  "status": "active",
  "next_run_time": "2023-07-16T09:00:00Z",
  "updated_at": "2023-07-15T15:35:45Z"
}
```