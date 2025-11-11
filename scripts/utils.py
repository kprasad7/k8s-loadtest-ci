#!/usr/bin/env python3
"""Shared helpers for the load-test automation pipeline."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Sequence

ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = ROOT / "artifacts"
STATE_FILE = ARTIFACTS / "state.json"


@dataclass
class CommandResult:
    command: Sequence[str]
    returncode: int
    stdout: str
    stderr: str


class CommandError(RuntimeError):
    """Raised when a subprocess exits with a non-zero status."""


def ensure_artifacts_dir() -> None:
    ARTIFACTS.mkdir(exist_ok=True)


def log(message: str) -> None:
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def ensure_binary(name: str) -> None:
    if shutil.which(name) is None:
        raise FileNotFoundError(f"Required binary '{name}' not found on PATH")


def run_cmd(
    command: Sequence[str],
    *,
    check: bool = True,
    capture_output: bool = True,
    env: Optional[Dict[str, str]] = None,
    cwd: Optional[Path] = None,
    input_data: Optional[str] = None,
) -> CommandResult:
    log(f"$ {' '.join(command)}")
    completed = subprocess.run(
        list(command),
        check=False,
        capture_output=capture_output,
        text=True,
        env=env,
        cwd=cwd,
        input=input_data,
    )
    result = CommandResult(
        command=command,
        returncode=completed.returncode,
        stdout=(completed.stdout or "").strip(),
        stderr=(completed.stderr or "").strip(),
    )
    if check and result.returncode != 0:
        raise CommandError(
            f"Command {' '.join(command)} failed with exit code {result.returncode}\n"
            f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )
    return result


def load_state() -> Dict[str, object]:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text())
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse state file: {STATE_FILE}") from exc


def save_state(state: Dict[str, object]) -> None:
    ensure_artifacts_dir()
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True))


def update_state(updates: Dict[str, object]) -> Dict[str, object]:
    state = load_state()
    state.update(updates)
    save_state(state)
    return state


def build_kube_env(state: Dict[str, object]) -> Dict[str, str]:
    kubeconfig = state.get("kubeconfig")
    if not kubeconfig:
        raise RuntimeError("Kubeconfig path missing from state; did create_cluster run?")
    path = Path(str(kubeconfig))
    if not path.exists():
        raise RuntimeError(f"Kubeconfig not found at {path}; re-run create_cluster")
    env = os.environ.copy()
    env["KUBECONFIG"] = str(path)
    return env


def write_github_env(key: str, value: str) -> None:
    target = os.getenv("GITHUB_ENV")
    if not target:
        return
    with open(target, "a", encoding="utf-8") as handle:
        handle.write(f"{key}={value}\n")


def read_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text())


def write_file(path: Path, content: str) -> None:
    ensure_artifacts_dir()
    path.write_text(content)
