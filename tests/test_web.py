import pytest
from crosshelp.web import app


@pytest.fixture
def client():
    """A Flask test client for sending requests."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home_page_loads(client):
    """The root page should return 200 OK with HTML."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Crossword Helper" in response.data


def test_pattern_endpoint_returns_results(client):
    """POSTing a valid pattern should return matching words."""
    response = client.post("/api/pattern", json={"pattern": "CAT"})
    assert response.status_code == 200
    data = response.get_json()
    assert "results" in data
    words = [item["word"] for item in data["results"]]
    assert "CAT" in words


def test_pattern_endpoint_rejects_empty(client):
    """An empty pattern should return 400."""
    response = client.post("/api/pattern", json={"pattern": ""})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_pattern_endpoint_rejects_invalid(client):
    """Invalid characters should return 400."""
    response = client.post("/api/pattern", json={"pattern": "C@T"})
    assert response.status_code == 400