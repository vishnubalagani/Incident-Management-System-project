#!/usr/bin/env python3
"""
Simulate a failure scenario:
  1. RDBMS outage (PG_PRIMARY_01) — 150 signals over 15s → debounced to 1 Work Item
  2. MCP host failure (MCP_HOST_02) — 60 signals over 8s → debounced to 1 Work Item
  3. Cache degradation (REDIS_CLUSTER_01) — 30 signals → P2
  4. API latency spike (API_GATEWAY_01) — 20 signals → P1
"""
import asyncio
import httpx
import random
import time

BASE_URL = "http://localhost:8000"

SCENARIOS = [
    {
        "component_id": "PG_PRIMARY_01",
        "component_type": "RDBMS",
        "errors": ["CONNECTION_REFUSED", "DEADLOCK_DETECTED", "QUERY_TIMEOUT"],
        "count": 150,
        "burst_over_seconds": 15,
    },
    {
        "component_id": "MCP_HOST_02",
        "component_type": "MCP",
        "errors": ["HOST_UNREACHABLE", "TLS_HANDSHAKE_FAILED"],
        "count": 60,
        "burst_over_seconds": 8,
    },
    {
        "component_id": "REDIS_CLUSTER_01",
        "component_type": "CACHE",
        "errors": ["CACHE_MISS_STORM", "EVICTION_THRESHOLD_EXCEEDED"],
        "count": 30,
        "burst_over_seconds": 5,
    },
    {
        "component_id": "API_GATEWAY_01",
        "component_type": "API",
        "errors": ["LATENCY_SPIKE", "UPSTREAM_TIMEOUT"],
        "count": 20,
        "burst_over_seconds": 4,
    },
]


async def send_signal(client: httpx.AsyncClient, scenario: dict):
    payload = {
        "component_id": scenario["component_id"],
        "component_type": scenario["component_type"],
        "error_code": random.choice(scenario["errors"]),
        "message": f"Automated failure simulation for {scenario['component_id']}",
        "latency_ms": round(random.uniform(500, 5000), 1),
        "metadata": {"simulated": True, "run_id": int(time.time())},
    }
    try:
        r = await client.post(f"{BASE_URL}/api/signals", json=payload, timeout=5)
        return r.status_code
    except Exception as e:
        return f"error: {e}"


async def run_scenario(scenario: dict):
    delay = scenario["burst_over_seconds"] / scenario["count"]
    print(f"\n[{scenario['component_id']}] Sending {scenario['count']} signals over {scenario['burst_over_seconds']}s...")
    async with httpx.AsyncClient() as client:
        tasks = []
        for i in range(scenario["count"]):
            tasks.append(send_signal(client, scenario))
            await asyncio.sleep(delay)
        results = await asyncio.gather(*tasks)
    ok = sum(1 for r in results if r == 200)
    print(f"[{scenario['component_id']}] Done — {ok}/{scenario['count']} signals accepted")


async def main():
    print("=" * 60)
    print("IMS Failure Simulation Script")
    print("=" * 60)

    # Check backend is up
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{BASE_URL}/health", timeout=5)
            print(f"Backend health: {r.json()['status']}")
        except Exception as e:
            print(f"Backend not reachable: {e}")
            print("Make sure docker-compose is running: docker compose up -d")
            return

    # Run all scenarios concurrently
    await asyncio.gather(*[run_scenario(s) for s in SCENARIOS])
    print("\nSimulation complete. Check the dashboard at http://localhost:3000")


if __name__ == "__main__":
    asyncio.run(main())
