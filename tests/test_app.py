import pytest
import copy
from fastapi.testclient import TestClient
from src.app import app, activities

# Create a deep copy of the original activities for resetting between tests
ORIGINAL_ACTIVITIES = copy.deepcopy(activities)


@pytest.fixture
def client():
    """Test client fixture that resets the activities data before each test."""
    # Reset activities to original state
    activities.clear()
    activities.update(ORIGINAL_ACTIVITIES)
    return TestClient(app, follow_redirects=False)


def test_get_activities(client):
    """Test GET /activities endpoint returns all activities."""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) == 9  # Should have 9 activities
    assert "Chess Club" in data
    assert "Programming Class" in data
    # Verify structure of one activity
    chess_club = data["Chess Club"]
    assert "description" in chess_club
    assert "schedule" in chess_club
    assert "max_participants" in chess_club
    assert "participants" in chess_club
    assert isinstance(chess_club["participants"], list)


def test_signup_success(client):
    """Test successful signup for an activity."""
    email = "newstudent@mergington.edu"
    activity_name = "Chess Club"

    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 200
    result = response.json()
    assert "message" in result
    assert email in result["message"]
    assert activity_name in result["message"]

    # Verify the student was added to participants
    assert email in activities[activity_name]["participants"]


def test_signup_already_signed_up(client):
    """Test signup fails when student is already signed up."""
    email = "michael@mergington.edu"  # Already in Chess Club
    activity_name = "Chess Club"

    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 400
    result = response.json()
    assert "detail" in result
    assert "already signed up" in result["detail"]


def test_signup_activity_not_found(client):
    """Test signup fails for non-existent activity."""
    email = "test@mergington.edu"
    activity_name = "Nonexistent Activity"

    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 404
    result = response.json()
    assert "detail" in result
    assert "Activity not found" in result["detail"]


def test_unregister_success(client):
    """Test successful unregistration from an activity."""
    email = "michael@mergington.edu"
    activity_name = "Chess Club"

    # Verify student is initially signed up
    assert email in activities[activity_name]["participants"]

    response = client.delete(f"/activities/{activity_name}/participants?email={email}")
    assert response.status_code == 200
    result = response.json()
    assert "message" in result
    assert email in result["message"]
    assert activity_name in result["message"]

    # Verify the student was removed from participants
    assert email not in activities[activity_name]["participants"]


def test_unregister_not_signed_up(client):
    """Test unregister fails when student is not signed up."""
    email = "notsigned@mergington.edu"
    activity_name = "Chess Club"

    response = client.delete(f"/activities/{activity_name}/participants?email={email}")
    assert response.status_code == 404
    result = response.json()
    assert "detail" in result
    assert "not registered" in result["detail"]


def test_unregister_activity_not_found(client):
    """Test unregister fails for non-existent activity."""
    email = "test@mergington.edu"
    activity_name = "Nonexistent Activity"

    response = client.delete(f"/activities/{activity_name}/participants?email={email}")
    assert response.status_code == 404
    result = response.json()
    assert "detail" in result
    assert "Activity not found" in result["detail"]


def test_root_redirect(client):
    """Test root endpoint redirects to static HTML."""
    response = client.get("/")
    assert response.status_code == 307  # Temporary redirect
    assert response.headers["location"] == "/static/index.html"