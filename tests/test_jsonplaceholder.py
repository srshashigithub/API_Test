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

import allure
import pytest
import requests

BASE = "https://jsonplaceholder.typicode.com"

POST_FIELDS = {"id", "userId", "title", "body"}
USER_FIELDS = {"id", "name", "username", "email", "address", "phone", "website", "company"}


# ──────────────────────────────────────────────────────────────────────────────
# TC-01  GET /posts/{id}  —  valid IDs return 200 + correct schema + correct id
# ──────────────────────────────────────────────────────────────────────────────
@allure.epic("JSONPlaceholder API")
@allure.feature("Posts")
@allure.story("Get single post")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("post_id", [1, 50, 100])
def test_get_post_valid_id(http, post_id):
    """Valid IDs must return 200, a complete post schema, and the correct id."""
    with allure.step(f"GET /posts/{post_id}"):
        resp = http.get(f"{BASE}/posts/{post_id}")

    with allure.step("Assert status 200"):
        assert resp.status_code == 200, f"Expected 200 for /posts/{post_id}"

    data = resp.json()
    allure.attach(str(data), name="Response body", attachment_type=allure.attachment_type.TEXT)

    with allure.step("Assert schema completeness"):
        missing = POST_FIELDS - data.keys()
        assert not missing, f"post/{post_id} is missing fields: {missing}"

    with allure.step("Assert id, userId, title, body values"):
        assert data["id"] == post_id,               f"'id' mismatch: expected {post_id}, got {data['id']}"
        assert isinstance(data["userId"], int),      "'userId' must be an integer"
        assert 1 <= data["userId"] <= 10,            f"'userId' {data['userId']} out of expected range 1–10"
        assert isinstance(data["title"], str) and data["title"].strip(), "'title' must be a non-empty string"
        assert isinstance(data["body"],  str) and data["body"].strip(),  "'body' must be a non-empty string"


# ──────────────────────────────────────────────────────────────────────────────
# TC-02  GET /posts/{id}  —  out-of-range IDs return 404
# ──────────────────────────────────────────────────────────────────────────────
@allure.epic("JSONPlaceholder API")
@allure.feature("Posts")
@allure.story("Get single post — invalid ID")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("invalid_id", [0, 101, 9999])
def test_get_post_invalid_id_returns_404(http, invalid_id):
    """IDs outside [1, 100] must return 404."""
    with allure.step(f"GET /posts/{invalid_id}"):
        resp = http.get(f"{BASE}/posts/{invalid_id}")

    with allure.step("Assert status 404"):
        assert resp.status_code == 404, (
            f"Expected 404 for /posts/{invalid_id}, got {resp.status_code}"
        )


# ──────────────────────────────────────────────────────────────────────────────
# TC-03  GET /posts?userId=N  —  filter returns the right posts
# ──────────────────────────────────────────────────────────────────────────────
@allure.epic("JSONPlaceholder API")
@allure.feature("Posts")
@allure.story("Filter posts by userId")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("user_id", [1, 3, 7, 10])
def test_filter_posts_by_user(http, user_id):
    """userId filter must return exactly 10 posts all belonging to that user."""
    with allure.step(f"GET /posts?userId={user_id}"):
        resp = http.get(f"{BASE}/posts", params={"userId": user_id})

    with allure.step("Assert status 200 and list length = 10"):
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list),  "Filtered response must be a JSON array"
        assert len(data) == 10,         f"userId={user_id}: expected 10 posts, got {len(data)}"

    with allure.step("Assert ownership integrity — every post belongs to the requested user"):
        wrong_owner = [p["id"] for p in data if p.get("userId") != user_id]
        assert not wrong_owner, f"Posts {wrong_owner} do not belong to userId={user_id}"


# ──────────────────────────────────────────────────────────────────────────────
# TC-04  POST /posts  —  create returns 201 and echoes the request body
# ──────────────────────────────────────────────────────────────────────────────
@allure.epic("JSONPlaceholder API")
@allure.feature("Posts")
@allure.story("Create post")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("payload", [
    {"title": "Hello World",   "body": "First test post",   "userId": 1},
    {"title": "Second article","body": "Another test post", "userId": 7},
])
def test_create_post_returns_201_and_echoes_body(http, payload):
    """POST /posts must return 201 and echo all submitted fields plus a new id."""
    with allure.step(f"POST /posts with payload {payload}"):
        resp = http.post(f"{BASE}/posts", json=payload)

    allure.attach(str(resp.json()), name="Response body", attachment_type=allure.attachment_type.TEXT)

    with allure.step("Assert status 201 Created"):
        assert resp.status_code == 201, f"Expected 201 Created, got {resp.status_code}"

    data = resp.json()
    with allure.step("Assert generated id is a positive integer"):
        assert "id" in data,                        "Response must include a generated 'id'"
        assert isinstance(data["id"], int) and data["id"] > 0, "'id' must be a positive integer"

    with allure.step("Assert all submitted fields are echoed back"):
        for key, expected in payload.items():
            assert data.get(key) == expected, (
                f"Field '{key}': expected '{expected}', got '{data.get(key)}'"
            )


# ──────────────────────────────────────────────────────────────────────────────
# TC-05  GET /posts  —  full collection size and Content-Type header
# ──────────────────────────────────────────────────────────────────────────────
@allure.epic("JSONPlaceholder API")
@allure.feature("Posts")
@allure.story("Posts collection")
@allure.severity(allure.severity_level.NORMAL)
def test_posts_collection_returns_100_items(http):
    """GET /posts must return a list of exactly 100 posts."""
    with allure.step("GET /posts"):
        resp = http.get(f"{BASE}/posts")

    with allure.step("Assert status 200 and list length = 100"):
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 99, f"Expected 99 posts, got {len(data)}"  # intentional failure


@allure.epic("JSONPlaceholder API")
@allure.feature("Headers")
@allure.story("Content-Type validation")
@allure.severity(allure.severity_level.MINOR)
@pytest.mark.parametrize("endpoint", ["/posts", "/posts/1", "/users"])
def test_content_type_is_application_json(http, endpoint):
    """Every GET endpoint must advertise 'application/json' in Content-Type."""
    with allure.step(f"GET {endpoint}"):
        resp = http.get(f"{BASE}{endpoint}")

    with allure.step("Assert Content-Type contains application/json"):
        ct = resp.headers.get("Content-Type", "")
        assert "application/json" in ct, f"{endpoint}: Content-Type is '{ct}'"


# ──────────────────────────────────────────────────────────────────────────────
# TC-06  GET /users  —  collection size and user schema
# ──────────────────────────────────────────────────────────────────────────────
@allure.epic("JSONPlaceholder API")
@allure.feature("Users")
@allure.story("Users collection")
@allure.severity(allure.severity_level.NORMAL)
def test_users_collection_returns_10_items(http):
    """GET /users must return a list of exactly 10 users."""
    with allure.step("GET /users"):
        resp = http.get(f"{BASE}/users")

    with allure.step("Assert status 200 and list length = 10"):
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 10, f"Expected 10 users, got {len(data)}"


@allure.epic("JSONPlaceholder API")
@allure.feature("Users")
@allure.story("User schema and email format")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("user_id", [1, 5, 10])
def test_user_schema_and_email_format(http, user_id):
    """User objects must have all required fields; email must contain '@'."""
    with allure.step(f"GET /users/{user_id}"):
        resp = http.get(f"{BASE}/users/{user_id}")

    with allure.step("Assert status 200"):
        assert resp.status_code == 200

    u = resp.json()
    allure.attach(str(u), name="Response body", attachment_type=allure.attachment_type.TEXT)

    with allure.step("Assert schema completeness"):
        missing = USER_FIELDS - u.keys()
        assert not missing, f"user/{user_id} missing fields: {missing}"

    with allure.step("Assert email format, nested address and company"):
        assert "@" in u["email"], f"user/{user_id} email '{u['email']}' is not valid"
        assert isinstance(u["address"], dict) and "city" in u["address"]
        assert isinstance(u["company"], dict) and "name" in u["company"]
