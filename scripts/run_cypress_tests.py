#!/usr/bin/env python3
"""Run Cypress end-to-end tests against deployed services."""

import subprocess
import sys
import json
from pathlib import Path

import utils


def run_cypress_tests() -> bool:
    """
    Run Cypress E2E tests.
    
    Returns:
        True if all tests passed, False otherwise
    """
    utils.log("🧪 Running Cypress E2E tests")
    utils.log("=" * 40)

    try:
        # Run Cypress in headless mode with JSON reporter
        result = subprocess.run(
            [
                "cypress",
                "run",
                "--headless",
                "--browser",
                "chrome",
                "--reporter",
                "json",
                "--reporter-options",
                'reportDir=artifacts,reportFilename=cypress-results.json'
            ],
            cwd=str(utils.ROOT),
            capture_output=True,
            text=True,
            timeout=300,
        )

        # Log the output
        if result.stdout:
            utils.log(result.stdout)
        if result.stderr:
            utils.log(f"[STDERR] {result.stderr}")

        # Check if tests passed
        if result.returncode == 0:
            utils.log("✅ All Cypress tests passed!")
            return True
        else:
            utils.log(f"❌ Cypress tests failed with exit code {result.returncode}")
            return False

    except subprocess.TimeoutExpired:
        utils.log("❌ Cypress tests timed out (5 minutes exceeded)")
        return False
    except FileNotFoundError:
        utils.log("❌ Cypress is not installed. Run: npm install -g cypress")
        return False
    except Exception as e:
        utils.log(f"❌ Error running Cypress tests: {e}")
        return False


def generate_cypress_report() -> None:
    """Generate a markdown report from Cypress JSON results."""
    results_file = utils.ARTIFACTS / "cypress-results.json"
    
    if not results_file.exists():
        utils.log("⚠️  No Cypress results file found")
        return

    try:
        with open(results_file, 'r') as f:
            results = json.load(f)

        # Extract test statistics
        stats = results.get('stats', {})
        tests = stats.get('tests', 0)
        passes = stats.get('passes', 0)
        failures = stats.get('failures', 0)
        duration = stats.get('duration', 0)

        # Generate markdown report
        report_content = f"""### 🧪 Cypress E2E Test Results

| Metric | Value |
|--------|-------|
| Total Tests | {tests} |
| ✅ Passed | {passes} |
| ❌ Failed | {failures} |
| ⏱️ Duration | {duration / 1000:.2f}s |
| Success Rate | {(passes / tests * 100):.1f}% |

"""
        
        # Add per-file results
        if 'results' in results:
            report_content += "### 📋 Test Files\n\n"
            for result in results.get('results', []):
                file_name = result.get('file', 'unknown')
                file_tests = result.get('stats', {}).get('tests', 0)
                file_passes = result.get('stats', {}).get('passes', 0)
                file_failures = result.get('stats', {}).get('failures', 0)
                
                status = "✅" if file_failures == 0 else "❌"
                report_content += f"{status} **{file_name}**: {file_passes}/{file_tests} passed\n"

        # Save markdown report
        report_file = utils.ARTIFACTS / "cypress-results.md"
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        utils.log(f"📊 Report saved to {report_file}")

    except Exception as e:
        utils.log(f"⚠️  Error generating report: {e}")


def main():
    """Main entry point."""
    try:
        # Ensure artifacts directory exists
        utils.ARTIFACTS.mkdir(parents=True, exist_ok=True)

        # Run tests
        success = run_cypress_tests()

        # Generate report
        generate_cypress_report()

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        utils.log("\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        utils.log(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
