# Meetrix — AI-Powered Meeting Intelligence

> *Stop letting bad meetings steal your team's time.*

Meetrix analyses your calendar data to quantify exactly how much meeting waste is costing your organisation, identify the meetings that trigger costly follow-up chains, and surface the people drowning in back-to-back bookings — all running **100% locally** with no data leaving your machine.

---

## The Problem

The average knowledge worker spends **31 hours per month** in unproductive meetings. Most organisations have no visibility into which meetings are generating value and which are silently burning through payroll. There is no easy way to answer:

- Which recurring meetings have outlived their purpose?
- Why does our team keep scheduling follow-up meetings for the same topic?
- Who is so meeting-heavy they have no time for deep work?
- What decisions actually came out of last week's sessions?

Meetrix answers all of these with a single CSV upload.

---

## What Meetrix Does

Upload your calendar export (Google Calendar, Outlook, or any standard format) and within minutes you get:

| Output | What It Tells You |
|--------|------------------|
| **Waste Score (0–100%)** | A composite score per meeting combining salary cost, missing decisions, unbalanced participation, and recurring staleness |
| **Cascade Chain Detection** | Meetings that ended without decisions and spawned follow-up meetings within 72 hours with the same group — the #1 source of meeting bloat |
| **Focus Time Analysis** | Per-person breakdown of how much of their working day is consumed by meetings vs. available for deep work |
| **AI Recommendations** | Specific, meeting-level actions: cancel, shorten, restructure, or keep — with reasoning tied to the meeting's actual pattern |
| **ROI Projection** | Estimated annual savings if the top recommendations are acted on |
| **Ask Meetrix** | Natural-language Q&A over your own data — "What did Sarah decide in the Q3 planning session?" |

---

## Architecture

Meetrix is built as a **5-node LangGraph pipeline** that runs deterministic analysis first and uses an LLM for only two targeted tasks — keeping it fast, predictable, and privacy-safe.

```
CSV Upload
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    5-Node Analysis Pipeline                      │
│                                                                  │
│  [1] INGEST        Parse CSV, validate emails, match transcripts │
│         │                                                        │
│  [2] ANALYZE       All deterministic maths — no LLM             │
│         │          • classify meeting type (heuristic rules)     │
│         │          • compute salary cost per meeting             │
│         │          • waste score (cost + decisions + parti. +    │
│         │            recurrence staleness)                       │
│         │          • focus time per person                       │
│         │          • health score (agenda, duration, fit)        │
│         │          • cascade chain detection                     │
│         │          • co-occurrence network graph                 │
│         │          • recommendations + ROI                       │
│         │                                                        │
│  [3] EXTRACT  ◄──── LLM CALL 1: extract action items +          │
│         │           decisions from notes / transcripts           │
│         │           → re-scores waste with real decision data    │
│         │                                                        │
│  [4] SYNTHESIZE ◄── LLM CALL 2: generate executive report       │
│         │           from compact analysis summary                │
│         │                                                        │
│  [5] SAVE          Write everything to local SQLite             │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
    React Dashboard  ←→  Ask Meetrix (separate LangGraph interaction graph)
```

### Why only 2 LLM calls?

Most analysis is mathematics — cost ratios, overlap percentages, time gaps. LLMs are reserved for tasks that genuinely need language understanding: extracting decisions from free-text transcripts, and writing an executive summary. This keeps the pipeline fast (< 60 s on typical datasets) and the results auditable.

### The Interaction Graph

A second, stateless LangGraph handles natural-language queries after analysis completes. It builds a rich context from the database (meetings, costs, focus scores, action items, cascade chains, anomalies, and full transcript text) and passes it to the LLM in a single call. This is what powers **Ask Meetrix**.

---

## Waste Score Formula

Each meeting is scored on four dimensions, weighted and summed into a composite:

```
Waste = (Cost Factor × 0.25)
      + (Decision Deficit × 0.40)
      + (Participation Imbalance × 0.20)
      + (Recurrence Staleness × 0.15)
```

| Dimension | What It Measures |
|-----------|-----------------|
| **Cost Factor** | Salary cost relative to the most expensive meeting in the dataset |
| **Decision Deficit** | How few decisions were recorded — reduced by keywords like "decided", "agreed", "action:" in notes or transcripts |
| **Participation Imbalance** | How over-attended the meeting was relative to its type norm |
| **Recurrence Staleness** | For recurring series: age + attendance drop over time |

Categories: **High Waste ≥ 50%** · **Medium Waste ≥ 30%** · **Low Waste ≥ 15%** · **High Value < 15%**

---

## Cascade Chain Detection

A cascade chain is triggered when:
1. A meeting ends with **Decision Deficit > 0.80** (no decisions recorded)
2. A follow-up meeting is booked **within 72 hours**
3. The follow-up has **> 40% attendee overlap** with the original

Origin meetings must have ≥ 3 attendees and be ≥ 20 minutes to avoid false positives from standups and 1:1s.

---

## Dashboard Pages

| Page | Purpose |
|------|---------|
| **Overview** | KPI summary — total cost, avg waste, overloaded people, cascade chains, Meetrix Score |
| **Meetings** | Full sortable table with expandable waste breakdowns and AI recommendations |
| **People** | Per-person focus time, meeting hours, and overload flags |
| **Health** | Meeting hygiene metrics — agenda presence, duration fit, attendee fit |
| **Network** | Interactive D3 force graph — drag nodes, zoom/pan, hover for metrics |
| **Trends** | Waste distribution chart, meeting hours by person, ROI projection |
| **Reports** | Executive briefing + key findings — copy as Markdown or plain text |
| **Ask** | Natural-language Q&A over your analysis data |
| **Schedule** | Smart meeting scheduler using your team's load data *(in development)* |

---

## Tech Stack

**Backend** — Python 3.11, FastAPI, LangGraph, LangChain, Ollama (local LLM), SQLite, aiosqlite

**Frontend** — React 18, TypeScript, Vite, Tailwind CSS, D3.js, Recharts

**Infrastructure** — Docker Compose (single command startup), no external API calls

---

## Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [Ollama](https://ollama.com) installed with `llama3.2` pulled:

```bash
ollama pull llama3.2
```

### Start the application

```bash
git clone <repo-url>
cd generatedcode
docker compose up --build
```

That's it. The dashboard opens at **http://localhost:5173**.  
The backend API runs at **http://localhost:8000**.

> **Note for Linux users:** Ollama must be running on the host. The backend connects to it via `host.docker.internal`. On Linux, the `docker-compose.yml` already includes the `extra_hosts` mapping to make this work.

### Run your first analysis

1. Open **Settings** in the sidebar
2. Upload a CSV file (see format below, or use `sample_data/sample_meetings.csv`)
3. Optionally attach `.txt` transcripts to specific meetings
4. Set your team's average hourly rate and adjust the waste score weights if needed
5. Click **Analyze** and watch the pipeline run live

### CSV format

Required columns: `title`, `start`, `end`, `attendees`

```csv
title,start,end,attendees,organizer,recurring,notes
Weekly Standup,2026-05-05T09:00:00,2026-05-05T09:15:00,"alice@co.com,bob@co.com",alice@co.com,true,
Q3 Planning,2026-05-06T14:00:00,2026-05-06T16:00:00,"alice@co.com,bob@co.com,carol@co.com",alice@co.com,false,"Decided: ship v2 by August. Action: Bob to draft spec."
```

Column names are flexible — `subject`, `participants`, `begin`, `from`, `host` etc. are all recognised.

### Sample dataset

`sample_data/sample_meetings.csv` contains 18 meetings for a fictional team (NovaTech Inc.) designed to demonstrate every feature:

- Two cascade chains
- One clearly overloaded person (Sarah Chen, 19 h of meetings)
- High Waste / Medium Waste / Low Waste / High Value spread
- Five matching transcript files (`transcript_1.txt`, `_2.txt`, `_9.txt`, `_12.txt`, `_16.txt`)

See `sample_data/README.md` for the transcript-to-meeting index mapping.

---

## Configuration

All weights and thresholds are adjustable in the Settings page before each analysis run. Defaults are stored in `backend/app/config.py`:

```python
DEFAULT_HOURLY_RATE = 75.0   # $/hr — average fully-loaded employee cost
WEIGHT_COST         = 0.25
WEIGHT_DECISION     = 0.40   # Highest weight — decisions are the #1 indicator of meeting value
WEIGHT_PARTICIPATION = 0.20
WEIGHT_RECURRENCE   = 0.15
```

Override any value via environment variable (e.g. `WEIGHT_DECISION=0.50` in `backend/.env`).

---

## Privacy

**All data stays on your machine.**

- The LLM runs locally via Ollama — no OpenAI, no Anthropic, no cloud API
- Meeting data is stored in a local SQLite file (`backend/data/meetrix.db`)
- No telemetry, no analytics, no external network calls

---

## Project Structure

```
generatedcode/
├── backend/
│   ├── app/
│   │   ├── api/v1/routes.py          # FastAPI endpoints
│   │   ├── graph/
│   │   │   ├── analysis_builder.py   # 5-node LangGraph pipeline
│   │   │   ├── interaction_builder.py # Ask Meetrix graph
│   │   │   ├── nodes/
│   │   │   │   ├── tools.py          # All deterministic analysis functions
│   │   │   │   └── llm_nodes.py      # The 2 LLM calls
│   │   │   └── state.py              # TypedDict state definitions
│   │   ├── models/schemas.py         # Pydantic models
│   │   ├── utils/csv_parser.py       # Flexible CSV ingestion
│   │   └── config.py                 # All tunable parameters
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/                    # One file per dashboard page
│       ├── components/ui/            # Reusable UI primitives
│       └── types/api.ts              # TypeScript types mirroring backend schemas
└── sample_data/                      # Demo dataset for NovaTech Inc.
```

---

*Built with ♥ and way too many meetings.*