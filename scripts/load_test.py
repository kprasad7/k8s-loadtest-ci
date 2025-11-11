#!/usr/bin/env python3
"""Execute the HTTP load test against foo and bar hosts."""
from __future__ import annotations

import argparse
import json
import random
import statistics
import time
from pathlib import Path
from typing import Dict, List

import requests

import utils

HOSTS = ["foo.localhost", "bar.localhost"]
RESULT_JSON = "load-test-results.json"
RESULT_MARKDOWN = "load-test-results.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run load test")
    parser.add_argument("--requests", type=int, default=200, help="Total number of requests to send")
    parser.add_argument("--timeout", type=float, default=10.0, help="Per-request timeout in seconds")
    parser.add_argument("--warmup-attempts", type=int, default=20)
    parser.add_argument("--warmup-delay", type=float, default=5.0)
    return parser.parse_args()


def warmup(session: requests.Session, host: str, attempts: int, delay: float, timeout: float) -> None:
    url = f"http://{host}"
    for attempt in range(1, attempts + 1):
        try:
            response = session.get(url, timeout=timeout)
            if response.status_code == 200:
                utils.log(f"Warm-up for {host} succeeded on attempt {attempt}")
                return
        except requests.RequestException:
            pass
        utils.log(f"Warm-up attempt {attempt} for {host} failed; retrying in {delay}s")
        time.sleep(delay)
    raise RuntimeError(f"Warm-up failed for {host} after {attempts} attempts")


def percentile(latencies: List[float], pct: float) -> float:
    if not latencies:
        return 0.0
    ordered = sorted(latencies)
    k = (len(ordered) - 1) * pct
    f = int(k)
    c = min(f + 1, len(ordered) - 1)
    if f == c:
        return ordered[f]
    return ordered[f] * (c - k) + ordered[c] * (k - f)


def compute_metrics(latencies: List[float], successes: int, attempts: int, duration: float, failures: int) -> Dict[str, float]:
    if attempts == 0:
        return {"rps": 0.0, "success_rate": 0.0, "avg": 0.0, "p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0}
    avg = statistics.mean(latencies) if latencies else 0.0
    return {
        "rps": attempts / duration if duration else 0.0,
        "success_rate": successes / attempts,
        "avg": avg,
        "p50": percentile(latencies, 0.50),
        "p90": percentile(latencies, 0.90),
        "p95": percentile(latencies, 0.95),
        "p99": percentile(latencies, 0.99),
        "max": max(latencies) if latencies else 0.0,
        "requests": attempts,
        "failures": failures,
    }


def summarise(results: Dict[str, Dict[str, float]]) -> str:
    lines = [
        "### 🚦 Load-test summary",
        "| Host | Requests | Success % | Avg (ms) | P90 (ms) | P95 (ms) | P99 (ms) | Req/s | Failures |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for host in HOSTS:
        metrics = results[host]
        lines.append(
            "| {host} | {req} | {success:.1f}% | {avg:.2f} | {p90:.2f} | {p95:.2f} | {p99:.2f} | {rps:.2f} | {fail} |".format(
                host=host,
                req=int(metrics["requests"]),
                success=metrics["success_rate"] * 100,
                avg=metrics["avg"] * 1000,
                p90=metrics["p90"] * 1000,
                p95=metrics["p95"] * 1000,
                p99=metrics["p99"] * 1000,
                rps=metrics["rps"],
                fail=int(metrics["failures"]),
            )
        )
    combined = results["combined"]
    lines.append(
        "\nTotal duration: {duration:.2f}s for {total} requests (failures: {fail}).".format(
            duration=combined["duration"],
            total=int(combined["total_requests"]),
            fail=int(combined["failures"]),
        )
    )
    return "\n".join(lines)


def run_load(session: requests.Session, total_requests: int, timeout: float) -> Dict[str, Dict[str, float]]:
    stats = {
        host: {"latencies": [], "successes": 0, "failures": 0, "attempts": 0}
        for host in HOSTS
    }
    start = time.perf_counter()
    for _ in range(total_requests):
        host = random.choice(HOSTS)
        stats[host]["attempts"] += 1
        url = f"http://{host}"
        sent = time.perf_counter()
        try:
            response = session.get(url, timeout=timeout)
            latency = time.perf_counter() - sent
            stats[host]["latencies"].append(latency)
            expected = host.split(".")[0]
            if response.status_code == 200 and expected in response.text:
                stats[host]["successes"] += 1
            else:
                stats[host]["failures"] += 1
        except requests.RequestException as exc:
            stats[host]["latencies"].append(time.perf_counter() - sent)
            stats[host]["failures"] += 1
            utils.log(f"Request to {host} failed: {exc}")
    duration = time.perf_counter() - start

    results: Dict[str, Dict[str, float]] = {}
    for host in HOSTS:
        latencies = stats[host]["latencies"]
        successes = stats[host]["successes"]
        attempts = stats[host]["attempts"]
        failures = stats[host]["failures"]
        results[host] = compute_metrics(latencies, successes, attempts, duration, failures)

    all_latencies: List[float] = stats[HOSTS[0]]["latencies"] + stats[HOSTS[1]]["latencies"]
    total_attempts = sum(stats[host]["attempts"] for host in HOSTS)
    total_successes = sum(stats[host]["successes"] for host in HOSTS)
    total_failures = sum(stats[host]["failures"] for host in HOSTS)
    combined = compute_metrics(all_latencies, total_successes, total_attempts, duration, total_failures)
    combined.update({"duration": duration, "total_requests": total_attempts})
    results["combined"] = combined
    return results


def write_results(results: Dict[str, Dict[str, float]]) -> Dict[str, str]:
    utils.ensure_artifacts_dir()
    json_path = utils.ARTIFACTS / RESULT_JSON
    md_path = utils.ARTIFACTS / RESULT_MARKDOWN
    json_path.write_text(json.dumps(results, indent=2))
    markdown = summarise(results)
    md_path.write_text(markdown)
    utils.log("\n" + markdown)
    return {"json": str(json_path), "markdown": str(md_path)}


def main() -> int:
    args = parse_args()
    utils.ensure_artifacts_dir()

    session = requests.Session()
    for host in HOSTS:
        warmup(session, host, args.warmup_attempts, args.warmup_delay, args.timeout)

    results = run_load(session, args.requests, args.timeout)
    paths = write_results(results)
    utils.update_state({"load_test": {**paths, "results": results}})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
