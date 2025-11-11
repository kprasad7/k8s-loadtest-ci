#!/usr/bin/env python3
"""Verify cluster, ingress, and workloads are healthy."""
from __future__ import annotations

import argparse

import utils

DEFAULT_TIMEOUT = "180s"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check workload health")
    parser.add_argument("--namespace", default="echo")
    parser.add_argument("--timeout", default=DEFAULT_TIMEOUT)
    return parser.parse_args()


def wait_for_nodes(env, timeout: str) -> None:
    utils.log("Waiting for nodes to become Ready")
    utils.run_cmd(("kubectl", "wait", "--for=condition=Ready", "nodes", "--all", f"--timeout={timeout}"), env=env)


def wait_for_ingress_controller(env, timeout: str) -> None:
    utils.log("Waiting for ingress-nginx controller pod")
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
            f"--timeout={timeout}",
        ),
        env=env,
    )


def wait_for_deployments(env, namespace: str, timeout: str) -> None:
    for deployment in ("echo-foo", "echo-bar"):
        utils.log(f"Waiting for deployment {namespace}/{deployment}")
        utils.run_cmd(
            (
                "kubectl",
                "rollout",
                "status",
                f"deployment/{deployment}",
                "--namespace",
                namespace,
                f"--timeout={timeout}",
            ),
            env=env,
        )


def main() -> int:
    args = parse_args()
    state = utils.load_state()
    env = utils.build_kube_env(state)

    utils.ensure_binary("kubectl")
    wait_for_nodes(env, args.timeout)
    wait_for_ingress_controller(env, args.timeout)
    wait_for_deployments(env, args.namespace, args.timeout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
