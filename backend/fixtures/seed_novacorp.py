"""Seed database with NovaCorp demo dataset.

This script creates a realistic 90-day meeting dataset for a fictional company
with 50 employees across 5 departments. Includes various meeting patterns:
- Regular standups and syncs
- Strategic planning sessions
- Cross-functional collaboration
- 1:1s and skip-levels
- All-hands and town halls
- Wasteful patterns: status updates, FYI meetings, over-attendance
"""
import asyncio
import csv
import json
import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

import aiosqlite

# Database path
DB_PATH = Path(os.environ.get("DATABASE_PATH", "/app/data/meetrix.db"))

# NovaCorp organizational structure
DEPARTMENTS = {
    "Engineering": ["Alice Chen", "Bob Smith", "Carol Wang", "David Lee", "Emma Brown", 
                    "Frank Miller", "Grace Kim", "Henry Davis", "Iris Johnson", "Jack Wilson"],
    "Product": ["Kate Martinez", "Liam Anderson", "Maya Patel", "Noah Taylor", "Olivia White",
                "Paul Garcia", "Quinn Rodriguez", "Rachel Green", "Sam Thompson", "Tina Lopez"],
    "Sales": ["Uma Singh", "Victor Chen", "Wendy Park", "Xavier Brown", "Yuki Tanaka",
              "Zara Ahmed", "Aaron Scott", "Bella Martinez", "Carlos Rivera", "Diana Foster"],
    "Marketing": ["Ethan Cooper", "Fiona Bell", "George Hayes", "Hannah Price", "Ian Murphy",
                  "Julia Ward", "Kevin Ross", "Laura Bennett", "Mike Coleman", "Nina Gray"],
    "Operations": ["Oscar Reed", "Penny Brooks", "Quincy Powell", "Ruby Sanders", "Steve Hughes",
                   "Tara Jenkins", "Umar Perry", "Vera Long", "Wade Butler", "Xena Barnes"],
}

ALL_EMPLOYEES = [name for dept in DEPARTMENTS.values() for name in dept]

# Meeting templates with realistic patterns
MEETING_TEMPLATES = [
    # Regular syncs (high frequency, often wasteful)
    {
        "subject": "Daily Standup - {dept}",
        "duration": 15,
        "frequency": "daily",
        "attendees": lambda dept: DEPARTMENTS[dept][:5],
        "waste_probability": 0.3,
    },
    {
        "subject": "Weekly Team Sync - {dept}",
        "duration": 60,
        "frequency": "weekly",
        "attendees": lambda dept: DEPARTMENTS[dept],
        "waste_probability": 0.4,
    },
    # Strategic meetings (valuable)
    {
        "subject": "Product Roadmap Planning",
        "duration": 120,
        "frequency": "biweekly",
        "attendees": lambda dept: DEPARTMENTS["Product"] + DEPARTMENTS["Engineering"][:3],
        "waste_probability": 0.1,
    },
    {
        "subject": "Quarterly Business Review",
        "duration": 180,
        "frequency": "quarterly",
        "attendees": lambda dept: [ALL_EMPLOYEES[i] for i in range(0, 50, 5)],
        "waste_probability": 0.05,
    },
    # Cross-functional (mixed value)
    {
        "subject": "Sales & Engineering Alignment",
        "duration": 45,
        "frequency": "weekly",
        "attendees": lambda dept: DEPARTMENTS["Sales"][:3] + DEPARTMENTS["Engineering"][:3],
        "waste_probability": 0.5,
    },
    {
        "subject": "Marketing Campaign Review",
        "duration": 60,
        "frequency": "weekly",
        "attendees": lambda dept: DEPARTMENTS["Marketing"] + DEPARTMENTS["Product"][:2],
        "waste_probability": 0.3,
    },
    # 1:1s (valuable)
    {
        "subject": "1:1 - Manager Check-in",
        "duration": 30,
        "frequency": "weekly",
        "attendees": lambda dept: random.sample(DEPARTMENTS[dept], 2),
        "waste_probability": 0.1,
    },
    # All-hands (mixed)
    {
        "subject": "All-Hands Meeting",
        "duration": 60,
        "frequency": "monthly",
        "attendees": lambda dept: ALL_EMPLOYEES,
        "waste_probability": 0.2,
    },
    # Status updates (wasteful)
    {
        "subject": "Status Update - {dept}",
        "duration": 30,
        "frequency": "weekly",
        "attendees": lambda dept: DEPARTMENTS[dept][:6],
        "waste_probability": 0.8,
    },
    # FYI meetings (wasteful)
    {
        "subject": "FYI: Project Update",
        "duration": 45,
        "frequency": "biweekly",
        "attendees": lambda dept: random.sample(ALL_EMPLOYEES, 8),
        "waste_probability": 0.9,
    },
]


def generate_meetings(start_date: datetime, days: int = 90) -> list[dict]:
    """Generate realistic meeting dataset."""
    meetings = []
    current_date = start_date

    for day in range(days):
        # Skip weekends
        if current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue

        # Generate meetings for this day
        for template in MEETING_TEMPLATES:
            # Check if meeting should occur today based on frequency
            should_occur = False
            if template["frequency"] == "daily":
                should_occur = True
            elif template["frequency"] == "weekly" and current_date.weekday() == 1:  # Tuesday
                should_occur = True
            elif template["frequency"] == "biweekly" and current_date.weekday() == 2 and day % 14 == 0:
                should_occur = True
            elif template["frequency"] == "monthly" and current_date.day == 15:
                should_occur = True
            elif template["frequency"] == "quarterly" and current_date.day == 1 and current_date.month % 3 == 1:
                should_occur = True

            if not should_occur:
                continue

            # Select department for this meeting
            dept = random.choice(list(DEPARTMENTS.keys()))
            
            # Generate meeting
            subject = template["subject"].format(dept=dept)
            attendees = template["attendees"](dept)
            organizer = attendees[0]
            
            # Add some randomness to duration
            duration = template["duration"] + random.randint(-5, 10)
            
            # Random start time during work hours (9 AM - 5 PM)
            start_hour = random.randint(9, 16)
            start_minute = random.choice([0, 15, 30, 45])
            start_time = current_date.replace(hour=start_hour, minute=start_minute, second=0)
            end_time = start_time + timedelta(minutes=duration)
            
            # Determine if this is a wasteful meeting
            is_wasteful = random.random() < template["waste_probability"]
            
            meeting = {
                "subject": subject,
                "organizer": organizer,
                "required_attendees": ";".join(attendees),
                "optional_attendees": "",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_minutes": duration,
                "location": "Conference Room" if len(attendees) > 5 else "Virtual",
                "is_recurring": template["frequency"] != "quarterly",
                "recurrence_pattern": template["frequency"],
                "response_status": "Accepted",
                "is_wasteful": is_wasteful,
            }
            
            meetings.append(meeting)

        current_date += timedelta(days=1)

    return meetings


async def seed_novacorp_data():
    """Seed database with NovaCorp dataset."""
    print("Generating NovaCorp meeting dataset...")
    
    # Generate 90 days of meetings starting from 3 months ago
    start_date = datetime.now() - timedelta(days=90)
    meetings = generate_meetings(start_date, days=90)
    
    print(f"Generated {len(meetings)} meetings")
    
    # Write to CSV
    csv_path = Path(__file__).parent / "novacorp_meetings.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=meetings[0].keys())
        writer.writeheader()
        writer.writerows(meetings)
    
    print(f"Wrote CSV to {csv_path}")
    
    # Insert into database
    print("Inserting into database...")
    demo_session_id = "novacorp-demo-session"
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Create demo session first (FK requirement)
        await db.execute(
            "INSERT OR REPLACE INTO sessions (session_id, status) VALUES (?, 'complete')",
            (demo_session_id,),
        )
        await db.commit()
        
        # Clear existing meetings for this session
        await db.execute("DELETE FROM meetings WHERE session_id = ?", (demo_session_id,))
        await db.commit()
        
        # Insert meetings
        for meeting in meetings:
            # Convert attendee names to email format
            attendees = [
                f"{name.lower().replace(' ', '.')}@novacorp.com"
                for name in meeting["required_attendees"].split(";")
                if name.strip()
            ]
            organizer_email = f"{meeting['organizer'].lower().replace(' ', '.')}@novacorp.com"
            
            await db.execute(
                """INSERT INTO meetings
                   (meeting_id, session_id, title, start_datetime, end_datetime,
                    duration_minutes, attendee_emails, organizer_email,
                    is_recurring, recurrence_rule, meeting_type, notes_text)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid4()),
                    demo_session_id,
                    meeting["subject"],
                    meeting["start_time"],
                    meeting["end_time"],
                    meeting["duration_minutes"],
                    json.dumps(attendees),
                    organizer_email,
                    meeting["is_recurring"],
                    meeting["recurrence_pattern"],
                    None,
                    None,
                ),
            )
        
        await db.commit()
    
    print(f"Seeded {len(meetings)} meetings into database")
    print("\nDataset summary:")
    print(f"  Date range: {start_date.date()} to {(start_date + timedelta(days=90)).date()}")
    print(f"  Employees: {len(ALL_EMPLOYEES)}")
    print(f"  Departments: {len(DEPARTMENTS)}")
    print(f"  Total meetings: {len(meetings)}")
    print(f"  Wasteful meetings: {sum(1 for m in meetings if m['is_wasteful'])}")
    print(f"  Average duration: {sum(m['duration_minutes'] for m in meetings) / len(meetings):.1f} minutes")


if __name__ == "__main__":
    asyncio.run(seed_novacorp_data())

# Made with Bob
