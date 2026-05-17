# Meetrix — Intelligent Meeting OS

> **Reclaim your team's time. Understand. Optimize. Execute.**

Meetrix transforms your chaotic meeting calendar into clear, actionable intelligence. It quantifies exactly how much time and money meetings are costing your team, identifies wasteful patterns, detects costly meeting cascades, and delivers powerful insights — **all running 100% locally** with zero data leaving your machine.

![Meetrix Overview](screenshots/screenshot%203.png)

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

| Overview | Meetings | Ask Meetrix |
|----------|----------|-------------|
| ![Overview](screenshots/screenshot%203.png) | ![Meetings](screenshots/screenshot%205.png) | ![Ask](screenshots/screenshot%204.png) |

| People & Focus Time | Network Graph | Health |
|---------------------|---------------|--------|
| ![People](screenshots/screenshot%206.png) | ![Network](screenshots/screenshot%207.png) | ![Health](screenshots/screenshot%208.png) |

---

## Tech Stack

- **Backend**: Python + FastAPI + LangGraph + Ollama + SQLite
- **Frontend**: React 18 + TypeScript + Tailwind CSS + D3.js
- **Architecture**: Deterministic 5-node analysis pipeline with targeted LLM calls only when necessary

---

## Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Ollama](https://ollama.com)

```bash
ollama pull llama3.2
