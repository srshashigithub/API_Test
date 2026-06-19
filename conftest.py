import pytest
import requests


@pytest.fixture(scope="session")
def http():
    """Session-scoped requests.Session — one TCP connection pool for the entire test run."""
    s = requests.Session()
    yield s
    s.close()
