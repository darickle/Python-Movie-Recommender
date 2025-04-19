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
        return {"_id": query["_id"], "liked_content": [], "disliked_content": []}
    monkeypatch.setattr("app.db.users.find_one", fake_find_one)
    
    # Mock StreamingService.get_discover_content to return a content item
    def fake_get_discover_content(_):
        return {
            "id": "tt0111161",
            "title": "Test Movie",
            "content_type": "movie"
        }
    
    # Patch the imported StreamingService
    with patch('app.StreamingService.get_discover_content', side_effect=fake_get_discover_content):
        response = client.get("/api/discover/next", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "id" in data

# Test simulating API error with fallback
def test_discover_next_api_error_fallback(client, monkeypatch):
    token = get_test_token()

    # Monkeypatch db.users.find_one to return a user with streaming_services
    def fake_find_one(query):
        return {
            "_id": query["_id"], 
            "streaming_services": ["203", "26"],
            "liked_content": ["tt1234567"],
            "disliked_content": []
        }
    monkeypatch.setattr("app.db.users.find_one", fake_find_one)

    # Mock StreamingService.get_discover_content to raise an exception first,
    # then return a fallback content item on second call
    call_count = [0]
    def fake_get_discover_content(_):
        call_count[0] += 1
        if call_count[0] == 1:
            raise Exception("API error")
        return {
            "id": "tt9876543",
            "title": "Fallback Movie",
            "content_type": "movie"
        }
    
    # Mock find_one for the fallback content query
    def fake_content_find_one(query, projection):
        return {
            "id": "tt5555555",
            "title": "Cache Fallback Movie",
            "content_type": "movie"
        }
    monkeypatch.setattr("app.db.content_cache.find_one", fake_content_find_one)
    
    with patch('app.StreamingService.get_discover_content', side_effect=fake_get_discover_content):
        response = client.get("/api/discover/next", headers={"Authorization": f"Bearer {token}"})
        data = json.loads(response.data)
        # Should fall back to cached content
        assert response.status_code == 200
        assert data["id"] == "tt5555555"

# Test preference recording
def test_record_preference(client, monkeypatch):
    token = get_test_token()
    user_id = "64f0b7f1aabbccddeeff0011"
    
    # Mock update_one for user document
    mock_update = MagicMock()
    monkeypatch.setattr("app.db.users.update_one", mock_update)
    
    # Test liking content
    response = client.post(
        "/api/discover/preference", 
        headers={"Authorization": f"Bearer {token}"},
        json={"content_id": "tt0111161", "preference": "like"}
    )
    
    assert response.status_code == 201
    # Check that update_one was called with the right parameters
    mock_update.assert_called_once()
    args, kwargs = mock_update.call_args
    assert args[0] == {"_id": ObjectId(user_id)}
    assert "$addToSet" in args[1]
    assert "$pull" in args[1]
    assert args[1]["$addToSet"] == {"liked_content": "tt0111161"}
    
    # Reset mock
    mock_update.reset_mock()
    
    # Test disliking content
    response = client.post(
        "/api/discover/preference", 
        headers={"Authorization": f"Bearer {token}"},
        json={"content_id": "tt0111161", "preference": "dislike"}
    )
    
    assert response.status_code == 201
    mock_update.assert_called_once()
    args, kwargs = mock_update.call_args
    assert args[1]["$addToSet"] == {"disliked_content": "tt0111161"}
