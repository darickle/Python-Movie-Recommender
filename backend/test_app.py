import os
import json
import pytest
from app import app, db
from flask_jwt_extended import create_access_token
import http.client
from unittest.mock import patch, MagicMock

# Fixture for test client
@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

# Helper to create a dummy JWT token
def get_test_token(user_id="64f0b7f1aabbccddeeff0011"):
    return create_access_token(identity=user_id)

# Test without Authorization header
def test_discover_next_unauthorized(client):
    response = client.get("/api/discover/next")
    # Expecting 401 due to missing token
    assert response.status_code == 401

# Test when user's streaming services are not set
def test_discover_next_no_streaming_services(client, monkeypatch):
    token = get_test_token()
    # Monkeypatch db.users.find_one to return a user with no streaming_services
    def fake_find_one(query):
        return {"_id": query["_id"]}
    monkeypatch.setattr("app.db.users.find_one", fake_find_one)
    
    response = client.get("/api/discover/next", headers={"Authorization": f"Bearer {token}"})
    data = json.loads(response.data)
    assert response.status_code == 400
    assert "User streaming services not set" in data.get("error", "")

# Test simulating RapidAPI error response
def test_discover_next_api_error(client, monkeypatch):
    token = get_test_token()

    # Monkeypatch db.users.find_one to return a user with streaming_services set
    def fake_find_one(query):
        return {"_id": query["_id"], "streaming_services": ["203", "26"]}
    monkeypatch.setattr("app.db.users.find_one", fake_find_one)

    # Mock the http.client.HTTPSConnection
    mock_conn = MagicMock()
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({"error": "API error"}).encode('utf-8')
    mock_conn.getresponse.return_value = mock_response
    
    with patch('http.client.HTTPSConnection', return_value=mock_conn):
        response = client.get("/api/discover/next", headers={"Authorization": f"Bearer {token}"})
        data = json.loads(response.data)
        # Expecting the endpoint to return 404 when no content is available
        assert response.status_code == 404
        # The error message should indicate no content is available
        assert "No more content available" in data.get("error", "")
