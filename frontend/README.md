# Meetrix Frontend — Kawaii-Brutalism Edition

A React + TypeScript + Vite frontend for the Meetrix meeting intelligence platform, styled with a unique **Kawaii-Brutalism** design system that combines raw neo-brutalist structure with soft kawaii aesthetics.

## Design System

**Kawaii-Brutalism** = Neo-brutalism skeleton + Kawaii heart

- **Structure**: Thick 2-3px black borders, hard offset shadows (no blur), zero border-radius, 75ms snappy transitions
- **Soul**: Soft pastel fills (pink, lavender, mint, peach, coral), cute mascot ✦(•‿•)✦, decorative stickers (✦ ✿ ♡ ★)
- **Typography**: Space Grotesk (body), JetBrains Mono (data), Nunito (headings)
- **Interaction**: Press effect — elements translate toward shadow on hover/active

## Tech Stack

- **React 18** + **TypeScript** (strict mode)
- **Vite** (dev server + build tool)
- **Tailwind CSS** (with custom Kawaii-Brutalism tokens)
- **React Router v6** (client-side routing)
- **Recharts** (charts) + **D3.js** (network graph)

## Project Structure

```
frontend/
├── src/
│   ├── types/          # TypeScript interfaces from backend Pydantic models
│   │   └── api.ts
│   ├── lib/            # API client + utilities
│   │   ├── api.ts      # Typed fetch wrapper
│   │   └── session.ts  # Session ID management
│   ├── contexts/       # React contexts
│   │   └── SessionContext.tsx
│   ├── hooks/          # Custom hooks
│   │   ├── useAnalysisPolling.ts  # Polls /api/v1/results/:id every 3s
│   │   └── useAgentStatus.ts      # Polls /api/v1/sessions/:id/agent-status every 1s
│   ├── components/
│   │   ├── ui/         # Base UI primitives (Button, Card, Badge, Input, etc.)
│   │   └── shell/      # Shell + Sidebar (persistent layout)
│   ├── pages/          # Route components
│   │   ├── Settings.tsx   # Upload + config (entry point)
│   │   ├── Overview.tsx   # Dashboard with agent pipeline + KPI cards
│   │   ├── Schedule.tsx   # Smart meeting scheduling
│   │   ├── Ask.tsx        # Natural language queries
│   │   ├── Meetings.tsx   # Meeting table + slide-over
│   │   ├── People.tsx     # Person cards + calendar view
│   │   ├── Network.tsx    # D3 force-directed graph
│   │   ├── Health.tsx     # Meeting health metrics
│   │   ├── Trends.tsx     # Time series charts
│   │   └── Reports.tsx    # Executive report
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── index.html
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
└── .env.example
```

## Setup

### Prerequisites

- **Node.js 20+** and **npm**
- **Backend running** at `http://localhost:8000` (see `../backend/README.md`)

### Installation

```bash
cd frontend
npm install
```

### Environment Variables

Create `.env.local` from `.env.example`:

```bash
cp .env.example .env.local
```

For local development (no Docker):
```env
VITE_BACKEND_URL=http://localhost:8000
VITE_API_BASE_URL=
```

For Docker Compose (set in `docker-compose.yml` instead):
```env
VITE_BACKEND_URL=http://backend:8000
VITE_API_BASE_URL=
```

### Development

```bash
npm run dev
```

Frontend runs at **http://localhost:5173**

Vite proxies `/api/*` requests to the backend, so no CORS issues in development.

### Build

```bash
npm run build
```

Outputs to `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## API Integration

### Backend Contract

All API types in [`src/types/api.ts`](src/types/api.ts) are derived from backend Pydantic models in `backend/app/models/schemas.py`.

**Never invent API endpoints or field names** — the frontend is built against the real backend contract.

### API Client

All fetch calls go through [`src/lib/api.ts`](src/lib/api.ts):

```typescript
import { analyze, getResults, getAgentStatus } from '@/lib/api';

// Upload and start analysis
const { session_id } = await analyze(historicalCsv, upcomingCsv, config);

// Poll for results
const results = await getResults(session_id);

// Poll for agent status
const { agents } = await getAgentStatus(session_id);
```

### Session Management

Session IDs are generated per browser tab and stored in `sessionStorage`:

```typescript
import { getSessionId } from '@/lib/session';

const sessionId = getSessionId(); // Generates or retrieves existing ID
```

### Polling Pattern

- **Results polling**: [`useAnalysisPolling`](src/hooks/useAnalysisPolling.ts) polls `/api/v1/results/:id` every 3 seconds until `status === 'complete' || 'failed'`
- **Agent status polling**: [`useAgentStatus`](src/hooks/useAgentStatus.ts) polls `/api/v1/sessions/:id/agent-status` every 1 second while `status === 'processing'`

## Pages

### 1. Settings (`/settings`)
**Entry point** for new analyses. Upload historical meetings CSV (required) + upcoming meetings CSV (optional). Configure analysis weights. Triggers backend pipeline.

### 2. Overview (`/`)
**Dashboard** with:
- Live agent execution panel (6 tiers, 19 agents)
- 4 KPI cards (cost, waste score, people in overload, cascade chains)
- Meetrix Score widget
- Top 5 worst meetings table

### 3. Schedule (`/schedule`)
Smart meeting scheduling with waste prediction. *Coming soon.*

### 4. Ask (`/ask`)
Natural language queries about analysis results. *Coming soon.*

### 5. Meetings (`/meetings`)
Filterable meeting table with slide-over detail view. *Coming soon.*

### 6. People (`/people`)
Person cards with focus time analysis + calendar week view. *Coming soon.*

### 7. Network (`/network`)
D3 force-directed graph of meeting network + bottleneck detection. *Coming soon.*

### 8. Health (`/health`)
Meeting health metrics + action item follow-through. *Coming soon.*

### 9. Trends (`/trends`)
Time series charts (Meetrix score, cost, focus time, anomalies). *Coming soon.*

### 10. Reports (`/reports`)
Executive report with ROI projection. *Coming soon.*

## Design System Usage

### Colors

```typescript
// Tailwind classes
bg-kb-pink      // #FFB7C5 - Primary CTA, active states
bg-kb-lavender  // #C8B8F8 - Secondary accent, hover states
bg-kb-mint      // #A8EED4 - Success, complete states
bg-kb-peach     // #FFD4B8 - Warning, medium severity
bg-kb-coral     // #FF8FA3 - Errors, high waste
bg-kb-cream     // #FFF8F0 - Page background
bg-kb-white     // #FFFFFF - Card surfaces
bg-kb-muted     // #EDE8F5 - Disabled, subtle dividers
bg-kb-black     // #000000 - Borders, shadows, text
```

### Shadows

```typescript
shadow-brutal-sm   // 3px 3px 0px #000000
shadow-brutal-md   // 5px 5px 0px #000000
shadow-brutal-lg   // 8px 8px 0px #000000
shadow-brutal-none // 0px 0px 0px #000000 (pressed state)
```

### Typography

```typescript
font-sans     // Space Grotesk - body, labels, buttons
font-mono     // JetBrains Mono - data, numbers, status tags
font-display  // Nunito - page titles, section headings
```

### Components

All base UI components in [`src/components/ui/`](src/components/ui/):

- **Button**: Primary, secondary, destructive, success variants
- **Card**: With optional sticker accent
- **Badge**: Status tags with color variants
- **Input / Textarea**: With labels
- **ProgressBar**: Animated with color options
- **Table**: Brutal table with sortable headers
- **Spinner / LoadingText**: Loading indicators

## Docker

Frontend is containerized in `docker-compose.yml` at project root.

```bash
# From project root
docker compose up --build
```

Frontend container:
- Runs Vite dev server on port 5173
- Proxies `/api/*` to backend service
- Hot reload enabled

## Troubleshooting

### TypeScript Errors

All TypeScript errors about missing React types will resolve after running `npm install`.

### CORS Issues

If you see CORS errors:
1. Check backend is running at `http://localhost:8000`
2. Verify Vite proxy config in `vite.config.ts`
3. Check backend CORS config in `backend/app/main.py` allows `http://localhost:5173`

### Ollama Not Connected

The Settings page shows Ollama connection status. If offline:
1. Start Ollama: `ollama serve`
2. Verify it's running at `http://localhost:11434`
3. Backend will show warning in logs but won't crash

## Contributing

When adding new pages:
1. Create page component in `src/pages/`
2. Add route in `src/App.tsx`
3. Add nav item in `src/components/shell/Sidebar.tsx`
4. Follow Kawaii-Brutalism design system strictly
5. Handle loading, error, and empty states
6. Use custom hooks for data fetching

## License

See project root LICENSE file.