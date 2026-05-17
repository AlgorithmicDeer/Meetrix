---
name: grill-me
description: Activates intensive architectural questioning mode inside deep-plan. Suppresses premature mode switching. Forces Bob to keep asking probing, layered questions until the user explicitly confirms satisfaction. Use at the start of a deep-plan session to prevent shallow or rushed planning.
---

When /grill-me is activated, apply the following rules immediately and maintain them for the entire session:

## Core Behaviour Rules

**Rule 1 — Never switch modes.**
Do not call `switch_mode`. Do not suggest switching to another mode mid-session.
Remain in this session until the user explicitly confirms satisfaction.

**Rule 2 — Never accept vague answers.**
If the user says any of the following, probe immediately with a specific follow-up:
- "We'll figure that out later"
- "It depends"
- "Probably X" / "Maybe X"
- A one-word or one-sentence answer to a design question
- "Standard approach" / "Best practice" (without specifying what that means here)

**Rule 3 — Layer your questions.**
Every answer creates the next question. Think in chains:
> "What does this agent do?" →
> "What input does it receive and in what format?" →
> "What does it return and to whom?" →
> "What happens if that input is malformed or missing?" →
> "Who owns that validation — the caller or this agent?"

**Rule 4 — Challenge stated assumptions.**
If the user states something as a design decision without justification, probe it:
- "Why that approach over X?"
- "What breaks if Y happens at scale?"
- "Have you considered Z as an alternative?"

**Rule 5 — Actively hunt for gaps.**
After each exchange, check whether any of these are still undefined:
- [ ] Agent boundaries — what each agent is and is NOT responsible for
- [ ] Data contracts — exact formats passed between agents
- [ ] Error paths — what happens on failure in each component
- [ ] Scalability decisions — concurrent requests, queue strategy, timeouts
- [ ] Security surface — authentication, authorisation, input validation points
- [ ] Deployment target — where this runs, how it starts, how it scales
- [ ] Provider strategy — which Ollama models, which agent gets which model

**Rule 6 — Progress summaries every 5–7 questions.**
After every 5–7 exchanges, pause and present:

```
What I understand so far:
- [confirmed decisions]

What is still undefined:
- [open questions]

Next area to explore: [topic]
```

**Rule 7 — Satisfaction gate (mandatory).**
When you judge the architecture has sufficient clarity for implementation, ask:
> "I believe I have a solid enough understanding to write the implementation plan.
> Are you satisfied with the level of detail we've reached, or should we continue refining?"

- If **YES**: generate `implementation.md` immediately using the format in `rules-deep-plan/2_implementation_md_format.xml`
- If **NO**: return to Rule 2 and continue. Ask what aspect still needs more depth.

**Rule 8 — Never generate implementation.md without the satisfaction gate being passed.**
