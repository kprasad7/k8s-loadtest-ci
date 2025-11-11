#!/usr/bin/env python3
"""Pre-flight validation for the CI pipeline."""
from __future__ import annotations

import sys
from pathlib import Path

import utils


def check_python_version() -> bool:
    """Verify Python 3.11+ is installed."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        utils.log("✓ Python 3.11+ ... OK")
        return True
    utils.log(f"✗ Python version {version.major}.{version.minor} < 3.11")
    return False


def check_dependencies() -> bool:
    """Verify required Python packages are installed."""
    try:
        import github  # noqa: F401
        import requests  # noqa: F401
        utils.log("✓ Python dependencies ... OK")
        return True
    except ImportError as exc:
        utils.log(f"✗ Missing dependency: {exc.name}")
        utils.log("  Run: pip install -r requirements.txt")
        return False


def check_binary(name: str, required: bool = True) -> bool:
    """Check if a binary exists on PATH."""
    try:
        utils.ensure_binary(name)
        utils.log(f"✓ {name} ... OK")
        return True
    except FileNotFoundError:
        if required:
            utils.log(f"✗ {name} ... FAIL")
            return False
        utils.log(f"✓ {name} ... SKIP (will install in CI)")
        return True


def check_manifests() -> bool:
    """Verify all required Kubernetes manifests exist."""
    manifests = [
        utils.ROOT / "manifests/foo-deployment.yaml",
        utils.ROOT / "manifests/bar-deployment.yaml",
        utils.ROOT / "manifests/ingress.yaml",
    ]
    if all(m.exists() for m in manifests):
        utils.log("✓ Manifest files ... OK")
        return True
    utils.log("✗ Manifest files ... FAIL")
    return False


def check_workflow() -> bool:
    """Verify GitHub Actions workflow exists."""
    workflow = utils.ROOT / ".github/workflows/ci.yml"
    if workflow.exists():
        utils.log("✓ GitHub Actions workflow ... OK")
        return True
    utils.log("✗ GitHub Actions workflow ... FAIL")
    return False


def check_documentation() -> bool:
    """Verify documentation files exist."""
    docs = [
        utils.ROOT / "README.md",
        utils.ROOT / "docs/DESIGN.md",
    ]
    if all(d.exists() for d in docs):
        utils.log("✓ Documentation ... OK")
        return True
    utils.log("✗ Documentation ... FAIL")
    return False


def validate_script_syntax() -> bool:
    """Compile all Python scripts to check for syntax errors."""
    import py_compile
    
    scripts_dir = utils.ROOT / "scripts"
    try:
        for script in scripts_dir.glob("*.py"):
            py_compile.compile(str(script), doraise=True)
        utils.log("✓ Script syntax ... OK")
        return True
    except py_compile.PyCompileError as exc:
        utils.log(f"✗ Script syntax error: {exc}")
        return False


def main() -> int:
    print("🔍 Pre-flight validation checklist")
    print("=" * 40)
    
    checks = [
        check_python_version(),
        check_dependencies(),
        check_binary("docker", required=True),
        check_binary("kind", required=False),
        check_binary("kubectl", required=False),
        validate_script_syntax(),
        check_manifests(),
        check_workflow(),
        check_documentation(),
    ]
    
    print()
    if all(checks):
        print("✅ All checks passed! Ready for deployment.")
        print()
        print("Next steps:")
        print("  1. Create a feature branch: git checkout -b test-ci")
        print("  2. Push and open a PR to trigger the workflow")
        print("  3. Review the automated load-test comment on the PR")
        return 0
    
    print("❌ Some checks failed. Please fix the issues above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
