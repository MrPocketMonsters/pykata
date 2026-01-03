# API Quick Reference

This document provides a concise reference for the PyKata API endpoints, focusing on request/response schemas and usage examples. For detailed architecture and implementation notes, see [API (src/README.md)](src/README.md#api-api).

## Endpoints Summary

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health` | Service health check |
| `GET` | `/katas` | List all katas (metadata only) |
| `GET` | `/katas/{id}` | Get single kata details (includes code) |
| `POST` | `/katas/run` | Execute kata code |

---

## Health Check

### `GET /health`

**Responses:**

- **200 OK** (Healthy)

  ```json
  {
    "status": "healthy",
    "services": {
      "dynamodb": true,
      "s3": true
    }
  }
  ```

- **503 Service Unavailable** (Degraded)

  ```json
  {
    "status": "degraded",
    "services": {
      "dynamodb": false,
      "s3": true
    }
  }
  ```

**Example:**

```bash
curl http://localhost:8000/health
```

---

## Kata Retrieval

### `GET /katas`

**Query Parameters:**

- `limit` (int, default: 20)
- `offset` (int, default: 0)

**Responses:**

- **200 OK**

  ```json
  [
    {
      "id": "kata-123",
      "title": "Reverse String",
      "description": "Reverse a given string",
      "tags": ["strings", "algorithms"],
      "difficulty": "beginner"
    }
  ]
  ```

- **400 Bad Request**: Invalid parameters.
- **500 Internal Server Error**: Database connection issues.

**Example:**

```bash
curl "http://localhost:8000/katas?limit=10&offset=0"
```

### `GET /katas/{kata_id}`

**Path Parameters:**

- `kata_id` (string)

**Responses:**

- **200 OK**

  ```json
  {
    "id": "kata-123",
    "title": "Reverse String",
    "description": "Reverse a given string",
    "tags": ["strings", "algorithms"],
    "difficulty": "beginner",
    "code": "print(input()[::-1])",
    "sample_input": "hello",
    "sample_output": "olleh"
  }
  ```

- **404 Not Found**: Kata ID does not exist.
- **500 Internal Server Error**: Storage retrieval failure.

**Example:**

```bash
curl "http://localhost:8000/katas/kata-123"
```

---

## Execution

### `POST /katas/run`

**Request Body:**

```json
{
  "kata_id": "kata-123",
  "user_input": "sample input data",
  "max_timeout": 10
}
```

**Responses:**

- **200 OK**

  ```json
  {
    "success": true,
    "stdout": "output from code",
    "stderr": "",
    "execution_time_ms": 150
  }
  ```

- **404 Not Found**: Kata ID does not exist.
- **500 Internal Server Error**: Execution service failure.

**Example:**

```bash
curl -X POST "http://localhost:8000/katas/run" \
  -H "Content-Type: application/json" \
  -d '{"kata_id": "kata-123", "user_input": "hello"}'
```

---

## Error Schema

Standard structure for 400, 404, 408, and 500 errors:

```json
{
  "detail": "Human-readable error message",
  "status_code": 400,
  "errors": [],
  "path": "/requested/path"
}
```
