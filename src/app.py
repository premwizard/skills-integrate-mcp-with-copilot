"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path
import sqlite3
import os

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

DB_PATH = Path(__file__).resolve().parents[1] / "activities.db"
DEFAULT_ACTIVITIES = {
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


def get_db_connection():
    connection = sqlite3.connect(DB_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_db_connection()
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS activities (
                name TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                schedule TEXT NOT NULL,
                max_participants INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_name TEXT NOT NULL,
                email TEXT NOT NULL,
                UNIQUE(activity_name, email),
                FOREIGN KEY(activity_name) REFERENCES activities(name) ON DELETE CASCADE
            )
            """
        )

        total = conn.execute("SELECT COUNT(*) as count FROM activities").fetchone()["count"]
        if total == 0:
            for name, details in DEFAULT_ACTIVITIES.items():
                conn.execute(
                    "INSERT INTO activities (name, description, schedule, max_participants) VALUES (?, ?, ?, ?)",
                    (name, details["description"], details["schedule"], details["max_participants"]),
                )
                for email in details["participants"]:
                    conn.execute(
                        "INSERT INTO participants (activity_name, email) VALUES (?, ?)",
                        (name, email),
                    )

    conn.close()


def fetch_activities() -> dict:
    conn = get_db_connection()
    activities = {}
    activity_rows = conn.execute("SELECT name, description, schedule, max_participants FROM activities").fetchall()
    for row in activity_rows:
        participants = [p["email"] for p in conn.execute(
            "SELECT email FROM participants WHERE activity_name = ? ORDER BY id",
            (row["name"],),
        ).fetchall()]
        activities[row["name"]] = {
            "description": row["description"],
            "schedule": row["schedule"],
            "max_participants": row["max_participants"],
            "participants": participants,
        }
    conn.close()
    return activities


@app.on_event("startup")
def on_startup() -> None:
    initialize_database()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return fetch_activities()


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    conn = get_db_connection()
    activity = conn.execute(
        "SELECT name, max_participants FROM activities WHERE name = ?",
        (activity_name,),
    ).fetchone()
    if activity is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Activity not found")

    existing_participant = conn.execute(
        "SELECT email FROM participants WHERE activity_name = ? AND email = ?",
        (activity_name, email),
    ).fetchone()
    if existing_participant is not None:
        conn.close()
        raise HTTPException(status_code=400, detail="Student is already signed up")

    current_count = conn.execute(
        "SELECT COUNT(*) as count FROM participants WHERE activity_name = ?",
        (activity_name,),
    ).fetchone()["count"]
    if current_count >= activity["max_participants"]:
        conn.close()
        raise HTTPException(status_code=400, detail="Activity is full")

    conn.execute(
        "INSERT INTO participants (activity_name, email) VALUES (?, ?)",
        (activity_name, email),
    )
    conn.commit()
    conn.close()
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    conn = get_db_connection()
    activity = conn.execute(
        "SELECT name FROM activities WHERE name = ?",
        (activity_name,),
    ).fetchone()
    if activity is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Activity not found")

    deleted = conn.execute(
        "DELETE FROM participants WHERE activity_name = ? AND email = ?",
        (activity_name, email),
    ).rowcount
    conn.commit()
    conn.close()

    if deleted == 0:
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

    return {"message": f"Unregistered {email} from {activity_name}"}


@app.post("/admin/activities")
def create_activity(activity: dict):
    if not activity.get("name") or not activity.get("description") or not activity.get("schedule"):
        raise HTTPException(status_code=400, detail="Activity name, description, and schedule are required")

    try:
        max_participants = int(activity.get("max_participants", 10))
    except ValueError:
        raise HTTPException(status_code=400, detail="max_participants must be an integer")

    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO activities (name, description, schedule, max_participants) VALUES (?, ?, ?, ?)",
            (activity["name"], activity["description"], activity["schedule"], max_participants),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Activity already exists")
    conn.close()
    return {"message": f"Created activity {activity['name']}"}


@app.delete("/admin/activities/{activity_name}")
def delete_activity(activity_name: str):
    conn = get_db_connection()
    activity = conn.execute(
        "SELECT name FROM activities WHERE name = ?",
        (activity_name,),
    ).fetchone()
    if activity is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Activity not found")

    conn.execute(
        "DELETE FROM activities WHERE name = ?",
        (activity_name,),
    )
    conn.commit()
    conn.close()
    return {"message": f"Deleted activity {activity_name}"}
