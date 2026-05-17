# Project Context

## Stack

- **Backend**: Python 3.11+ with FastAPI
- **Frontend**: React 18 + TypeScript + Vite
- **AI Provider**: Ollama (local, `http://localhost:11434`)
- **Agent Orchestration**: LangGraph (StateGraph + MemorySaver) with ChatOllama via langchain-ollama
- **Deployment**: Docker Compose — `docker compose up --build` starts everything; Ollama runs on the host machine

## Naming Conventions

Enforced across all modes. Non-negotiable.

- All Python identifiers: `snake_case` — agent names, tool names, function names, variables
- All file names: `snake_case.py`, `snake_case.yaml`, `snake_case.json`
- Agent naming pattern: `domain_role_agent` (e.g., `research_summariser_agent`, `data_validation_agent`)
- Tool naming pattern: `verb_object` (e.g., `fetch_web_content`, `store_result`, `send_email`)
- React components: PascalCase (only exception to snake_case rule)
- No camelCase in Python, no hyphens in code identifiers

## Architecture Principles

- **LangGraph-first**: All orchestration uses `StateGraph` from `langgraph`. No custom agent base classes or registry patterns. One graph per system, compiled once at startup with `MemorySaver` checkpointer.
- **Provider via langchain-ollama**: All LLM calls go through `ChatOllama` from `langchain_ollama` (NOT `langchain_community`). The `get_llm()` factory in `app/llm.py` is the single import point — nothing else creates LLM instances directly.
- **Single-responsibility agents**: One agent, one clearly scoped domain. Each agent is either a LangGraph node function (`async def node(state) -> dict`) or a `create_react_agent()` instance. Never a "general purpose" agent.
- **Session state via MemorySaver**: Conversation history is managed by LangGraph's `MemorySaver` checkpointer. Every invocation passes `config={"configurable": {"thread_id": session_id}}`. No external session store needed for development; swap to `SqliteSaver`/Redis for production.
- **No hardcoded credentials**: All secrets via environment variables or `.env` files. Never in code.
- **Scripts, not commands**: Always generate deployment and setup scripts. Never execute commands directly.

## Key Files

- `docker-compose.yml` — starts backend + frontend containers; Ollama runs on host
- `backend/Dockerfile` — Python 3.11-slim container
- `frontend/Dockerfile` — Node 20-slim container
- `implementation.md` — architectural source of truth, produced by `deep-plan` mode
- `.bob/custom_modes.yaml` — all Bob mode definitions for this project
- `.bob/mcp.json` — MCP server config: `docs-langchain` (LangChain/LangGraph live docs)
- `.bob/skills/` — reusable Bob skills (`/grill-me`, `/lint`)
- `.bob/rules-deep-plan/` — questioning protocol and implementation.md format
- `.bob/rules-multi-agent-system-builder/` — generation rules for the backend (1–4, 6–9)

## MCP Servers

| Server | Tools | Purpose |
|--------|-------|---------|
| `docs-langchain` | `search_docs_by_lang_chain(query)` | Semantic search across all LangChain + LangGraph docs |
| | `query_docs_filesystem_docs_by_lang_chain(command)` | ripgrep/find/cat against raw doc files |

Phase 0 Step 4 in multi-agent-system-builder batches all necessary `search_docs_by_lang_chain`
queries once at the start of a session — do not re-run per file. The batch covers: StateGraph,
MessagesState, MemorySaver, ChatOllama parameters, create_react_agent, @tool, and all message
class imports. Only streaming and SqliteSaver queries are run separately, when needed.

## Session Workflow

```
deep-plan mode + /grill-me      →  implementation.md
        ↓
multi-agent-system-builder      →  full backend generated (FastAPI + LangGraph)
        ↓
frontend-craftsman + /neo-brutalism  →  React + TypeScript frontend
        ↓
Advanced mode + /lint           →  bug fixes across both layers
        ↓
Advanced mode                   →  full testing
```

## Frontend Stack

- **Framework**: React 18 + TypeScript (strict) + Vite
- **Styling**: Tailwind CSS with style-system tokens from active skill
- **API client**: typed fetch wrapper in `src/lib/api.ts` — maps to backend Pydantic models
- **Routing**: React Router v6
- **Design system**: skill-driven — `/neo-brutalism` currently available
- **Dev proxy**: Vite proxies `/api/*` → `http://localhost:8000` (no CORS issues in dev)
