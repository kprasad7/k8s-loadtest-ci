#!/usr/bin/env python3
"""Create a multi-node KinD cluster for the CI workflow."""
from __future__ import annotations

import argparse
from pathlib import Path
from textwrap import dedent
import time

import utils

KIND_CONFIG_NAME = "kind-config.yaml"
KUBECONFIG_NAME = "kubeconfig"

KIND_CONFIG_YAML = dedent(
    """
    kind: Cluster
    apiVersion: kind.x-k8s.io/v1alpha4
    nodes:
      - role: control-plane
        kubeadmConfigPatches:
          - |
            kind: InitConfiguration
            nodeRegistration:
              kubeletExtraArgs:
                node-labels: "ingress-ready=true"
        extraPortMappings:
          - containerPort: 80
            hostPort: 80
            protocol: TCP
          - containerPort: 443
            hostPort: 443
            protocol: TCP
      - role: worker
      - role: worker
    """
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create KinD cluster")
    parser.add_argument("--cluster-name", default="ci-loadtest", help="KinD cluster name")
    parser.add_argument("--wait", default="180s", help="Timeout for kind create cluster")
    return parser.parse_args()


def write_kind_config(path: Path) -> None:
    utils.ensure_artifacts_dir()
    path.write_text(KIND_CONFIG_YAML)


def main() -> int:
    args = parse_args()
    utils.ensure_artifacts_dir()
    utils.ensure_binary("kind")

    kind_config_path = utils.ARTIFACTS / KIND_CONFIG_NAME
    write_kind_config(kind_config_path)

    kubeconfig_path = utils.ARTIFACTS / KUBECONFIG_NAME

    utils.log("Ensuring no stale KinD cluster exists")
    utils.run_cmd(("kind", "delete", "cluster", "--name", args.cluster_name), check=False)

    utils.log(f"Creating KinD cluster '{args.cluster_name}'")
    utils.run_cmd(
        (
            "kind",
            "create",
            "cluster",
            "--name",
            args.cluster_name,
            "--config",
            str(kind_config_path),
            "--wait",
            args.wait,
        )
    )

    kubeconfig = utils.run_cmd(("kind", "get", "kubeconfig", "--name", args.cluster_name)).stdout
    kubeconfig_path.write_text(kubeconfig)
    utils.log(f"Kubeconfig written to {kubeconfig_path}")

    utils.update_state(
        {
            "cluster_name": args.cluster_name,
            "kubeconfig": str(kubeconfig_path),
            "kind_config": str(kind_config_path),
            "cluster_created_at": time.time(),
        }
    )
    utils.write_github_env("KUBECONFIG", str(kubeconfig_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
