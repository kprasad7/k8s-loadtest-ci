#!/bin/bash
set -euo pipefail

echo "🔍 Pre-flight validation checklist"
echo "===================================="

# Check Python version
echo -n "✓ Python 3.11+ ... "
python3 --version | grep -q "Python 3\.\(1[1-9]\|[2-9][0-9]\)" && echo "OK" || (echo "FAIL"; exit 1)

# Check dependencies
echo -n "✓ Python dependencies ... "
python3 -c "import github, requests" 2>/dev/null && echo "OK" || (echo "FAIL - run: pip install -r requirements.txt"; exit 1)

# Check binaries
echo -n "✓ Docker ... "
command -v docker >/dev/null 2>&1 && echo "OK" || (echo "FAIL"; exit 1)

echo -n "✓ kind ... "
command -v kind >/dev/null 2>&1 && echo "OK" || echo "SKIP (will install in CI)"

echo -n "✓ kubectl ... "
command -v kubectl >/dev/null 2>&1 && echo "OK" || echo "SKIP (will install in CI)"

# Validate Python syntax
echo -n "✓ Script syntax ... "
python3 -m py_compile scripts/*.py && echo "OK" || (echo "FAIL"; exit 1)

# Validate manifests structure
echo -n "✓ Manifest files ... "
test -f manifests/foo-deployment.yaml && \
test -f manifests/bar-deployment.yaml && \
test -f manifests/ingress.yaml && \
echo "OK" || (echo "FAIL"; exit 1)

# Check workflow file
echo -n "✓ GitHub Actions workflow ... "
test -f .github/workflows/ci.yml && echo "OK" || (echo "FAIL"; exit 1)

# Validate documentation
echo -n "✓ Documentation ... "
test -f README.md && test -f docs/DESIGN.md && echo "OK" || (echo "FAIL"; exit 1)

echo ""
echo "✅ All checks passed! Ready for deployment."
echo ""
echo "Next steps:"
echo "  1. Create a feature branch: git checkout -b test-ci"
echo "  2. Push and open a PR to trigger the workflow"
echo "  3. Review the automated load-test comment on the PR"
