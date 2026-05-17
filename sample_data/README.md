# Sample Meeting Data

A 3-week dataset for NovaTech Inc. (fictional company) designed to showcase every component of the analysis.

## How to use

1. Go to **Settings** in the dashboard
2. Upload `sample_meetings.csv`
3. Click **Preview Meetings** — you'll see 18 meetings listed
4. For meetings 1, 2, 9, 12, 16 — click the upload button in the TRANSCRIPT column and upload the corresponding `.txt` files
5. Set your hourly rate and weights, then click **Analyze**

## What the data demonstrates

| Feature | Which meetings |
|---------|---------------|
| **Cascade Chain 1** | Meeting 0 (Weekly Status Update, no decisions) → spawns meetings 2, 3, 4 within 72hr |
| **Cascade Chain 2** | Meeting 6 (Mobile App Design Review, no decisions) → spawns meetings 7, 8 within 24hr |
| **High-value meetings** | Meetings 1, 9, 16 (clear decisions, good transcripts) |
| **Recurring staleness** | Meetings 0, 10, 13 (recurring with no outcomes) |
| **1:1 meetings** | Meetings 5, 11 (healthy, low waste) |
| **Overloaded person** | sarah.chen@novatech.io attends 16 of 18 meetings |
| **Planning meeting** | Meeting 9 (Q3 Planning Workshop, 2hr, all hands, clear OKRs) |
| **Brainstorm waste** | Meeting 17 (2hr unstructured brainstorm with no notes) |

## Transcript files

| File | Meeting index | Meeting name |
|------|--------------|-------------|
| transcript_1.txt | 1 | Q2 Budget Planning |
| transcript_2.txt | 2 | Engineering Standup |
| transcript_9.txt | 9 | Q3 Planning Workshop |
| transcript_12.txt | 12 | Sprint Retrospective |
| transcript_16.txt | 16 | Sprint Demo |

## Cascade chain design

Cascade chains require:
- Origin meeting: decision_deficit > 0.80 (achieved by having NO notes and NO transcript with decisions)
- Follow-up meeting: within 72 hours AND >40% attendee overlap with origin

Meetings 0, 6, and 13 have no notes and no transcripts to maximize their decision deficit.
