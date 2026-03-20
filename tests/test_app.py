import copy
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add src to path for test discovery/imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from app import app, activities  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


def test_get_activities_returns_initial_data():
    # Arrange
    # (no setup needed for default data)

    # Act
    response = client.get("/activities")
    payload = response.json()

    # Assert
    assert response.status_code == 200
    assert "Chess Club" in payload
    assert "Programming Class" in payload
    assert "Gym Class" in payload


def test_signup_new_student_success():
    # Arrange
    email = "newstudent@mergington.edu"

    # Act
    response = client.post("/activities/Chess%20Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for Chess Club"

    # Act: fetch latest state
    updated = client.get("/activities").json()
    assert email in updated["Chess Club"]["participants"]


def test_signup_duplicate_student_fails():
    # Arrange
    existing = "michael@mergington.edu"

    # Act
    response = client.post("/activities/Chess%20Club/signup", params={"email": existing})

    # Assert
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"].lower()


def test_signup_activity_full_fails():
    # Arrange
    activities["Chess Club"]["max_participants"] = len(activities["Chess Club"]["participants"])

    # Act
    response = client.post("/activities/Chess%20Club/signup", params={"email": "another@mergington.edu"})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_delete_participant_success():
    # Arrange
    email = "michael@mergington.edu"

    # Act
    response = client.delete(f"/activities/Chess%20Club/participants/{email}")

    # Assert
    assert response.status_code == 200
    assert "Removed" in response.json()["message"]

    # Act: fetch latest state
    updated = client.get("/activities").json()
    assert email not in updated["Chess Club"]["participants"]


def test_delete_nonexistent_participant_returns_404():
    # Arrange
    invalid_email = "doesnotexist@mergington.edu"

    # Act
    response = client.delete(f"/activities/Chess%20Club/participants/{invalid_email}")

    # Assert
    assert response.status_code == 404
    assert "Participant not found" in response.json()["detail"]
