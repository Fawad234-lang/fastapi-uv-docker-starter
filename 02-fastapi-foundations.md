# Task 02 — Build a Simple Messages API

## User story

As an API client, I want to create and manage chat messages so that I can learn how REST APIs, validation, and HTTP responses work before connecting a real LLM or database.

> For this task, store messages in a Python list or dictionary. Do not add PostgreSQL, authentication, or an LLM yet.

## APIs to build

All endpoints must use the `/api/v1` prefix.

| Method | Endpoint | Purpose | Successful response |
|---|---|---|---|
| `POST` | `/api/v1/messages` | Create a message | `201 Created` |
| `GET` | `/api/v1/messages` | List messages | `200 OK` |
| `GET` | `/api/v1/messages/{message_id}` | Get one message | `200 OK` |
| `PATCH` | `/api/v1/messages/{message_id}` | Update message content | `200 OK` |
| `DELETE` | `/api/v1/messages/{message_id}` | Delete a message | `204 No Content` |

The list endpoint must support these optional query parameters:

- `limit`: maximum messages returned, from 1 to 100; default 20.
- `offset`: number of messages skipped; default 0.
- `role`: filter by `user` or `assistant`.

## Data models

### Create message request

```json
{
  "role": "user",
  "content": "What is FastAPI?"
}
```

### Update message request

```json
{
  "content": "Explain FastAPI in simple words."
}
```

### Message response

```json
{
  "id": 1,
  "role": "user",
  "content": "What is FastAPI?",
  "created_at": "2026-10-13T10:00:00Z"
}
```

## Validation and errors

- `role` must be either `user` or `assistant`.
- `content` must contain 1–2,000 characters after trimming whitespace.
- `limit` and `offset` must follow their documented ranges.
- Return `404 Not Found` when a requested message ID does not exist.
- Return FastAPI's standard `422 Unprocessable Entity` response for invalid input.
- Add a custom JSON error response for the 404 case.

## Acceptance criteria

- All five endpoints work through Swagger UI.
- Creating a valid message returns 201 and a generated ID and timestamp.
- Listing supports pagination and role filtering.
- Getting, updating, or deleting an unknown ID returns 404.
- Invalid role, empty content, oversized content, and invalid query parameters return 422.
- Deleting a message returns 204 with no response body.
- Request and response bodies use separate Pydantic models.
- Endpoint descriptions, response models, status codes, and tags appear in OpenAPI documentation.

## Verification

Add automated tests for at least these cases:

1. Create a valid message.
2. Reject an empty message.
3. List messages using `limit`, `offset`, and `role`.
4. Retrieve an existing message.
5. Return 404 for a missing message.
6. Update a message.
7. Delete a message and confirm it can no longer be retrieved.

Also demonstrate the complete create → list → retrieve → update → delete flow in Swagger UI or with an API client.

## Submission

Push branch `task/02-fastapi-foundations` and open a pull request containing:

- The implementation and automated tests.
- Sample request and response examples.
- A short explanation of when the API returns 201, 204, 404, and 422.
- Confirmation that no database, authentication, or LLM was added in this task.
