#!/usr/bin/env python3
"""Deploy ingress controller and echo workloads."""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import utils

INGRESS_CONTROLLER_MANIFEST = (
    "https://raw.githubusercontent.com/kubernetes/ingress-nginx/"
    "controller-v1.9.4/deploy/static/provider/kind/deploy.yaml"
)
NAMESPACE_MANIFEST = """apiVersion: v1
kind: Namespace
metadata:
  name: echo
"""
MANIFEST_FILES = [
    Path("manifests/foo-deployment.yaml"),
    Path("manifests/bar-deployment.yaml"),
    Path("manifests/ingress.yaml"),
    Path("manifests/prometheus.yaml"),
]


def wait_until_job_exists(job: str, env) -> None:
    """Poll until the specified job is created before waiting on completion."""
    deadline = time.time() + 120
    while time.time() < deadline:
        result = utils.run_cmd(
            (
                "kubectl",
                "get",
                "job",
                job,
                "--namespace",
                "ingress-nginx",
            ),
            env=env,
            check=False,
        )
        if result.returncode == 0:
            return
        time.sleep(3)
    raise RuntimeError(f"Timed out waiting for job {job} to be created")


def wait_for_ingress_ready(env) -> None:
    """Ensure ingress-nginx controller and admission webhook are ready."""
    utils.log("Waiting for ingress-nginx controller pods to become Ready")
    utils.run_cmd(
        (
            "kubectl",
            "wait",
            "--namespace",
            "ingress-nginx",
            "--for=condition=Ready",
            "pod",
            "-l",
            "app.kubernetes.io/component=controller",
            "--timeout=180s",
        ),
        env=env,
    )

    utils.log("Ensuring ingress-nginx admission webhook jobs have completed")
    for job in ("ingress-nginx-admission-create", "ingress-nginx-admission-patch"):
        wait_until_job_exists(job, env)
        utils.run_cmd(
            (
                "kubectl",
                "wait",
                "--namespace",
                "ingress-nginx",
                "--for=condition=complete",
                f"job/{job}",
                "--timeout=120s",
            ),
            env=env,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deploy workloads onto KinD")
    parser.add_argument("--namespace", default="echo")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    state = utils.load_state()
    env = utils.build_kube_env(state)

    utils.ensure_binary("kubectl")
    utils.log("Creating namespace if missing")
    utils.run_cmd(("kubectl", "apply", "-f", "-"), env=env, input_data=NAMESPACE_MANIFEST)

    utils.log("Installing ingress-nginx controller")
    utils.run_cmd(("kubectl", "apply", "-f", INGRESS_CONTROLLER_MANIFEST), env=env)

    wait_for_ingress_ready(env)

    for manifest in MANIFEST_FILES:
        full_path = utils.ROOT / manifest
        utils.log(f"Applying manifest {full_path}")
        utils.run_cmd(("kubectl", "apply", "-f", str(full_path)), env=env)

    utils.update_state({"namespace": args.namespace})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
