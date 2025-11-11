#!/usr/bin/env python3
"""Delete the KinD cluster if it exists."""
from __future__ import annotations

import argparse
from pathlib import Path

import utils


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Delete KinD cluster")
    parser.add_argument("--cluster-name", help="Cluster name override")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    state = utils.load_state()
    cluster_name = args.cluster_name or state.get("cluster_name")
    if not cluster_name:
        utils.log("No cluster information found in state; skipping delete")
        return 0

    utils.ensure_binary("kind")
    utils.log(f"Deleting KinD cluster '{cluster_name}'")
    utils.run_cmd(("kind", "delete", "cluster", "--name", cluster_name), check=False)

    kubeconfig_path = state.get("kubeconfig")
    if kubeconfig_path:
        path = Path(kubeconfig_path)
        if path.exists():
            path.unlink()
            utils.log(f"Removed kubeconfig at {path}")

    kind_config_path = state.get("kind_config")
    if kind_config_path:
        path = Path(kind_config_path)
        if path.exists():
            path.unlink()
            utils.log(f"Removed KinD config at {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
