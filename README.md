# Meetrix — Intelligent Meeting OS

> **Reclaim your team's time. Understand. Optimize. Execute.**

Meetrix transforms your chaotic meeting calendar into clear, actionable intelligence. It quantifies exactly how much time and money meetings are costing your team, identifies wasteful patterns, detects costly meeting cascades, and delivers powerful insights — **all running 100% locally** with zero data leaving your machine.

![Meetrix Upload Screen](screenshots/Screenshot%201.png)

---

## The Problem

Knowledge workers spend **15+ hours per week** in meetings, yet most teams lack visibility into which meetings create real value versus which ones multiply waste, delay decisions, and destroy focus time.

Meetrix turns raw calendar data into strategic intelligence.

---

## Key Features

### 📊 Core Intelligence
- **Meetrix Score** — Overall team meeting health (0–100)
- **Waste Score** per meeting using four weighted dimensions:
  - Cost Factor (salary cost)
  - Decision Deficit (were real decisions made?)
  - Participation Imbalance (too many people?)
  - Recurrence Staleness (has this meeting outlived its purpose?)
- **Cascade Chain Detection** — Automatically identifies meetings that spawn expensive follow-up chains
- **Meeting Health Score** — Evaluates agenda quality, duration fit, and attendee appropriateness

### 👥 People & Network Insights
- Identifies overloaded team members and fragmented focus time
- Interactive **Meeting Network Graph** showing collaboration patterns
- Most central people and highest-cost collaboration pairs

### 🧠 Ask Meetrix
Natural language AI assistant over your own meeting data:
- “Which meetings cost the most?”
- “What did Sarah say in the last meeting?”
- “Summarize decisions from the Q3 Planning Workshop”

### 📈 Actionable Outputs
- Prioritized recommendations (Shorten, Restructure, Cancel)
- Projected annual ROI and savings
- Professional executive reports (export as Markdown or Plain Text)
- Trends, waste distribution, and focus time analysis

### 🔒 Privacy-First
- Runs entirely locally via **Ollama**
- All data stored in local SQLite
- No cloud services • No external APIs • No telemetry

---

## Screenshots

| Upload Calendar | Attach Transcripts | Overview |
|-----------------|---------------------|----------|
| ![Upload CSV](screenshots/Screenshot%201.png) | ![Transcript Upload](screenshots/screenshot%202.png) | ![Overview](screenshots/screenshot%203.png) |

| Meetings | Ask Meetrix | People & Focus Time |
|----------|-------------|---------------------|
| ![Meetings](screenshots/screenshot%205.png) | ![Ask](screenshots/screenshot%204.png) | ![People](screenshots/screenshot%206.png) |

| Network Graph | Health | Trends |
|---------------|--------|--------|
| ![Network](screenshots/screenshot%207.png) | ![Health](screenshots/screenshot%208.png) | ![Trends](screenshots/screenshot%209.png) |

---

## How It Works

### 1. Upload Your Calendar
- Go to **Upload Data**
- Drop your meeting calendar export (`.csv`) from Google Calendar, Outlook, or any standard calendar app

![Upload Screen](screenshots/Screenshot%201.png)

### 2. Attach Transcripts (Optional but Recommended)
After uploading the CSV, Meetrix shows all detected meetings. You can:
- Attach individual **`.txt` transcript files** to specific meetings
- This enables deep extraction of decisions, action items, and discussion quality

![Transcript Upload & Config](screenshots/screenshot%202.png)

### 3. Run Analysis
Configure hourly rate and waste weights, then click **Analyze** to get full insights.

---

## Transcript Support

Meetrix has **first-class support for meeting transcripts**:

- Upload `.txt` files for any meeting
- The AI extracts real **decisions**, **action items**, and **outcomes**
- This significantly improves **Decision Deficit** scoring and recommendation quality
- Sample transcripts are included in the `sample_data/` folder (`transcript_1.txt`, `transcript_2.txt`, `transcript_9.txt`, etc.)

**Example Transcript** (`sample_data/transcript_1.txt`):

```txt
Meeting: Weekly Status Update
Date: May 5, 2026 | Duration: 60 minutes
Attendees: Diana Ross, Priya Patel, Sarah Chen, Marcus Johnson

Diana: Let's do a quick round-robin.

Sarah: Marketing campaign is on track at 87% of target.
Marcus: Engineering is blocked on API v2 migration. We need a decision on priority.
Priya: Product wants to move Q3 planning to next week.

Diana: Marcus, follow up with the infra team. Sarah, share updated metrics by Thursday.
We'll discuss Q3 priorities separately.

Action Items:
• Marcus: Resolve API migration blocker
• Sarah: Send campaign metrics
• Team: Review investor pitch deck by EOD Thursday
