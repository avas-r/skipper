# Skipper API Reference

## Authentication

### Obtain Access Token

```
POST /api/v1/auth/token
```

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## Agents

### List Agents

```
GET /api/v1/agents
```

**Response:**
```json
{
  "agents": [
    {
      "id": "string",
      "name": "string",
      "status": "active|inactive|error",
      "last_heartbeat": "2023-09-01T12:00:00Z",
      "capabilities": ["string"]
    }
  ],
  "total": 0,
  "page": 1,
  "page_size": 20
}
```

[Additional API endpoints documentation]
