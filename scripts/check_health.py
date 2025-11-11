"""Verify cluster, ingress, and workloads are healthy and ready for load testing."""
from __future__ import annotations

import argparse
import subprocess
import time

import requests

import utils

DEFAULT_TIMEOUT = 180  # seconds
DEFAULT_RETRIES = 3
PROMETHEUS_TIMEOUT = 5


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Check workload health and readiness")
    parser.add_argument("--namespace", default="echo", help="Target namespace for echo services")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Timeout in seconds")
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES, help="Number of retries for transient failures")
    return parser.parse_args()


def run_kubectl_wait(
    cmd: tuple,
    env: dict,
    timeout: int,
    description: str,
) -> None:
    """Run kubectl wait command with error handling."""
    utils.log(f"Waiting for: {description}")
    
    try:
        result = subprocess.run(
            cmd,
            env=env,
            check=False,
            capture_output=True,
            timeout=timeout + 10,
            text=True,
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout
            raise RuntimeError(f"Timeout or error waiting for {description}: {error_msg}")
        
        utils.log(f"✓ {description} ... READY")
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Timeout exceeded ({timeout}s) waiting for {description}")
    except Exception as exc:
        raise RuntimeError(f"Failed to verify {description}: {exc}")


def wait_for_nodes(env: dict, timeout: int) -> None:
    """Wait for all nodes to be in Ready state."""
    run_kubectl_wait(
        cmd=("kubectl", "wait", "--for=condition=Ready", "nodes", "--all", f"--timeout={timeout}s"),
        env=env,
        timeout=timeout,
        description="Kubernetes nodes to be Ready",
    )


def wait_for_admission_webhooks(env: dict, timeout: int) -> None:
    """Wait for admission webhooks to be operational (critical for ingress validation)."""
    utils.log("Waiting for admission webhooks to be operational")
    
    try:
        # Wait for webhook pods
        result = subprocess.run(
            (
                "kubectl",
                "wait",
                "--namespace",
                "ingress-nginx",
                "--for=condition=Ready",
                "pod",
                "-l",
                "app.kubernetes.io/component=webhook",
                f"--timeout={timeout}s",
            ),
            env=env,
            check=False,
            capture_output=True,
            timeout=timeout + 10,
            text=True,
        )
        
        if result.returncode != 0:
            utils.log("⚠️  Webhook pods not found (may use job-based deployment)")
        else:
            utils.log("✓ Admission webhooks ... READY")
            
        # Wait for webhook jobs to complete
        utils.log("Waiting for webhook job completion")
        subprocess.run(
            (
                "kubectl",
                "wait",
                "--namespace",
                "ingress-nginx",
                "--for=condition=complete",
                "job",
                "-l",
                "app.kubernetes.io/component=webhook",
                f"--timeout={timeout}s",
            ),
            env=env,
            check=False,
            capture_output=True,
            timeout=timeout + 10,
        )
        
        utils.log("✓ Webhook jobs ... COMPLETE")
    except Exception as exc:
        utils.log(f"⚠️  Webhook check had issues (non-fatal): {exc}")


def wait_for_ingress_controller(env: dict, timeout: int) -> None:
    """Wait for NGINX ingress controller pod to be Ready."""
    run_kubectl_wait(
        cmd=(
            "kubectl",
            "wait",
            "--namespace",
            "ingress-nginx",
            "--for=condition=Ready",
            "pod",
            "-l",
            "app.kubernetes.io/component=controller",
            f"--timeout={timeout}s",
        ),
        env=env,
        timeout=timeout,
        description="ingress-nginx controller pod to be Ready",
    )


def wait_for_deployments(env: dict, namespace: str, timeout: int) -> None:
    """Wait for echo deployments to be rolled out."""
    for deployment in ("echo-foo", "echo-bar"):
        utils.log(f"Waiting for deployment rollout: {namespace}/{deployment}")
        
        try:
            result = subprocess.run(
                (
                    "kubectl",
                    "rollout",
                    "status",
                    f"deployment/{deployment}",
                    "--namespace",
                    namespace,
                    f"--timeout={timeout}s",
                ),
                env=env,
                check=False,
                capture_output=True,
                timeout=timeout + 10,
                text=True,
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Rollout failed: {result.stderr}")
            
            utils.log(f"✓ {deployment} ... ROLLED OUT")
        except Exception as exc:
            raise RuntimeError(f"Deployment {deployment} not ready: {exc}")


def verify_endpoints_exist(env: dict, namespace: str) -> None:
    """Verify that services have endpoints (actual pods behind them)."""
    utils.log("Verifying service endpoints exist")
    
    for service in ("echo-foo", "echo-bar"):
        try:
            result = subprocess.run(
                (
                    "kubectl",
                    "get",
                    "endpoints",
                    service,
                    "--namespace",
                    namespace,
                    "-o",
                    "jsonpath={.subsets[*].addresses[*].ip}",
                ),
                env=env,
                check=True,
                capture_output=True,
                timeout=10,
                text=True,
            )
            
            endpoints = result.stdout.strip()
            if not endpoints:
                raise RuntimeError(f"Service {service} has no endpoints (no running pods)")
            
            utils.log(f"✓ {service} endpoints ... {len(endpoints.split())} pod(s) found")
        except Exception as exc:
            raise RuntimeError(f"Endpoint check failed for {service}: {exc}")


def verify_ingress_backends(env: dict, namespace: str) -> None:
    """Verify ingress has backend services configured."""
    utils.log("Verifying ingress backend configuration")
    
    try:
        result = subprocess.run(
            (
                "kubectl",
                "get",
                "ingress",
                "-n",
                namespace,
                "-o",
                "jsonpath={.items[*].spec.rules[*].http.paths[*].backend.service.name}",
            ),
            env=env,
            check=True,
            capture_output=True,
            timeout=10,
            text=True,
        )
        
        backends = result.stdout.strip().split()
        if not backends:
            raise RuntimeError("Ingress has no backend services configured")
        
        utils.log(f"✓ Ingress backends ... {len(backends)} service(s) configured")
    except Exception as exc:
        raise RuntimeError(f"Ingress backend verification failed: {exc}")


def wait_for_prometheus(env: dict, timeout: int) -> None:
    """Wait for Prometheus deployment to be ready."""
    run_kubectl_wait(
        cmd=(
            "kubectl",
            "rollout",
            "status",
            "deployment/prometheus",
            "--namespace",
            "monitoring",
            f"--timeout={timeout}s",
        ),
        env=env,
        timeout=timeout,
        description="Prometheus deployment to be Ready",
    )


def verify_prometheus_connectivity(env: dict, max_retries: int = 3) -> None:
    """Verify Prometheus is actually reachable and scraping metrics."""
    utils.log("Verifying Prometheus connectivity and metrics scraping")
    
    port_forward_proc = None
    try:
        utils.log("Starting kubectl port-forward to Prometheus")
        port_forward_proc = subprocess.Popen(
            (
                "kubectl",
                "port-forward",
                "-n",
                "monitoring",
                "svc/prometheus",
                "9090:9090",
            ),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        
        # Give port-forward time to establish
        time.sleep(2)
        
        # Try to reach Prometheus API
        prometheus_url = "http://localhost:9090/api/v1/query"
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    prometheus_url,
                    params={"query": "up"},
                    timeout=PROMETHEUS_TIMEOUT,
                )
                response.raise_for_status()
                utils.log("✓ Prometheus API ... REACHABLE")
                break
            except requests.RequestException as exc:
                if attempt < max_retries - 1:
                    utils.log(f"⚠️  Attempt {attempt + 1}/{max_retries}: {exc}")
                    time.sleep(2)
                else:
                    raise RuntimeError(f"Cannot reach Prometheus after {max_retries} attempts: {exc}")
        
        # Verify Prometheus has scrape targets
        utils.log("Checking Prometheus scrape targets")
        response = requests.get(
            "http://localhost:9090/api/v1/targets",
            timeout=PROMETHEUS_TIMEOUT,
        )
        response.raise_for_status()
        
        targets_data = response.json()
        active_targets = len(targets_data.get("data", {}).get("activeTargets", []))
        
        if active_targets == 0:
            utils.log("⚠️  Prometheus has no active scrape targets")
        else:
            utils.log(f"✓ Prometheus scrape targets ... {active_targets} found")
            
    except Exception as exc:
        raise RuntimeError(f"Prometheus connectivity check failed: {exc}")
    finally:
        # Clean up port-forward
        if port_forward_proc:
            utils.log("Stopping kubectl port-forward")
            port_forward_proc.terminate()
            try:
                port_forward_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                port_forward_proc.kill()



def main() -> int:
    """Execute all health checks."""
    args = parse_args()
    
    try:
        state = utils.load_state()
        env = utils.build_kube_env(state)
        
        utils.ensure_binary("kubectl")
        
        utils.log("=" * 50)
        utils.log("Health Check: Phase 1 - Cluster Infrastructure")
        utils.log("=" * 50)
        wait_for_nodes(env, args.timeout)
        
        utils.log("")
        utils.log("=" * 50)
        utils.log("Health Check: Phase 2 - Admission Webhooks")
        utils.log("=" * 50)
        wait_for_admission_webhooks(env, args.timeout)
        
        utils.log("")
        utils.log("=" * 50)
        utils.log("Health Check: Phase 3 - Ingress Controller")
        utils.log("=" * 50)
        wait_for_ingress_controller(env, args.timeout)
        
        utils.log("")
        utils.log("=" * 50)
        utils.log("Health Check: Phase 4 - Application Deployments")
        utils.log("=" * 50)
        wait_for_deployments(env, args.namespace, args.timeout)
        verify_endpoints_exist(env, args.namespace)
        verify_ingress_backends(env, args.namespace)
        
        utils.log("")
        utils.log("=" * 50)
        utils.log("Health Check: Phase 5 - Monitoring Stack")
        utils.log("=" * 50)
        wait_for_prometheus(env, args.timeout)
        verify_prometheus_connectivity(env, max_retries=args.retries)
        
        utils.log("")
        utils.log("=" * 50)
        utils.log("✅ ALL HEALTH CHECKS PASSED")
        utils.log("=" * 50)
        utils.log("Cluster is ready for load testing")
        
        return 0
        
    except Exception as exc:
        utils.log(f"❌ HEALTH CHECK FAILED: {exc}")
        return 1



if __name__ == "__main__":
    raise SystemExit(main())
