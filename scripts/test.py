#!/usr/bin/env python3
"""Run unit and integration tests for the pipeline."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import utils


def test_state_management() -> bool:
    """Test state save/load/update operations."""
    utils.log("Running state management tests...")
    
    # Create temporary state file
    original_state_file = utils.STATE_FILE
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        temp_state = Path(tmp.name)
    
    try:
        utils.STATE_FILE = temp_state
        
        # Test save
        test_data = {"cluster_name": "test", "kubeconfig": "/tmp/test"}
        utils.save_state(test_data)
        
        # Test load
        loaded = utils.load_state()
        assert loaded == test_data, "State load mismatch"
        
        # Test update
        utils.update_state({"new_key": "new_value"})
        updated = utils.load_state()
        assert updated["new_key"] == "new_value", "State update failed"
        assert updated["cluster_name"] == "test", "Original data lost"
        
        utils.log("  ✓ State management tests passed")
        return True
    except AssertionError as exc:
        utils.log(f"  ✗ State test failed: {exc}")
        return False
    finally:
        utils.STATE_FILE = original_state_file
        if temp_state.exists():
            temp_state.unlink()


def test_command_execution() -> bool:
    """Test subprocess command wrapper."""
    utils.log("Running command execution tests...")
    
    try:
        # Test successful command
        result = utils.run_cmd(("echo", "test"))
        assert result.returncode == 0, "Echo command failed"
        assert result.stdout == "test", f"Unexpected output: {result.stdout}"
        
        # Test failed command handling
        result = utils.run_cmd(("false",), check=False)
        assert result.returncode != 0, "False command should fail"
        
        utils.log("  ✓ Command execution tests passed")
        return True
    except (AssertionError, utils.CommandError) as exc:
        utils.log(f"  ✗ Command test failed: {exc}")
        return False


def test_manifest_validity() -> bool:
    """Validate Kubernetes manifest structure."""
    utils.log("Running manifest validation tests...")
    
    manifests = [
        utils.ROOT / "manifests/foo-deployment.yaml",
        utils.ROOT / "manifests/bar-deployment.yaml",
        utils.ROOT / "manifests/ingress.yaml",
    ]
    
    try:
        for manifest in manifests:
            if not manifest.exists():
                raise AssertionError(f"Manifest not found: {manifest}")
            
            # Basic YAML structure check
            content = manifest.read_text()
            if "apiVersion:" not in content or "kind:" not in content:
                raise AssertionError(f"Invalid manifest structure: {manifest}")
        
        utils.log("  ✓ Manifest validation tests passed")
        return True
    except AssertionError as exc:
        utils.log(f"  ✗ Manifest test failed: {exc}")
        return False


def test_percentile_calculation() -> bool:
    """Test load test percentile calculation logic."""
    utils.log("Running percentile calculation tests...")
    
    # Import the percentile function from load_test
    import sys
    sys.path.insert(0, str(utils.ROOT / "scripts"))
    from load_test import percentile
    
    try:
        # Test with known dataset
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        p50 = percentile(data, 0.50)
        assert 2.5 <= p50 <= 3.5, f"P50 out of range: {p50}"
        
        p90 = percentile(data, 0.90)
        assert 4.5 <= p90 <= 5.0, f"P90 out of range: {p90}"
        
        # Test edge cases
        assert percentile([], 0.50) == 0.0, "Empty list should return 0"
        assert percentile([1.0], 0.99) == 1.0, "Single element should return itself"
        
        utils.log("  ✓ Percentile calculation tests passed")
        return True
    except (AssertionError, ImportError) as exc:
        utils.log(f"  ✗ Percentile test failed: {exc}")
        return False


def test_pr_context_discovery() -> bool:
    """Test GitHub PR context extraction."""
    utils.log("Running PR context discovery tests...")
    
    import sys
    import os
    sys.path.insert(0, str(utils.ROOT / "scripts"))
    from post_comment import discover_pr_context
    
    try:
        original_env = {
            "GITHUB_EVENT_PATH": os.environ.pop("GITHUB_EVENT_PATH", None),
            "GITHUB_REPOSITORY": os.environ.pop("GITHUB_REPOSITORY", None),
        }

        # Without GitHub environment, should return None
        repo, pr = discover_pr_context()
        assert repo is None and pr is None, "Should return None outside CI"
        
        utils.log("  ✓ PR context discovery tests passed")
        return True
    except (AssertionError, ImportError) as exc:
        utils.log(f"  ✗ PR context test failed: {exc}")
        return False
    finally:
        for key, value in original_env.items():
            if value is not None:
                os.environ[key] = value


def main() -> int:
    print("🧪 Running test suite")
    print("=" * 40)
    
    utils.ensure_artifacts_dir()
    
    tests = [
        test_state_management(),
        test_command_execution(),
        test_manifest_validity(),
        test_percentile_calculation(),
        test_pr_context_discovery(),
    ]
    
    print()
    passed = sum(tests)
    total = len(tests)
    
    if all(tests):
        print(f"✅ All {total} tests passed!")
        return 0
    
    print(f"❌ {total - passed}/{total} tests failed")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
