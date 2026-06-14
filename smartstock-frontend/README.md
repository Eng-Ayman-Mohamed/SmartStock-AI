# SmartStock AI — Frontend

React + TypeScript + Vite frontend for the SmartStock AI inventory management platform.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | React 19 |
| Build tool | Vite 8 |
| Language | TypeScript 6 |
| Styling | Tailwind CSS 4 |
| State | Zustand 5 |
| Data fetching | TanStack React Query 5 |
| Routing | React Router 7 |
| Charts | Recharts 3 |
| HTTP client | Axios 1 |

## Prerequisites

- **Node.js** >= 22 (LTS recommended)
- **npm** >= 10
- **Backend** running on `localhost:8000` (see `smartstock-backend/`)

## Quick Start — Local Development

```bash
cd smartstock-frontend
cp .env.example .env.local   # edit as needed
npm install
npm run dev
```

Dev server starts on [http://localhost:5173](http://localhost:5173). API requests to `/api` are proxied to `http://localhost:8000` via the Vite dev server.

## Quick Start — Docker (Full Stack)

From the repository root:

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000/api/ |
| PostgreSQL | localhost:5433 |
| Redis | localhost:6379 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 |

## Environment Variables

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `VITE_API_URL` | `/api` | Yes | Base path for backend API requests. In dev, proxied through Vite. In Docker, proxied through Nginx. |
| `VITE_API_BASE_URL` | *(unset)* | No | Absolute backend URL for production builds not using a reverse proxy. |
| `VITE_AUTH_BYPASS` | `false` | No | Set to `"true"` to bypass authentication during development. |

Copy `.env.example` to `.env.local` and adjust values. `.env.local` is git-ignored.

## Available Commands

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Vite dev server on port 5173 with HMR |
| `npm run build` | Type-check with `tsc -b` then build production bundle to `dist/` |
| `npm run preview` | Preview the production build locally |
| `npm run lint` | Run ESLint across the project |

## Project Structure

```
smartstock-frontend/
├── src/
│   ├── features/           # Feature modules (domain-driven)
│   │   ├── ai-assistant/   # AI chat & voice assistant
│   │   ├── auth/           # Login, register, session management
│   │   ├── dashboard/      # Dashboard widgets & metrics
│   │   ├── forecasting/    # Demand forecasting charts & alerts
│   │   ├── inventory/      # Product & stock management
│   │   ├── invoice-scan/   # AI-powered invoice scanning
│   │   ├── profile/        # User profile page
│   │   ├── purchasing/     # Purchase orders & suppliers
│   │   └── users/          # User management (admin)
│   ├── lib/                # Core utilities (axios, router, query client)
│   ├── shared/             # Reusable components, hooks, utils
│   ├── store/              # Zustand stores (auth, toast, UI)
│   ├── types/              # Shared TypeScript types
│   ├── App.tsx             # Root component
│   └── main.tsx            # Entry point
├── public/                 # Static assets
├── docker-entrypoint.sh    # Generates runtime env config for Docker
├── nginx.conf              # Production reverse proxy config
├── Dockerfile              # Multi-stage build (Node → Nginx)
├── vite.config.ts          # Vite config with dev proxy
├── tailwind.config.ts      # Tailwind theme (brand colors, typography)
└── eslint.config.js        # ESLint flat config
```

## Architecture

- **API proxy:** In development, Vite proxies `/api` → `http://localhost:8000`. In Docker, Nginx proxies `/api/` → `http://backend:8000/api/`.
- **Auth flow:** JWT access tokens stored in Zustand (in-memory). Refresh via HttpOnly cookie. Axios interceptor handles 401 → token refresh → retry.
- **API response envelope:** Backend returns `{ status, data, meta }`. Axios interceptor unwraps `data` automatically.
- **Roles:** `viewer`, `manager`, `admin`. Protected routes enforce role-based access.

## Testing

```bash
cd smartstock-frontend
npm run lint          # ESLint
npx tsc --noEmit      # Type checking
```

No frontend test framework is currently configured. Tests run in CI via GitHub Actions (`frontend-lint` and `frontend-build` jobs).

## Deployment

- **Frontend:** Deploy `dist/` to Vercel or any static host. Set `VITE_API_BASE_URL` to your backend URL.
- **Docker:** `docker compose up --build` runs the full stack with Nginx serving the SPA and proxying API calls.
- **CI:** GitHub Actions runs lint + build on push to `main`/`develop` and on PRs to `main`.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `npm run dev` can't reach API | Ensure backend is running on port 8000. Check Vite proxy config in `vite.config.ts`. |
| Docker: frontend can't reach backend | Ensure `docker compose up` started all services. Check network aliases (`backend`, `db`, `cache`). |
| Stale build after env change | Run `npm run build` again. Vite embeds env vars at build time. |
| CORS errors in dev | Backend must allow `http://localhost:5173`. Check Django CORS settings. |
