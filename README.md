# API Automated Tests — JSONPlaceholder

## Selected API

**JSONPlaceholder** · `https://jsonplaceholder.typicode.com`  
Source: [public-apis/public-apis](https://github.com/public-apis/public-apis) — *Test Data* category.

JSONPlaceholder is a free, zero-auth, always-available fake REST API.  It is one
of the most widely used tools for testing and prototyping HTTP clients, with a
stable contract and predictable dataset (100 posts, 10 users, etc.).

---

## Test Results

All **20 test cases** pass.

```text
20 passed in 4.25s
```

---

## Test Cases

| TC | Function | Method | Endpoint | Parametrize values | What is asserted | Validation type |
| --- | --- | --- | --- | --- | --- | --- |
| TC-01a | `test_get_post_valid_id` | GET | `/posts/1` | `post_id = 1` | Status 200, schema complete, `id` echoed, `userId` in 1–10, non-empty strings | Status + Schema + Value |
| TC-01b | `test_get_post_valid_id` | GET | `/posts/50` | `post_id = 50` | Same as TC-01a | Status + Schema + Value |
| TC-01c | `test_get_post_valid_id` | GET | `/posts/100` | `post_id = 100` | Same as TC-01a | Status + Schema + Value |
| TC-02a | `test_get_post_invalid_id_returns_404` | GET | `/posts/0` | `invalid_id = 0` | Status 404 | Status |
| TC-02b | `test_get_post_invalid_id_returns_404` | GET | `/posts/101` | `invalid_id = 101` | Status 404 | Status |
| TC-02c | `test_get_post_invalid_id_returns_404` | GET | `/posts/9999` | `invalid_id = 9999` | Status 404 | Status |
| TC-03a | `test_filter_posts_by_user` | GET | `/posts?userId=1` | `user_id = 1` | Status 200, list length = 10, all posts owned by user | Status + Count + Ownership |
| TC-03b | `test_filter_posts_by_user` | GET | `/posts?userId=3` | `user_id = 3` | Same as TC-03a | Status + Count + Ownership |
| TC-03c | `test_filter_posts_by_user` | GET | `/posts?userId=7` | `user_id = 7` | Same as TC-03a | Status + Count + Ownership |
| TC-03d | `test_filter_posts_by_user` | GET | `/posts?userId=10` | `user_id = 10` | Same as TC-03a | Status + Count + Ownership |
| TC-04a | `test_create_post_returns_201_and_echoes_body` | POST | `/posts` | `payload0` (userId=1) | Status 201, `id` is a positive int, all submitted fields echoed | Status + Schema + Echo |
| TC-04b | `test_create_post_returns_201_and_echoes_body` | POST | `/posts` | `payload1` (userId=7) | Same as TC-04a | Status + Schema + Echo |
| TC-05a | `test_posts_collection_returns_100_items` | GET | `/posts` | *(none)* | Status 200, list length = 100 | Status + Count |
| TC-05b | `test_content_type_is_application_json` | GET | `/posts` | `endpoint = /posts` | `Content-Type` contains `application/json` | Header |
| TC-05c | `test_content_type_is_application_json` | GET | `/posts/1` | `endpoint = /posts/1` | Same as TC-05b | Header |
| TC-05d | `test_content_type_is_application_json` | GET | `/users` | `endpoint = /users` | Same as TC-05b | Header |
| TC-06a | `test_users_collection_returns_10_items` | GET | `/users` | *(none)* | Status 200, list length = 10 | Status + Count |
| TC-06b | `test_user_schema_and_email_format` | GET | `/users/1` | `user_id = 1` | Schema complete, email contains `@`, nested `address.city` and `company.name` | Schema + Format + Nested |
| TC-06c | `test_user_schema_and_email_format` | GET | `/users/5` | `user_id = 5` | Same as TC-06b | Schema + Format + Nested |
| TC-06d | `test_user_schema_and_email_format` | GET | `/users/10` | `user_id = 10` | Same as TC-06b | Schema + Format + Nested |

---

## Validation Strategies — What and Why

### 1 · Status-code validation

Every test checks the HTTP status code first (200, 201, or 404).  
**Why:** The status code is the primary contract signal.  A body that looks fine but arrives with the wrong code can silently break clients that branch on `resp.ok`.

### 2 · Schema completeness (required-field presence)

Tests TC-01 and TC-06 build a set of expected keys (`POST_FIELDS`, `USER_FIELDS`) and assert `missing_fields = expected - actual.keys()` is empty.  
**Why:** APIs sometimes silently drop fields in a new deploy (e.g. a renamed column, a serialiser change).  A set-difference check catches removals without needing to enumerate every key individually, making the test easy to extend.

### 3 · Data-type and value-range validation

TC-01 additionally checks that `userId` is an `int` in `[1, 10]`, `title` and `body` are non-empty strings.  
**Why:** A field present but with the wrong type (e.g. `"userId": "1"` instead of `1`) breaks downstream code that does arithmetic or integer comparisons.  An empty string passes a presence check but fails a rendering check; catching it at the API layer prevents silent data quality regressions.

### 4 · Business-logic / ownership integrity validation

TC-03 asserts that every post returned by `?userId=N` actually has `post["userId"] == N`.  
**Why:** A broken filter that ignores the query param would still return a list with the right length if checked naively.  Iterating over every item and verifying ownership is the only way to confirm the filter is applied correctly rather than just returning all data.

### 5 · Collection-size validation

TC-05 and TC-06 assert exact counts (100 posts, 10 users).  
**Why:** JSONPlaceholder is a fixed dataset; a change in count signals either test-data corruption or an accidental API behaviour change.  For real APIs with dynamic data, a `len(data) >= minimum` lower-bound is more appropriate (as used in `test_filter_posts_by_user`).

### 6 · Create-response echo validation (POST round-trip)

TC-04 submits a POST body and checks that every submitted field is mirrored back in the response.  
**Why:** An API might accept a request with 200/201 but silently discard some fields.  A field-by-field comparison of the payload against the response body is the only way to confirm the data was actually received and returned correctly.

### 7 · Content-Type header validation

TC-05b/c/d confirm `application/json` is present in the `Content-Type` response header.  
**Why:** Clients typically call `resp.json()` without checking the MIME type first.  If the server misconfigures a route to return `text/html` (e.g. an error page), the JSON parser throws an unexpected exception rather than a clear test failure.  Validating the header makes that failure explicit.

### 8 · Format validation (email `@` check)

TC-06b/c/d assert `"@" in user["email"]`.  
**Why:** A value can exist and be a string while still being semantically invalid.  Checking for `@` is a lightweight sanity-check that catches obviously malformed emails (empty strings, placeholder values) without pulling in a full regex library.

---

## Why `@pytest.mark.parametrize`?

Each test function that uses `@pytest.mark.parametrize`:

- **Reduces duplication** — one function body covers N cases instead of N identical copy-pasted functions.
- **Keeps coverage high** — adding a new data point requires one extra tuple in the parameter list, not a new function.
- **Gives clear failure labels** — pytest names each case `test_get_post_valid_id[50]` so a failure immediately identifies the offending input without reading the body.
- **Enables selective re-runs** — `pytest -k "post_id-100"` re-runs only that case during debugging.

---

## Project Structure

```text
api-tests/
├── conftest.py                      # session-scoped requests.Session fixture
├── pytest.ini                       # testpaths, verbosity flags
├── requirements.txt                 # pytest, allure-pytest, requests
├── tests/
│   └── test_jsonplaceholder.py      # all test cases
└── README.md
```

## Running the Tests

```bash
pip install -r requirements.txt

# run all tests
python -m pytest

# run a single test group
python -m pytest -k "filter_posts"
```

## Allure Report

### Prerequisites — install Allure CLI once

**Windows (scoop):**

```bash
scoop install allure
```

**Windows (manual):** Download the zip from [allure-framework releases](https://github.com/allure-framework/allure2/releases), extract it, and add the `bin/` folder to your PATH.

### Generate and view the report

```bash
# 1. Run tests and collect results
python -m pytest --alluredir=allure-results

# 2. Open the interactive report in your browser
allure serve allure-results
```

The `allure serve` command starts a local web server and automatically opens the report in your default browser.

To save a static copy instead:

```bash
allure generate allure-results --clean -o allure-report
# then open allure-report/index.html
```
