"""
Automated tests for JSONPlaceholder API  (https://jsonplaceholder.typicode.com)
Source: public-apis/public-apis — "Test Data" category.

JSONPlaceholder is a free, zero-auth fake REST API widely used for prototyping
and testing HTTP clients.  It exposes six resource types; this suite exercises
the /posts and /users endpoints.

Endpoints exercised
-------------------
GET  /posts           – full collection (100 posts)
GET  /posts/{id}      – single post by numeric ID
GET  /posts?userId=N  – posts filtered by owner
POST /posts           – create a post  (returns 201 + echoed body)
GET  /users           – full collection (10 users)
"""

import pytest
import requests

BASE = "https://jsonplaceholder.typicode.com"

POST_FIELDS = {"id", "userId", "title", "body"}
USER_FIELDS = {"id", "name", "username", "email", "address", "phone", "website", "company"}


# ──────────────────────────────────────────────────────────────────────────────
# TC-01  GET /posts/{id}  —  valid IDs return 200 + correct schema + correct id
#
# Why parametrize: samples three evenly-spaced IDs (first, middle, last) so a
# regression on a specific post won't hide behind a lucky single-point test.
# Validation: status code, schema completeness, id echo, userId domain (1–10).
# ──────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("post_id", [1, 50, 100])
def test_get_post_valid_id(http, post_id):
    """Valid IDs must return 200, a complete post schema, and the correct id."""
    resp = http.get(f"{BASE}/posts/{post_id}")

    assert resp.status_code == 200, f"Expected 200 for /posts/{post_id}"

    data = resp.json()
    assert isinstance(data, dict), "Response body must be a JSON object"

    missing = POST_FIELDS - data.keys()
    assert not missing, f"post/{post_id} is missing fields: {missing}"

    assert data["id"] == post_id,               f"'id' mismatch: expected {post_id}, got {data['id']}"
    assert isinstance(data["userId"], int),      "'userId' must be an integer"
    assert 1 <= data["userId"] <= 10,            f"'userId' {data['userId']} out of expected range 1–10"
    assert isinstance(data["title"], str) and data["title"].strip(), "'title' must be a non-empty string"
    assert isinstance(data["body"],  str) and data["body"].strip(),  "'body' must be a non-empty string"


# ──────────────────────────────────────────────────────────────────────────────
# TC-02  GET /posts/{id}  —  out-of-range IDs return 404
#
# Why parametrize: tests the boundary (101) and deep out-of-range (9999) to
# distinguish "boundary check" from "global 404 handler."
# Validation: status code only — there is no meaningful body to validate on 404.
# ──────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("invalid_id", [0, 101, 9999])
def test_get_post_invalid_id_returns_404(http, invalid_id):
    """IDs outside [1, 100] must return 404."""
    resp = http.get(f"{BASE}/posts/{invalid_id}")
    assert resp.status_code == 404, (
        f"Expected 404 for /posts/{invalid_id}, got {resp.status_code}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# TC-03  GET /posts?userId=N  —  filter returns the right posts
#
# Why parametrize: checks four different users so we confirm the filter works
# across the dataset, not just for userId=1.
# Validation: status code, list length (each user owns exactly 10 posts), and
# that every returned post actually belongs to the requested user (ownership
# integrity check).
# ──────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("user_id", [1, 3, 7, 10])
def test_filter_posts_by_user(http, user_id):
    """userId filter must return exactly 10 posts all belonging to that user."""
    resp = http.get(f"{BASE}/posts", params={"userId": user_id})

    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list),  "Filtered response must be a JSON array"
    assert len(data) == 10,         f"userId={user_id}: expected 10 posts, got {len(data)}"

    wrong_owner = [p["id"] for p in data if p.get("userId") != user_id]
    assert not wrong_owner, f"Posts {wrong_owner} do not belong to userId={user_id}"


# ──────────────────────────────────────────────────────────────────────────────
# TC-04  POST /posts  —  create returns 201 and echoes the request body
#
# Why parametrize: two distinct payloads to prove the echo behaviour is not
# hardcoded to one fixed response.
# Validation: status code 201 (Created), presence of generated 'id', and
# field-by-field echo of every submitted key.
# ──────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("payload", [
    {"title": "Hello World",   "body": "First test post",   "userId": 1},
    {"title": "Second article","body": "Another test post", "userId": 7},
])
def test_create_post_returns_201_and_echoes_body(http, payload):
    """POST /posts must return 201 and echo all submitted fields plus a new id."""
    resp = http.post(f"{BASE}/posts", json=payload)

    assert resp.status_code == 201, f"Expected 201 Created, got {resp.status_code}"

    data = resp.json()
    assert "id" in data,                        "Response must include a generated 'id'"
    assert isinstance(data["id"], int) and data["id"] > 0, "'id' must be a positive integer"

    for key, expected in payload.items():
        assert data.get(key) == expected, (
            f"Field '{key}': expected '{expected}', got '{data.get(key)}'"
        )


# ──────────────────────────────────────────────────────────────────────────────
# TC-05  GET /posts  —  full collection size and Content-Type header
#
# Why parametrize: same Content-Type expectation is asserted across three
# different endpoints so one misconfigured route doesn't go undetected.
# Validation (Content-Type): header value must contain 'application/json' so
# callers can safely invoke resp.json() without a MIME mismatch error.
# ──────────────────────────────────────────────────────────────────────────────
def test_posts_collection_returns_100_items(http):
    """GET /posts must return a list of exactly 100 posts."""
    resp = http.get(f"{BASE}/posts")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 100, f"Expected 100 posts, got {len(data)}"


@pytest.mark.parametrize("endpoint", ["/posts", "/posts/1", "/users"])
def test_content_type_is_application_json(http, endpoint):
    """Every GET endpoint must advertise 'application/json' in Content-Type."""
    resp = http.get(f"{BASE}{endpoint}")
    ct = resp.headers.get("Content-Type", "")
    assert "application/json" in ct, f"{endpoint}: Content-Type is '{ct}'"


# ──────────────────────────────────────────────────────────────────────────────
# TC-06  GET /users  —  collection size and user schema
#
# Why parametrize: samples three user IDs to validate the schema is consistent
# across different records, not just the first one.
# Validation: collection count (10 users expected), schema completeness,
# e-mail format (must contain '@'), and nested address/company objects.
# ──────────────────────────────────────────────────────────────────────────────
def test_users_collection_returns_10_items(http):
    """GET /users must return a list of exactly 10 users."""
    resp = http.get(f"{BASE}/users")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 10, f"Expected 10 users, got {len(data)}"


@pytest.mark.parametrize("user_id", [1, 5, 10])
def test_user_schema_and_email_format(http, user_id):
    """User objects must have all required fields; email must contain '@'."""
    resp = http.get(f"{BASE}/users/{user_id}")
    assert resp.status_code == 200
    u = resp.json()

    missing = USER_FIELDS - u.keys()
    assert not missing, f"user/{user_id} missing fields: {missing}"

    assert "@" in u["email"], f"user/{user_id} email '{u['email']}' is not valid"
    assert isinstance(u["address"], dict) and "city" in u["address"]
    assert isinstance(u["company"], dict) and "name" in u["company"]
