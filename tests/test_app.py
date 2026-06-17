from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    # Arrange: snapshot mutable in-memory state before each test.
    original_activities = deepcopy(activities)

    with TestClient(app) as test_client:
        # Act: yield a configured client to the test.
        yield test_client

    # Assert: restore original activity state after each test.
    activities.clear()
    activities.update(original_activities)


def test_get_activities_returns_all_activities(client):
    # Arrange
    expected_keys = set(activities.keys())

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, dict)
    assert set(payload.keys()) == expected_keys


def test_signup_adds_participant_successfully(client):
    # Arrange
    activity_name = "Chess Club"
    new_email = "new.student@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": new_email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {new_email} for {activity_name}"}
    assert new_email in activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity_name = "Chess Club"
    existing_email = "michael@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": existing_email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}


def test_signup_returns_not_found_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"
    email = "someone@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_participant_successfully(client):
    # Arrange
    activity_name = "Chess Club"
    existing_email = "michael@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": existing_email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {existing_email} from {activity_name}"}
    assert existing_email not in activities[activity_name]["participants"]


def test_unregister_returns_not_found_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"
    email = "someone@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_returns_not_found_for_non_registered_student(client):
    # Arrange
    activity_name = "Chess Club"
    email = "not.registered@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up for this activity"}
