#!/usr/bin/env python3
"""Pre-flight validation for the CI pipeline."""
from __future__ import annotations

import subprocess
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
    required_packages = ["github", "requests"]
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if not missing:
        utils.log("✓ Python dependencies ... OK")
        return True
    
    utils.log(f"✗ Missing dependencies: {', '.join(missing)}")
    utils.log(f"  Run: pip install -r requirements.txt")
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


def check_docker_daemon() -> bool:
    """Verify Docker daemon is actually running."""
    try:
        utils.ensure_binary("docker")
        subprocess.run(
            ["docker", "ps"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=True,
        )
        utils.log("✓ Docker daemon running ... OK")
        return True
    except FileNotFoundError:
        utils.log("✗ Docker ... FAIL (not installed)")
        return False
    except subprocess.TimeoutExpired:
        utils.log("✗ Docker daemon ... FAIL (timeout connecting to daemon)")
        utils.log("  Check: Is Docker running? Try: docker ps")
        return False
    except subprocess.CalledProcessError:
        utils.log("✗ Docker daemon ... FAIL (permission denied or not running)")
        utils.log("  Check: docker ps works? Try: sudo usermod -aG docker $USER")
        return False


def check_manifests() -> bool:
    """Verify all required Kubernetes manifests exist."""
    manifests = {
        "Base deployments": [
            utils.ROOT / "manifests/base/foo-deployment.yaml",
            utils.ROOT / "manifests/base/bar-deployment.yaml",
        ],
        "Base ingress": [
            utils.ROOT / "manifests/base/ingress.yaml",
            utils.ROOT / "manifests/base/kustomization.yaml",
        ],
        "Monitoring": [
            utils.ROOT / "manifests/prometheus.yaml",
        ],
        "Kustomize overlays": [
            utils.ROOT / "manifests/overlays/production/kustomization.yaml",
        ],
    }
    
    all_exist = True
    for category, files in manifests.items():
        if all(f.exists() for f in files):
            utils.log(f"✓ {category} ... OK")
        else:
            missing = [f.name for f in files if not f.exists()]
            utils.log(f"✗ {category} ... FAIL (missing: {', '.join(missing)})")
            all_exist = False
    
    return all_exist


def check_workflow() -> bool:
    """Verify GitHub Actions workflow exists."""
    workflow = utils.ROOT / ".github/workflows/ci.yml"
    if workflow.exists():
        utils.log("✓ GitHub Actions workflow ... OK")
        return True
    utils.log("✗ GitHub Actions workflow ... FAIL")
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
    """Run all pre-flight checks."""
    utils.log("🔍 Pre-flight validation checklist")
    utils.log("=" * 50)
    utils.log("")
    
    # Critical checks (must pass)
    utils.log("CRITICAL CHECKS:")
    critical_checks = [
        check_python_version(),
        check_dependencies(),
        check_docker_daemon(),
    ]
    
    utils.log("")
    utils.log("ENVIRONMENT CHECKS:")
    env_checks = [
        check_binary("docker", required=True),
        check_binary("kind", required=False),
        check_binary("kubectl", required=False),
    ]
    
    utils.log("")
    utils.log("PROJECT CHECKS:")
    project_checks = [
        validate_script_syntax(),
        check_manifests(),
        check_workflow(),
    ]
    
    all_checks = critical_checks + env_checks + project_checks
    
    utils.log("")
    utils.log("=" * 50)
    if all(all_checks):
        utils.log("✅ All checks passed! Ready for deployment.")
        utils.log("")
        utils.log("Next steps:")
        utils.log("  1. Create a feature branch: git checkout -b test-ci")
        utils.log("  2. Push and open a PR to trigger the workflow")
        utils.log("  3. Review the automated load-test comment on the PR")
        return 0
    
    utils.log("❌ Some checks failed. Please fix the issues above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
