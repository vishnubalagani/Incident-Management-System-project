# Incident Management System (IMS)


A resilient, production-grade Incident Management System that monitors a distributed stack (APIs, MCP Hosts, Caches, Queues, RDBMS, NoSQL) and manages failure mediation workflows end-to-end.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        INGESTION TIER                        │
│  Signal Sources → Rate Limiter → POST /api/signals (FastAPI) │
└──────────────────────────┬──────────────────────────────────┘
                           │ non-blocking enqueue
┌──────────────────────────▼──────────────────────────────────┐
│                    IN-MEMORY BUFFER                          │
│              asyncio.Queue (maxsize=50,000)                  │
└──────────────────────────┬──────────────────────────────────┘
                           │ async worker drains
┌──────────────────────────▼──────────────────────────────────┐
│                    PROCESSING TIER                           │
│  Debounce Engine → Alert Strategy (P0/P1/P2) → State Machine │
│  OPEN → INVESTIGATING → RESOLVED → CLOSED (requires RCA)    │
└────────┬───────────────────┬────────────────────────────────┘
         │                   │
┌────────▼──────┐   ┌────────▼──────────────────────────────┐
│  PostgreSQL   │   │  MongoDB        Redis       Timescale  │
│  Work Items   │   │  Raw signals    Dashboard   Metrics    │
│  RCA records  │   │  Audit log      Hot-path    MTTR agg.  │
└───────────────┘   └───────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    REACT FRONTEND                            │
│  Live Feed (5s refresh) · Incident Detail · RCA Form        │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| Backend | Python 3.12 + FastAPI | Async-native, fast, great DX |
| Buffer | asyncio.Queue | Zero-dependency backpressure |
| RDBMS | PostgreSQL 16 + SQLAlchemy async | Transactional Work Item + RCA writes |
| NoSQL | MongoDB 7 + Motor | High-volume raw signal storage |
| Cache | Redis 7 | Dashboard hot-path, 10s TTL |
| Frontend | React 18 + Vite | SPA with live polling |
| Container | Docker Compose | One-command startup |

---

## Quick Start

### Prerequisites
- Docker 24+ and Docker Compose v2

### Run
```bash
git clone <your-repo-url>
cd incident-management-system
docker compose up --build
```

Services start in order (healthchecks enforce dependency ordering):
- PostgreSQL → MongoDB → Redis → Backend → Frontend

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Health | http://localhost:8000/health |

---

## Simulate a Failure

```bash
# Install httpx locally
pip install httpx

# Run simulation (sends 260 signals across 4 components)
python mock_data/simulate_outage.py
```

This simulates:
1. **PG_PRIMARY_01** — 150 RDBMS signals (debounced → 1 P0 Work Item)
2. **MCP_HOST_02** — 60 MCP host signals (debounced → 1 P0 Work Item)
3. **REDIS_CLUSTER_01** — 30 cache signals → 1 P2 Work Item
4. **API_GATEWAY_01** — 20 API signals → 1 P1 Work Item

---

## Backpressure Strategy

**The problem:** A DB write can take 5–50ms. At 10,000 signals/sec, a synchronous pipeline would exhaust connections and crash.

**The solution — three layers:**

1. **Rate limiter (SlowAPI):** Caps at 600 req/min per client IP. Prevents any single client overwhelming the endpoint.

2. **asyncio.Queue (maxsize=50,000):** The ingestion endpoint is *non-blocking* — it only does `queue.put_nowait()` and returns 200 immediately. If the queue is full, it returns 429. This fully decouples HTTP response time from DB write time.

3. **Async worker:** A single long-running `asyncio` task drains the queue, writes to MongoDB and PostgreSQL, and updates Redis. Being async (not threaded), it avoids GIL contention and context-switch overhead.

**Result:** The HTTP layer can accept bursts of 10k+ signals/sec regardless of storage latency.

---

## Design Patterns

### State Pattern — WorkItem Lifecycle
```
OPEN → INVESTIGATING → RESOLVED → CLOSED
```
Each status is a `State` class. Illegal transitions (e.g. OPEN → CLOSED) raise `InvalidTransitionError`. Transitioning to CLOSED without a complete RCA raises a `ValueError`.

### Strategy Pattern — Alert Priority
| Component | Strategy Class | Priority |
|---|---|---|
| RDBMS | RDBMSAlertStrategy | P0 |
| MCP | MCPAlertStrategy | P0 |
| API | APIAlertStrategy | P1 |
| QUEUE | QueueAlertStrategy | P1 |
| NOSQL | NoSQLAlertStrategy | P2 |
| CACHE | CacheAlertStrategy | P2 |

Adding a new component type = one new class + one dict entry. No existing code changes.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| POST | /api/signals | Ingest a signal |
| POST | /api/signals/batch | Ingest up to 100 signals |
| GET | /api/work-items | List all work items |
| GET | /api/work-items/dashboard | Cached dashboard (Redis) |
| GET | /api/work-items/{id} | Get work item detail |
| GET | /api/work-items/{id}/signals | Raw signals from MongoDB |
| PATCH | /api/work-items/{id}/status | Transition status |
| POST | /api/work-items/{id}/rca | Submit RCA |
| GET | /health | Health + throughput metrics |

---

## Run Tests

```bash
cd backend
pip install -r requirements.txt
pytest -v
```

Tests cover:
- All valid and invalid state machine transitions
- Alert strategy priority mapping
- RCA schema validation (min_length enforcement)

---

## Non-Functional Highlights

- **Concurrency:** Pure `asyncio` — no threads, no race conditions on status updates
- **Observability:** `/health` endpoint + console throughput logging every 5s
- **Resilience:** Queue-based decoupling means DB outage doesn't affect ingestion
- **Security:** Rate limiting on all ingestion endpoints; CORS configured
- **MTTR:** Auto-calculated on WorkItem close as `(closed_at - start_time).total_seconds()`
