import pytest
from fastapi.testclient import TestClient


def test_root_redirect(client):
    """Test that root path redirects to static/index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test getting list of activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    # Check for some expected activities
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert "Basketball Team" in data
    
    # Check activity structure
    activity = data["Chess Club"]
    assert "description" in activity
    assert "schedule" in activity
    assert "max_participants" in activity
    assert "participants" in activity
    assert isinstance(activity["participants"], list)


def test_signup_for_activity(client):
    """Test signing up a student for an activity"""
    email = "newstudent@mergington.edu"
    activity = "Chess Club"
    
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    assert activity in data["message"]


def test_signup_duplicate_email(client):
    """Test that duplicate signups are rejected"""
    email = "michael@mergington.edu"  # Already signed up for Chess Club
    activity = "Chess Club"
    
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "already signed up" in data["detail"]


def test_signup_nonexistent_activity(client):
    """Test signing up for a non-existent activity"""
    email = "test@mergington.edu"
    activity = "Nonexistent Club"
    
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email}
    )
    
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"]


def test_unregister_from_activity(client):
    """Test unregistering a student from an activity"""
    email = "michael@mergington.edu"
    activity = "Chess Club"
    
    # Verify student is registered
    response = client.get("/activities")
    assert email in response.json()[activity]["participants"]
    
    # Unregister
    response = client.delete(
        f"/activities/{activity}/unregister",
        params={"email": email}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    assert activity in data["message"]
    
    # Verify student is no longer registered
    response = client.get("/activities")
    assert email not in response.json()[activity]["participants"]


def test_unregister_not_registered(client):
    """Test unregistering a student who is not registered"""
    email = "notregistered@mergington.edu"
    activity = "Chess Club"
    
    response = client.delete(
        f"/activities/{activity}/unregister",
        params={"email": email}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "not registered" in data["detail"]


def test_unregister_nonexistent_activity(client):
    """Test unregistering from a non-existent activity"""
    email = "test@mergington.edu"
    activity = "Nonexistent Club"
    
    response = client.delete(
        f"/activities/{activity}/unregister",
        params={"email": email}
    )
    
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"]


def test_signup_and_unregister_flow(client):
    """Test complete signup and unregister flow"""
    email = "testflow@mergington.edu"
    activity = "Tennis Club"
    
    # Sign up
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email}
    )
    assert response.status_code == 200
    
    # Verify signup
    response = client.get("/activities")
    assert email in response.json()[activity]["participants"]
    
    # Unregister
    response = client.delete(
        f"/activities/{activity}/unregister",
        params={"email": email}
    )
    assert response.status_code == 200
    
    # Verify unregister
    response = client.get("/activities")
    assert email not in response.json()[activity]["participants"]


def test_activity_participants_count(client):
    """Test that participant count affects availability"""
    response = client.get("/activities")
    data = response.json()
    
    # Check that availability calculation works
    for activity_name, activity_data in data.items():
        max_participants = activity_data["max_participants"]
        num_participants = len(activity_data["participants"])
        assert num_participants <= max_participants
