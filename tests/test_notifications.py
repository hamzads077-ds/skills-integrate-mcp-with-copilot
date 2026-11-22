from fastapi.testclient import TestClient

from src.app import app, activities, notifications, registration_statuses, last_transition, notification_preferences


client = TestClient(app)


def setup_function():
    notifications.clear()
    registration_statuses.clear()
    last_transition.clear()
    notification_preferences.clear()
    activities["Chess Club"]["participants"] = [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]
    activities["Chess Club"]["max_participants"] = 12


def test_status_change_creates_notification_and_suppresses_duplicate():
    response = client.patch(
        "/activities/Chess%20Club/registrations/student@example.edu/status",
        params={"status": "waitlist"},
    )
    assert response.status_code == 200
    assert response.json()["notification"]["status"] == "waitlist"

    repeated = client.patch(
        "/activities/Chess%20Club/registrations/student@example.edu/status",
        params={"status": "waitlist"},
    )
    assert repeated.status_code == 200
    assert repeated.json()["notification"] is None
    assert len(notifications) == 1


def test_email_preference_is_configurable():
    enabled = client.put(
        "/notifications/preferences",
        params={"email": "student@example.edu", "email_enabled": True},
    )
    assert enabled.json()["email"] is True

    response = client.patch(
        "/activities/Chess%20Club/registrations/student@example.edu/status",
        params={"status": "confirmed"},
    )
    assert "email" in response.json()["notification"]["channels"]


def test_signup_waitlists_when_activity_is_full():
    activities["Chess Club"]["participants"] = [
        "one@example.edu",
        "two@example.edu",
    ]
    activities["Chess Club"]["max_participants"] = 2

    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "waitlisted@example.edu"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "waitlist"
