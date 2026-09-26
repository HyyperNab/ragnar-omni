# DEPLOYMENT — Production Guide

## Prerequisites

- Python ≥ 3.11 (3.12 recommended; StrEnum is load-bearing)
- ~200 MB RSS at runtime peak; the reference host was 4 GB with ×20 headroom
- Network only needed at install time (runtime is fully offline)

## Route 1 — Bare metal (venv)

```bash
git clone <repo> && cd RAGNAR
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,api]"

# The production gate, in order — all must pass:
ruff check src tests
mypy src
pytest -q
ragnar --test            # in-binary suite, exit 0

# Secret: 32+ random bytes, injected per environment, never committed
export RAGNAR_OMEGA_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
```

Ubuntu note: `python3-venv` may be missing (`apt install python3.12-venv`).
A user-site fallback works for gates: `pip install --user --break-system-packages -e .[dev,api]`.

## Route 2 — Docker / Compose (the full stack)

```bash
cp .env.example .env
# edit .env: set RAGNAR_OMEGA_KEY to a real 32+ byte secret (openssl rand -hex 32)
docker compose up --build -d
docker compose ps          # healthy = healthcheck green
docker compose logs -f api
```

What the stack gives you (see SPOF_ANALYSIS.md §C):
- non-root user, read-only root filesystem, no secret baked into the image
- memory/CPU limits, restart policy
- `/health` telemetry including the citation reverify flag
- pinned base image (`python:3.12-slim`), only `[api]` extras in the image

Behind TLS: put your reverse proxy (nginx/caddy/traefik) in front; the API
binds 127.0.0.1 by default. Set `RAGNAR_API_KEY` for an application-layer key
on every route (fail-closed: if set and missing → 401).

## Route 3 — Bare-metal service (systemd)

```ini
# /etc/systemd/system/ragnar-api.service
[Unit]
Description=RAGNAR OMNI v33 API
After=network.target

[Service]
Type=simple
User=ragnar
Environment=RAGNAR_OMEGA_KEY=<from your secret store>
Environment=RAGNAR_API_KEY=<optional>
WorkingDirectory=/opt/RAGNAR
ExecStart=/opt/RAGNAR/.venv/bin/uvicorn ragnar.api:app --host 127.0.0.1 --port 8000
Restart=on-failure
MemoryMax=512M
NoNewPrivileges=true
ProtectSystem=strict
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

## Operation

### The reverify calendar (non-negotiable)

`CITATIONS_VERIFIED.json` carries `reverify_after: 2027-01-27`. Production
telemetry exposes it (`GET /health → citation_reverify_due`). When it flips
true: reverify every CONFIRMED case citation against primary sources
(juris/dejure/openJur), update tiers, bump the date, and re-run the gates.
**BGH VI ZR 375/24 was ~10 weeks old at freeze — it is load-bearing.**

### Runtime self-verification

```bash
ragnar --test        # 42-contract suite, ships inside the wheel
```

Run it from cron after any environment change; exit != 0 means the wheel is
broken, not the case.

### State policy

- CLI: `save_state`/`load_state` round-trips the full orchestrator state
  including the hash-chained audit trail (integrity re-verified on load).
- API: plans are in-memory by design (restart clears them) — the operator
  decides where case state lives. Never commit `*.state.json`.

### Secrets

| Secret | Where it lives | What breaks without it |
|---|---|---|
| `RAGNAR_OMEGA_KEY` | env / secret manager only | Execution (lock refuses to engage); drafting still works — by design |
| `RAGNAR_API_KEY` | env, optional | API auth (fail-closed if set) |

Rotation: the Omega Lock compares its armed key hash timing-safely at unlock;
rotating the key while a lock is engaged invalidates unlocks (fail-closed).
