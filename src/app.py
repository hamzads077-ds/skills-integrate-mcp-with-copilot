"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}

# Registration and notification state
registration_statuses = {}
notifications = {}
notification_preferences = {}
last_transition = {}


STATUS_NEXT_STEPS = {
    "confirmed": "Prepare to attend and check the activity schedule.",
    "waitlist": "Your place is on the waitlist. We will notify you if a spot opens.",
    "rejected": "You can review other available activities and try registering again.",
    "cancelled": "No further action is needed. You may sign up again if there is availability.",
}


def transition_registration(activity_name: str, email: str, status: str):
    """Create one notification per registration status transition."""
    if status not in STATUS_NEXT_STEPS:
        raise HTTPException(status_code=400, detail="Invalid registration status")

    if last_transition.get((activity_name, email)) == status:
        return None

    previous_status = registration_statuses.get((activity_name, email))
    registration_statuses[(activity_name, email)] = status
    last_transition[(activity_name, email)] = status

    notification_id = f"{activity_name}:{email}:{status}"
    existing = notifications.get(notification_id)
    if existing:
        return existing

    channels = ["in_app"]
    if notification_preferences.get(email, False):
        channels.append("email")

    notification = {
        "id": notification_id,
        "email": email,
        "activity": activity_name,
        "status": status,
        "message": f"{activity_name} registration status changed from {previous_status or 'none'} to {status}.",
        "next_steps": STATUS_NEXT_STEPS[status],
        "channels": channels,
    }
    notifications[notification_id] = notification
    return notification


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.get("/notifications")
def get_notifications(email: str):
    return [
        notification
        for notification in notifications.values()
        if notification["email"] == email
    ]


@app.get("/notifications/preferences")
def get_notification_preferences(email: str):
    return {"email": notification_preferences.get(email, False)}


@app.put("/notifications/preferences")
def update_notification_preferences(email: str, email_enabled: bool):
    notification_preferences[email] = email_enabled
    return {"email": email_enabled}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Confirm immediately if there is capacity; otherwise place the student on a waitlist.
    if len(activity["participants"]) < activity["max_participants"]:
        activity["participants"].append(email)
        notification = transition_registration(activity_name, email, "confirmed")
        message = f"Signed up {email} for {activity_name}"
    else:
        notification = transition_registration(activity_name, email, "waitlist")
        message = f"{email} was added to the waitlist for {activity_name}"

    return {
        "message": message,
        "status": registration_statuses[(activity_name, email)],
        "notification": notification,
    }


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    notification = transition_registration(activity_name, email, "cancelled")
    return {
        "message": f"Unregistered {email} from {activity_name}",
        "status": "cancelled",
        "notification": notification,
    }


@app.patch("/activities/{activity_name}/registrations/{email}/status")
def update_registration_status(activity_name: str, email: str, status: str):
    """Update a student's registration outcome and notify them once."""
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity = activities[activity_name]
    if status in ("confirmed", "waitlist"):
        if status == "confirmed" and email not in activity["participants"]:
            if len(activity["participants"]) >= activity["max_participants"]:
                raise HTTPException(status_code=400, detail="Activity is full")
            activity["participants"].append(email)
        if status == "waitlist" and email in activity["participants"]:
            activity["participants"].remove(email)
    elif status == "rejected":
        if email in activity["participants"]:
            activity["participants"].remove(email)
    elif status == "cancelled":
        if email in activity["participants"]:
            activity["participants"].remove(email)

    notification = transition_registration(activity_name, email, status)
    return {
        "message": f"{email} registration status changed to {status}",
        "status": status,
        "notification": notification,
    }
