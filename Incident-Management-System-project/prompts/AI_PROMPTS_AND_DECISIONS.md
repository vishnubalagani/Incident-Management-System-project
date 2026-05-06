# Prompts & AI Assistance Log

This file documents the AI-assisted development process for this project,
as required by the assignment submission guidelines.

## Tools Used
- Claude Sonnet (claude.ai) — architecture design, code generation, debugging

---

## Prompt 1 — Architecture Design
**Goal:** Design a full system architecture for the IMS.

**Prompt used:**
> "I have a Zeotap SRE intern assignment to build an Incident Management System.
> Help me design the full architecture including: signal ingestion at 10k/sec,
> debouncing, state machine for work items, alert strategy pattern, and storage
> for PostgreSQL (work items), MongoDB (raw signals), Redis (cache), and TimescaleDB.
> Use Python FastAPI. Show me the architecture diagram first."

**Output:** Architecture diagram with 4 tiers (Ingestion → Processing → Storage → Frontend),
tech stack selection, and folder structure.

---

## Prompt 2 — Backend Code Generation
**Goal:** Generate all backend files at once.

**Prompt used:**
> "Build the complete backend: FastAPI app, asyncio.Queue buffer, debounce engine,
> State pattern for OPEN→INVESTIGATING→RESOLVED→CLOSED transitions,
> Strategy pattern for alert priorities (P0=RDBMS, P1=API, P2=CACHE),
> PostgreSQL models (WorkItem + RCA), MongoDB raw signal storage,
> Redis dashboard cache, /health endpoint, throughput metrics every 5s,
> rate limiting via slowapi, and unit tests for state machine + RCA validation."

**Output:** All backend files including models, services, API routers, and tests.

---

## Prompt 3 — Frontend Generation
**Goal:** Build a React dashboard.

**Prompt used:**
> "Build a React + Vite frontend with: dark theme, live feed (auto-refreshes every 5s,
> severity-sorted), incident detail page showing raw MongoDB signals,
> status transition buttons with state machine enforcement,
> RCA form with datetime pickers, category dropdown, fix/prevention textareas,
> and a navbar showing live signals/sec and queue depth from /health."

**Output:** Full React frontend with App.jsx, Dashboard, IncidentDetail, RCAForm, Navbar.

---

## Prompt 4 — Infrastructure
**Goal:** Docker Compose for all services.

**Prompt used:**
> "Write a Docker Compose file that wires together: PostgreSQL 16, MongoDB 7,
> Redis 7, the FastAPI backend, and the React/Nginx frontend. Include healthchecks
> and proper dependency ordering."

**Output:** docker-compose.yml with all 5 services, healthchecks, and volumes.

---

## Prompt 5 — Simulation Script
**Goal:** Mock failure scenario script.

**Prompt used:**
> "Write a Python simulation script that sends 150 RDBMS signals, 60 MCP signals,
> 30 cache signals, and 20 API signals concurrently to test debouncing and the full pipeline."

**Output:** mock_data/simulate_outage.py

---

## Design Decisions Made With AI Assistance

| Decision | Rationale |
|---|---|
| asyncio.Queue (maxsize=50k) | Non-blocking backpressure — DB slowness never crashes ingestion |
| State pattern for WorkItem | Clean, extensible lifecycle; illegal transitions throw exceptions |
| Strategy pattern for alerts | Easily add new component types without touching core logic |
| Redis TTL=10s for dashboard | Trades 10s staleness for massive read reduction under load |
| Motor (async MongoDB driver) | Fully async — no thread blocking on high-volume signal writes |
| slowapi for rate limiting | Native FastAPI integration, per-IP limiting |
