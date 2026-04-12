# WorkReady Deploy

All-in-one deployment for the WorkReady internship simulation.

Nine services — six company websites, the student portal, a Seek-style job board, and the FastAPI backend — served from a single machine behind Caddy reverse proxy.

## Two deployment paths

### A) Docker (recommended)

```bash
# 1. Clone this repo
git clone https://github.com/michael-borck/workready-deploy.git
cd workready-deploy

# 2. Configure
cp domains.env.example domains.env   # edit with your 9 domain names
cp .env.example .env                 # edit with your LLM API keys + admin token

# 3. Run
docker compose up -d
```

The image is pre-built and published to `ghcr.io/michael-borck/workready:latest` on every push to main. No local build needed.

To build locally instead: `docker compose up -d --build`

### B) Bare metal (VPS / VM)

```bash
curl -fsSL https://raw.githubusercontent.com/michael-borck/workready-deploy/main/install.sh | bash
```

The script installs Caddy, uv, clones all 9 repos, builds the company sites, and installs the API dependencies. Then:

```bash
# Edit config
nano /opt/workready/domains.env
nano /opt/workready/.env

# Start
/opt/workready/start.sh
```

## DNS setup

You need 9 A (or CNAME) records pointing at the machine's IP:

| Domain | Service |
|---|---|
| `ironvaleresources.example.com` | IronVale Resources site |
| `nexuspointsystems.example.com` | NexusPoint Systems site |
| `horizonfoundation.example.com` | Horizon Foundation site |
| `southerncrossfinancial.example.com` | Southern Cross Financial site |
| `metrocouncilwa.example.com` | Metro Council WA site |
| `meridianadvisory.example.com` | Meridian Advisory site |
| `workready.example.com` | Student portal |
| `seekjobs.example.com` | seek.jobs job board |
| `workready-api.example.com` | FastAPI backend |

Edit `domains.env` with your actual domain names. Caddy handles TLS automatically via Let's Encrypt if port 443 is open.

## Configuration

### domains.env

Maps each service to a domain. See `domains.env.example`.

### .env

API configuration — LLM provider, model, API keys, admin token, interview booking settings. See `.env.example`.

### Data

SQLite database persists at `./data/workready.db` (Docker) or `/opt/workready/data/workready.db` (bare metal).

## Architecture

```
┌──────────────────────────────────────────────┐
│  Caddy (reverse proxy, :80/:443)             │
│    ├─ 6 company domains → static dist/       │
│    ├─ portal domain     → static HTML/JS     │
│    ├─ seek domain       → static dist/       │
│    └─ api domain        → reverse_proxy :8000│
│                                              │
│  FastAPI / uvicorn (:8000, internal)         │
│  SQLite (WAL mode, /data/workready.db)       │
└──────────────────────────────────────────────┘
```

The `install.sh` script is the single source of truth for both deployment paths. The Dockerfile runs the same script during `docker build`.

## Updating

**Docker:** `docker compose pull && docker compose up -d`

**Bare metal:** Re-run `install.sh` — it does `git pull --ff-only` on existing repos and rebuilds.

## Part of the WorkReady simulation

WorkReady is an educational internship simulation built for Curtin University. All companies and positions are fictional. See [the plan document](https://github.com/michael-borck/loco-ensayo) for the full context.
