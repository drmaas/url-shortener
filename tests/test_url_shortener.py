import pytest
import json
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.url_shortener import create_app

class FakeDynamoDBRepository:
    def __init__(self):
        self.data = {}

    def put_item(self, Item):
        self.data[Item["shortCode"]] = Item

    def get_item(self, key):
        if key in self.data:
            return self.data[key]
        return None

    def update_item(self, Key, UpdateExpression, ExpressionAttributeValues):
        if Key["shortCode"] in self.data:
            clicks = self.data[Key["shortCode"]]["clicks"]
            self.data[Key["shortCode"]]["clicks"] = clicks + 1
            
@pytest.fixture
def fake_dynamodb_repository():
    return FakeDynamoDBRepository()

@pytest.fixture
def test_app(fake_dynamodb_repository):
    app = create_app(fake_dynamodb_repository)
    return app

@pytest.fixture
def test_client(test_app):
    return TestClient(test_app) # Create TestClient instance

@pytest.fixture
def example_long_url():
    return "https://www.example.com/very/long/url"

@pytest.fixture
def example_short_code():
    return "abc12345"

def test_shorten_url_success(test_client, fake_dynamodb_repository, example_long_url, example_short_code):
    import random
    original_choices = random.choices
    random.choices = MagicMock(return_value=list(example_short_code))
    response = test_client.post("/url", json={"longUrl": example_long_url})
    data = response.json() # Use response.json()
    assert response.status_code == 200
    assert "shortUrl" in data
    assert data["shortUrl"] == f"http://testserver/{example_short_code}" # Use testserver
    assert example_short_code in fake_dynamodb_repository.data
    assert fake_dynamodb_repository.data[example_short_code]["longUrl"] == example_long_url
    random.choices = original_choices

def test_redirect_url_success(test_client, fake_dynamodb_repository, example_long_url, example_short_code):
    fake_dynamodb_repository.put_item({"shortCode": example_short_code, "longUrl": example_long_url, "createdAt": 1, "clicks": 0, "custom": False})
    response = test_client.get(f"/{example_short_code}", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == example_long_url
    assert fake_dynamodb_repository.data[example_short_code]["clicks"] == 1

def test_redirect_url_not_found(test_client):
    response = test_client.get("/notfound")
    assert response.status_code == 404
    assert b"Short code not found" in response.content

def test_get_original_url_success(test_client, fake_dynamodb_repository, example_long_url, example_short_code):
    fake_dynamodb_repository.put_item({"shortCode": example_short_code, "longUrl": example_long_url, "createdAt": 1, "clicks": 0, "custom": False})
    response = test_client.get(f"/url/{example_short_code}")
    data = response.json()
    assert response.status_code == 200
    assert data["longUrl"] == example_long_url

def test_get_original_url_not_found(test_client):
    response = test_client.get("/url/notfound")
    assert response.status_code == 404

def test_get_click_stats_success(test_client, fake_dynamodb_repository, example_short_code):
    fake_dynamodb_repository.put_item({"shortCode": example_short_code, "longUrl": "example.com", "createdAt": 1, "clicks": 5, "custom": False})
    response = test_client.get(f"/stats/{example_short_code}")
    data = response.json()
    assert response.status_code == 200
    assert data["clicks"] == 5

def test_get_click_stats_not_found(test_client):
    response = test_client.get("/stats/notfound")
    assert response.status_code == 404

def test_shorten_url_collision(test_client, fake_dynamodb_repository, example_long_url, example_short_code):
    fake_dynamodb_repository.put_item({"shortCode": example_short_code, "longUrl": "existing_url", "createdAt": 1, "clicks": 0, "custom": False})
    import random
    original_choices = random.choices
    random.choices = MagicMock(side_effect=[list(example_short_code), list("bcdefghi")])
    response = test_client.post("/url", json={"longUrl": example_long_url})
    data = response.json()
    assert response.status_code == 200
    assert data["shortUrl"] == "http://testserver/bcdefghi"
    random.choices = original_choices

def test_shorten_url_invalid_url(test_client):
    response = test_client.post("/url", json={"longUrl": "invalid-url"})
    assert response.status_code == 422

def test_shorten_url_missing_long_url(test_client):
    response = test_client.post("/url", json={})
    assert response.status_code == 422