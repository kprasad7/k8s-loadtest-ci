#!/usr/bin/env python3
"""Post the load-test summary as a PR comment when appropriate."""
from __future__ import annotations

import json
import os
from pathlib import Path

from github import Github

import utils


def discover_pr_context() -> tuple[str, int] | tuple[None, None]:
    event_path = os.getenv("GITHUB_EVENT_PATH")
    if not event_path:
        return (None, None)
    event_file = Path(event_path)
    if not event_file.exists():
        return (None, None)
    try:
        payload = json.loads(event_file.read_text())
    except json.JSONDecodeError:
        return (None, None)
    pull = payload.get("pull_request")
    repo = os.getenv("GITHUB_REPOSITORY")
    if not pull or not repo:
        return (None, None)
    number = pull.get("number")
    if not number:
        return (None, None)
    return (repo, int(number))


def main() -> int:
    state = utils.load_state()
    load_state = state.get("load_test")
    if not load_state:
        utils.log("No load-test state available; skipping PR comment")
        return 0

    markdown_path = Path(load_state.get("markdown", utils.ARTIFACTS / "load-test-results.md"))
    if not markdown_path.exists():
        utils.log(f"Load-test summary not found at {markdown_path}; skipping comment")
        return 0

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        utils.log("GITHUB_TOKEN not provided; skipping comment")
        return 0

    repo_name, pr_number = discover_pr_context()
    if not repo_name or not pr_number:
        utils.log("Not running in the context of a pull request; skipping comment")
        return 0

    body = markdown_path.read_text()
    utils.log(f"Posting load-test comment to {repo_name} PR #{pr_number}")
    gh = Github(token)
    repo = gh.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    pr.create_issue_comment(body)
    utils.log("Comment posted successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
