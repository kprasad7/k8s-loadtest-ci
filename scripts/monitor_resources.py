#!/usr/bin/env python3
"""Capture resource utilization metrics from Prometheus during load test."""
from __future__ import annotations

import argparse
import json
import subprocess
import time
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests

import utils

PROMETHEUS_URL = "http://localhost:9090"
METRICS_FILE = "resource-metrics.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture Prometheus metrics")
    parser.add_argument("--prometheus-url", default=PROMETHEUS_URL)
    parser.add_argument("--duration", type=int, default=60, help="Monitoring duration in seconds")
    parser.add_argument("--interval", type=int, default=10, help="Scrape interval in seconds")
    return parser.parse_args()


def is_prometheus_ready(url: str) -> bool:
    try:
        response = requests.get(f"{url}/-/healthy", timeout=5)
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False


def query_prometheus(url: str, query: str) -> Optional[Dict]:
    """Execute a PromQL query and return results."""
    try:
        response = requests.get(f"{url}/api/v1/query", params={"query": query}, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "success":
            return data.get("data", {})
        utils.log(f"Prometheus query failed: {data.get('error', 'unknown error')}")
        return None
    except requests.RequestException as exc:
        utils.log(f"Failed to query Prometheus: {exc}")
        return None


def collect_metrics(url: str, namespace: str = "echo") -> Dict[str, float]:
    """Collect current resource metrics for the echo namespace."""
    metrics = {}
    
    # CPU usage
    cpu_query = f'sum(rate(container_cpu_usage_seconds_total{{namespace="{namespace}"}}[1m])) by (pod)'
    cpu_data = query_prometheus(url, cpu_query)
    if cpu_data and cpu_data.get("result"):
        total_cpu = sum(float(r["value"][1]) for r in cpu_data["result"])
        metrics["cpu_cores"] = round(total_cpu, 4)
    
    # Memory usage
    mem_query = f'sum(container_memory_working_set_bytes{{namespace="{namespace}"}}) by (pod)'
    mem_data = query_prometheus(url, mem_query)
    if mem_data and mem_data.get("result"):
        total_mem = sum(float(r["value"][1]) for r in mem_data["result"])
        metrics["memory_mb"] = round(total_mem / (1024 * 1024), 2)
    
    # Network I/O
    net_rx_query = f'sum(rate(container_network_receive_bytes_total{{namespace="{namespace}"}}[1m]))'
    net_rx_data = query_prometheus(url, net_rx_query)
    if net_rx_data and net_rx_data.get("result"):
        metrics["network_rx_mbps"] = round(float(net_rx_data["result"][0]["value"][1]) / (1024 * 1024), 2)
    
    net_tx_query = f'sum(rate(container_network_transmit_bytes_total{{namespace="{namespace}"}}[1m]))'
    net_tx_data = query_prometheus(url, net_tx_query)
    if net_tx_data and net_tx_data.get("result"):
        metrics["network_tx_mbps"] = round(float(net_tx_data["result"][0]["value"][1]) / (1024 * 1024), 2)
    
    # Pod count
    pod_query = f'count(kube_pod_status_phase{{namespace="{namespace}", phase="Running"}})'
    pod_data = query_prometheus(url, pod_query)
    if pod_data and pod_data.get("result"):
        metrics["running_pods"] = int(float(pod_data["result"][0]["value"][1]))
    
    metrics["timestamp"] = time.time()
    return metrics


def monitor_resources(url: str, duration: int, interval: int) -> List[Dict[str, float]]:
    """Collect metrics over a time period."""
    samples = []
    end_time = time.time() + duration
    
    utils.log(f"Monitoring resources for {duration}s with {interval}s interval")
    
    while time.time() < end_time:
        metrics = collect_metrics(url)
        if metrics:
            samples.append(metrics)
            utils.log(
                f"Sample: CPU={metrics.get('cpu_cores', 0):.3f} cores, "
                f"Memory={metrics.get('memory_mb', 0):.1f}MB, "
                f"Pods={metrics.get('running_pods', 0)}"
            )
        time.sleep(interval)
    
    return samples


def compute_statistics(samples: List[Dict[str, float]]) -> Dict[str, Dict[str, float]]:
    """Compute aggregate statistics from samples."""
    if not samples:
        return {}
    
    stats = {}
    
    for key in ["cpu_cores", "memory_mb", "network_rx_mbps", "network_tx_mbps"]:
        values = [s[key] for s in samples if key in s]
        if values:
            stats[key] = {
                "avg": round(sum(values) / len(values), 3),
                "min": round(min(values), 3),
                "max": round(max(values), 3),
            }
    
    # Pod count (usually constant)
    pod_counts = [s.get("running_pods", 0) for s in samples]
    if pod_counts:
        stats["running_pods"] = {"avg": round(sum(pod_counts) / len(pod_counts), 1)}
    
    return stats


def format_markdown(stats: Dict[str, Dict[str, float]]) -> str:
    """Format resource metrics as markdown table."""
    lines = [
        "### 📊 Resource Utilization",
        "| Metric | Average | Min | Max |",
        "| --- | ---: | ---: | ---: |",
    ]
    
    if "cpu_cores" in stats:
        cpu = stats["cpu_cores"]
        lines.append(f"| CPU (cores) | {cpu['avg']:.3f} | {cpu['min']:.3f} | {cpu['max']:.3f} |")
    
    if "memory_mb" in stats:
        mem = stats["memory_mb"]
        lines.append(f"| Memory (MB) | {mem['avg']:.1f} | {mem['min']:.1f} | {mem['max']:.1f} |")
    
    if "network_rx_mbps" in stats:
        rx = stats["network_rx_mbps"]
        lines.append(f"| Network RX (MB/s) | {rx['avg']:.2f} | {rx['min']:.2f} | {rx['max']:.2f} |")
    
    if "network_tx_mbps" in stats:
        tx = stats["network_tx_mbps"]
        lines.append(f"| Network TX (MB/s) | {tx['avg']:.2f} | {tx['min']:.2f} | {tx['max']:.2f} |")
    
    if "running_pods" in stats:
        lines.append(f"\nRunning pods: {int(stats['running_pods']['avg'])}")
    
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    utils.ensure_artifacts_dir()
    
    # Check if Prometheus is accessible
    state = utils.load_state()

    port_forward_proc: Optional[subprocess.Popen[str]] = None

    try:
        if is_prometheus_ready(args.prometheus_url):
            utils.log("Prometheus is healthy and accessible")
        else:
            utils.log(
                f"Prometheus not directly reachable at {args.prometheus_url}; attempting kubectl port-forward"
            )
            try:
                port_forward_proc = start_port_forward(state, args.prometheus_url)
            except (RuntimeError, utils.CommandError, FileNotFoundError) as exc:
                utils.log(f"Failed to start port-forward: {exc}")
                return 1
            if not is_prometheus_ready(args.prometheus_url):
                utils.log(
                    "Failed to establish port-forward to Prometheus; skipping resource monitoring"
                )
                return 1
            utils.log("Port-forward established; Prometheus is accessible")
    
        # Collect metrics
        samples = monitor_resources(args.prometheus_url, args.duration, args.interval)
    
        if not samples:
            utils.log("No metrics collected; check Prometheus configuration")
            return 1
    
        # Compute statistics
        stats = compute_statistics(samples)
    
        # Save results
        output = {
            "samples": samples,
            "statistics": stats,
            "prometheus_url": args.prometheus_url,
            "duration": args.duration,
        }
    
        metrics_path = utils.ARTIFACTS / METRICS_FILE
        metrics_path.write_text(json.dumps(output, indent=2))
        utils.log(f"Resource metrics saved to {metrics_path}")
    
        # Generate markdown
        markdown = format_markdown(stats)
        md_path = utils.ARTIFACTS / "resource-metrics.md"
        md_path.write_text(markdown)
        utils.log("\n" + markdown)
    
        # Update state
        utils.update_state({
            "resource_metrics": {
                "json": str(metrics_path),
                "markdown": str(md_path),
                "statistics": stats,
            }
        })
    
        return 0
    finally:
        if port_forward_proc:
            utils.log("Stopping Prometheus port-forward")
            port_forward_proc.terminate()
            try:
                port_forward_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                port_forward_proc.kill()


def start_port_forward(state: Dict[str, object], prometheus_url: str) -> subprocess.Popen[str]:
    """Start a kubectl port-forward to expose Prometheus locally."""
    utils.ensure_binary("kubectl")
    env = utils.build_kube_env(state)
    parsed = urlparse(prometheus_url)
    if parsed.hostname not in {"127.0.0.1", "localhost"}:
        raise RuntimeError("Port-forward only supported for localhost targets")
    local_port = parsed.port or 9090
    command = (
        "kubectl",
        "port-forward",
        "svc/prometheus",
        f"{local_port}:9090",
        "-n",
        "monitoring",
    )
    utils.log("Starting kubectl port-forward for Prometheus")
    proc = subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
        env=env,
    )
    start_time = time.time()
    while time.time() - start_time < 15:
        if proc.poll() is not None:
            raise RuntimeError("kubectl port-forward exited unexpectedly")
        if is_prometheus_ready(prometheus_url):
            return proc
        time.sleep(1)
    raise RuntimeError("Timed out waiting for port-forward to become ready")


if __name__ == "__main__":
    raise SystemExit(main())
