from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as api


@pytest.fixture(autouse=True)
def isolate_activities(monkeypatch):
    monkeypatch.setattr(api, "activities", deepcopy(api.activities))


@pytest.fixture
def client():
    with TestClient(api.app) as test_client:
        yield test_client


def test_root_redirects_to_activity_page(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_data(client):
    # Arrange
    expected_activities = deepcopy(api.activities)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_participant_and_updates_activity_listing(client):
    # Arrange
    activity = "Chess Club"
    email = "new.student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email},
    )
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity}"}
    assert email in activities_response.json()[activity]["participants"]


def test_signup_returns_not_found_for_unknown_activity(client):
    # Arrange
    email = "new.student@mergington.edu"

    # Act
    response = client.post("/activities/Unknown%20Activity/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity = "Chess Club"
    email = api.activities[activity]["participants"][0]

    # Act
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up"


def test_unregister_removes_participant_and_updates_activity_listing(client):
    # Arrange
    activity = "Chess Club"
    email = api.activities[activity]["participants"][0]

    # Act
    response = client.delete(
        f"/activities/{activity}/participants",
        params={"email": email},
    )
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity}"}
    assert email not in activities_response.json()[activity]["participants"]


def test_unregister_returns_not_found_for_unknown_activity(client):
    # Arrange
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        "/activities/Unknown%20Activity/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_not_found_for_unsigned_participant(client):
    # Arrange
    activity = "Chess Club"
    email = "not.signed.up@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up"
