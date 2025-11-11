# 🚀 Quick Start Guide

**Get up and running in 5 minutes.**

---

## 📋 Prerequisites

Before you start, ensure your system has:

| Requirement | Minimum Version | Check Command | Install |
|-------------|-----------------|---------------|---------|
| **Python** | 3.11+ | `python3 --version` | `apt install python3.11` |
| **Docker** | 24+ | `docker --version` | `apt install docker.io` |
| **Git** | 2.40+ | `git --version` | `apt install git` |
| **curl** | Any | `curl --version` | `apt install curl` |
| **pip** | Latest | `pip --version` | `python3 -m pip install --upgrade pip` |

### Optional (for local testing only)
| Tool | Purpose | Check | Install |
|------|---------|-------|---------|
| **kind** | Local KinD cluster | `kind --version` | `curl -Lo kind https://kind.sigs.k8s.io/dl/v0.22.0/kind-linux-amd64 && chmod +x kind && sudo mv kind /usr/local/bin/` |
| **kubectl** | K8s CLI | `kubectl version --client` | `curl -Lo kubectl https://dl.k8s.io/release/v1.29.2/bin/linux/amd64/kubectl && chmod +x kubectl && sudo mv kubectl /usr/local/bin/` |

### Quick Prereq Check

```bash
# Run this to verify everything is installed
python -c "import sys; assert sys.version_info >= (3,11), 'Python 3.11+ required'"
docker ps > /dev/null || echo "⚠️  Docker not running; start it with: sudo systemctl start docker"
git --version > /dev/null && echo "✓ Git ready" || echo "✗ Git missing"
```

---

## 1️⃣ One-Time Setup

```bash
# Clone the repository
git clone https://github.com/kprasad7/k8s-loadtest-ci.git
cd k8s-loadtest-ci

# Install Python dependencies
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Verify environment is ready
python3 scripts/validate.py
```

**Expected output:**
```
🔍 Pre-flight validation checklist
========================================
[HH:MM:SS] ✓ Python 3.11+ ... OK
[HH:MM:SS] ✓ Python dependencies ... OK
[HH:MM:SS] ✓ docker ... OK
[HH:MM:SS] ✓ Script syntax ... OK
[HH:MM:SS] ✓ Manifest files ... OK
[HH:MM:SS] ✓ Documentation ... OK

✅ All checks passed! Ready for deployment.
```

---

## 2️⃣ Run the Full Pipeline Locally

```bash
# Execute the complete end-to-end pipeline
python3 scripts/create_cluster.py && \
python3 scripts/deploy.py && \
python3 scripts/check_health.py && \
python3 scripts/load_test.py && \
python3 scripts/monitor_resources.py && \
python3 scripts/delete_cluster.py
```

**What happens:**
```
[12:42:03] Creating KinD cluster 'ci-loadtest'
[12:42:49] ✓ Cluster ready (3 nodes)
[12:42:49] Installing ingress-nginx controller
[12:42:50] Deploying echo-foo and echo-bar
[12:43:15] ✓ All deployments ready
[12:43:21] Sending 200 load test requests
[12:43:26] ✓ Load test complete (100% success)
[12:43:26] Collecting resource metrics from Prometheus
[12:43:57] ✓ Metrics saved
[12:44:06] Deleting KinD cluster
[12:44:10] ✓ Cleanup complete
```
## 3️⃣ Trigger CI via GitHub (The Main Flow)

### Option A: Via Git CLI
```bash
# Create feature branch
git checkout -b test/my-feature

# Make a small change (e.g., update README)
echo "# Test PR" >> README.md

# Commit and push
git add .
git commit -m "test: trigger CI workflow"
git push origin test/my-feature

# Open PR (CLI)
gh pr create --base main --head test/my-feature --title "Test CI" --body "Triggering automated load test"
```

### Option B: Via GitHub Web UI
1. Push your branch: `git push origin test/my-feature`
2. Go to https://github.com/kprasad7/k8s-loadtest-ci
3. Click "Compare & pull request"
4. Create PR targeting `main`

### What Happens Automatically
✅ GitHub Actions triggered  
✅ Environment validated  
✅ Tests run  
✅ Security scan executed  
✅ KinD cluster provisioned  
✅ Workloads deployed  
✅ Health checks pass  
✅ Load test executed  
✅ Resource metrics collected  
✅ Results posted to PR comment  
✅ Resources cleaned up  

**Total time: ~3 minutes**


# 🚀 Kubernetes Load Test CI Pipeline

**GitHub Actions workflow** that automatically provisions a multi-node Kubernetes cluster, deploys load-balanced services, executes sophisticated load testing, monitors resource utilization with Prometheus, performs security scanning, and reports results back to your pull request—all in under 3 minutes.

> 🎯 **One PR trigger. Full end-to-end infrastructure validation.** No manual intervention required.

---

## 📑 Quick Navigation

- [What This Does](#-what-this-does)
- [Architecture Overview](#-architecture-overview)
- [File Structure](#-file-structure)
- [Features at a Glance](#-features-at-a-glance)
- [Getting Started](#-getting-started)
- [How the CI Pipeline Works](#-how-the-ci-pipeline-works)
- [Understanding the Reports](#-understanding-the-reports)
- [Running Locally](#-running-locally)
- [Troubleshooting](#-troubleshooting)
- [Production Considerations](#-production-considerations)

---

## 🎯 What This Does

Every time you open a pull request to `main`, this system automatically:

1. **Provisions** a 3-node Kubernetes cluster (KinD)
2. **Deploys** dual HTTP echo services behind an ingress
3. **Routes** traffic via hostnames (`foo.localhost` and `bar.localhost`)
4. **Executes** 200 randomized HTTP requests with full metrics capture
5. **Collects** CPU, memory, and network stats from Prometheus
6. **Scans** code for security vulnerabilities with Trivy
7. **Posts** a beautiful summary comment to your PR
8. **Cleans up** all resources automatically

**Result:** A complete infrastructure lifecycle test, all validated and reported in one automated workflow.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Actions CI/CD                        │
│                     (Triggered on PR)                           │
└────────┬────────────────────────────────────────────────────────┘
         │
         ├─► 1. VALIDATE        Environment & dependencies ready?
         │
         ├─► 2. TEST            Unit & integration tests pass?
         │
         ├─► 3. SECURITY SCAN   Vulnerabilities detected?
         │
         ├─► 4. PROVISION       ┌─────────────────────────────────┐
         │                       │    KinD Cluster (localhost)     │
         │                       │  ┌────────────────────────────┐ │
         │                       │  │   Control Plane (1 node)   │ │
         │                       │  ├────────────────────────────┤ │
         │                       │  │  Worker 1 │ Worker 2       │ │
         │                       │  └────────────────────────────┘ │
         │                       └─────────────────────────────────┘
         │
         ├─► 5. DEPLOY          ┌─────────────────────────────────┐
         │                       │  • ingress-nginx controller     │
         │                       │  • echo-foo service             │
         │                       │  • echo-bar service             │
         │                       │  • Prometheus monitoring        │
         │                       └─────────────────────────────────┘
         │
         ├─► 6. HEALTH CHECK    All workloads healthy & ready?
         │
         ├─► 7. LOAD TEST       ┌─────────────────────────────────┐
         │                       │  200 randomized HTTP requests   │
         │                       │  • P50, P90, P95, P99 latency   │
         │                       │  • Success rate & throughput    │
         │                       │  • Per-host breakdown           │
         │                       └─────────────────────────────────┘
         │
         ├─► 8. MONITOR         ┌─────────────────────────────────┐
         │                       │  Prometheus metrics collection  │
         │                       │  • CPU utilization              │
         │                       │  • Memory consumption           │
         │                       │  • Network I/O                  │
         │                       └─────────────────────────────────┘
         │
         ├─► 9. REPORT          ✅ Beautiful PR comment posted
         │                       📊 Load & resource metrics
         │                       🔒 Security findings
         │
         └─► 10. CLEANUP        🧹 All resources destroyed
                                 ✓ Guaranteed (even on failure)

         ⏱️  Total time: ~2-3 minutes
```

---

## 📂 File Structure

```
k8s-loadtest-ci/
│
├── 📄 README.md                              ← You are here
├── 📄 requirements.txt                       ← Python dependencies
├── 📄 IMPLEMENTATION_SUMMARY.md              ← Complete feature list
│
├── 📁 .github/workflows/
│   └── ci.yml                                ← GitHub Actions workflow
│
├── 📁 docs/                                  ← Deep documentation
│   ├── DESIGN.md                             ← Architecture decisions
│   └── INTERVIEW_PREP.md                     ← Q&A talking points
│
├── 📁 manifests/                             ← Kubernetes definitions
│   ├── foo-deployment.yaml                   ← Echo service #1
│   ├── bar-deployment.yaml                   ← Echo service #2
│   ├── ingress.yaml                          ← Host-based routing
│   ├── prometheus.yaml                       ← Monitoring stack
│   │
│   ├── base/                                 ← Kustomize foundation
│   │   └── kustomization.yaml
│   │
│   └── overlays/production/                  ← Environment patches
│       └── kustomization.yaml
│
└── 📁 scripts/                               ← Orchestration scripts
    ├── utils.py                              ← Shared utilities
    ├── create_cluster.py                     ← KinD provisioning
    ├── deploy.py                             ← Workload deployment
    ├── check_health.py                       ← Readiness validation
    ├── load_test.py                          ← Traffic generation
    ├── monitor_resources.py                  ← Metrics collection
    ├── post_comment.py                       ← PR automation
    ├── delete_cluster.py                     ← Resource cleanup
    ├── validate.py                           ← Environment checks
    └── test.py                               ← Test suite
```

---

## ✨ Features at a Glance

| Feature | What It Does | Why It Matters |
|---------|-------------|-----------------|
| **Multi-node cluster** | 1 control-plane + 2 workers | Tests real distributed scenarios |
| **Host-based routing** | `foo.localhost` → foo, `bar.localhost` → bar | Validates ingress configuration |
| **Readiness checks** | Waits for all pods/ingress/webhooks | Prevents false negatives from timing issues |
| **Percentile metrics** | p50, p90, p95, p99 latency | Shows real distribution, not just averages |
| **Resource monitoring** | CPU, memory, network from Prometheus | Catches performance regressions early |
| **Security scanning** | Trivy filesystem + dependency checks | Blocks vulnerable code pre-deployment |
| **PR comments** | Markdown tables with results | Developers see results without leaving GitHub |
| **Artifact storage** | JSON metrics + kubeconfig | Debug failures or re-run analysis |
| **Cleanup guarantee** | `if: always()` ensures teardown | Prevents resource leaks in CI |
| **Idempotent ops** | Safe to re-run without manual reset | CI-friendly, robust |

---

## 🚀 Getting Started

### Prerequisites

Install these locally (CI downloads them automatically):

```bash
# Required
python3 --version           # 3.11+
docker --version            # 24+
git --version

# Nice to have (optional for local testing)
kind --version              # KinD for local cluster
kubectl version --client    # Kubernetes CLI
```

### Quick Setup

```bash
# 1. Clone the repository
git clone https://github.com/kprasad7/k8s-loadtest-ci.git
cd k8s-loadtest-ci

# 2. Install Python dependencies
python -m pip install -r requirements.txt

# 3. Verify environment is ready
python scripts/validate.py

# 4. Create a test branch and push
git checkout -b feat/test-ci
git push origin feat/test-ci

# 5. Open a PR to main
# → GitHub Actions will run automatically
# → Check the PR for the automated comment with results
```

---

## 🔄 How the CI Pipeline Works

### Stage 1: **Validate** (10s)
```bash
python scripts/validate.py
```
✅ Checks: Python version, Docker, kind, kubectl, script syntax, manifest validity, GitHub Actions YAML  
❌ Fails fast if environment is incomplete

### Stage 2: **Test** (5s)
```bash
python scripts/test.py
```
✅ Runs 5 automated tests:
- State management (save/load JSON)
- Command execution (subprocess handling)
- Manifest validation (YAML structure)
- Percentile calculation (statistics)
- PR context discovery (GitHub integration)

### Stage 3: **Security Scan** (20s)
```bash
trivy fs . --format sarif --output trivy-results.sarif
```
✅ Scans Python dependencies, manifests, configs  
✅ Uploads SARIF report to GitHub Security tab  
⚠️ Doesn't block PR (advisory only)

### Stage 4: **Provision** (45s)
```bash
python scripts/create_cluster.py
```
✅ Creates KinD cluster with 3 nodes  
✅ Extracts kubeconfig to `artifacts/kubeconfig`  
✅ Waits 180s for cluster to stabilize

**KinD config:**
```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
  - role: worker
```

### Stage 5: **Deploy** (25s)
```bash
python scripts/deploy.py
```
✅ Installs ingress-nginx from official Helm chart  
✅ Applies foo & bar deployments with resource limits  
✅ Configures ingress for host-based routing  
✅ Deploys Prometheus for metrics collection  
⏳ Waits for admission webhooks before applying ingress

### Stage 6: **Health Check** (10s)
```bash
python scripts/check_health.py
```
✅ Verifies:
- All nodes `Ready`
- Ingress controller pod running
- Echo deployments rolled out successfully
- Prometheus deployment ready
- Services have endpoints

**Logs example:**
```
[12:43:16] Waiting for nodes to become Ready
[12:43:16] Waiting for ingress-nginx controller pod
[12:43:20] Waiting for deployment echo/echo-foo
[12:43:21] Prometheus is ready
```

### Stage 7: **Load Test** (5s)
```bash
python scripts/load_test.py \
  --requests 200 \
  --concurrency 20 \
  --warm-up-retries 2
```

**What happens:**
1. Warm-up request to each host (with retry)
2. Send 100 requests to `foo.localhost` + 100 to `bar.localhost`
3. Collect latency for each request
4. Calculate percentiles (p50, p90, p95, p99)
5. Count successes & failures
6. Save results to JSON + Markdown

**Sample output:**
```
### 🚦 Load-test summary
| Host          | Requests | Success % | Avg (ms) | P90 (ms) | Req/s |
|---------------|---------:|----------:|---------:|---------:|------:|
| foo.localhost |      108 |     100 % |     1.41 |     1.54 | 378.7 |
| bar.localhost |       92 |     100 % |     1.43 |     1.56 | 322.6 |
```

### Stage 8: **Monitor** (35s)
```bash
python scripts/monitor_resources.py \
  --duration 30 \
  --interval 5
```

**What it captures:**
- CPU cores (from Prometheus `container_cpu_usage_seconds_total`)
- Memory MB (from Prometheus `container_memory_working_set_bytes`)
- Network RX/TX (from Prometheus `container_network_*_bytes_total`)
- Pod replica count

**Handles connectivity:** Auto-detects if Prometheus isn't on localhost:9090 and starts a `kubectl port-forward` tunnel

### Stage 9: **Post Comment** (3s)
```bash
python scripts/post_comment.py
```

✅ Reads load-test results from JSON  
✅ Reads resource metrics from JSON  
✅ Formats as Markdown tables  
✅ Posts to GitHub PR comment  
✅ Includes artifact links

**Example comment:**
```markdown
## ✅ Load Test Results

### 🚦 Metrics
| Host | Requests | Avg | P90 | Failures |
|------|----------|-----|-----|----------|
| foo.localhost | 108 | 1.41ms | 1.54ms | 0 |

### 📊 Resource Utilization
| Metric | Avg | Min | Max |
|--------|-----|-----|-----|
| Memory | 25.1MB | 12.1MB | 32.1MB |
```

### Stage 10: **Cleanup** (8s)
```bash
python scripts/delete_cluster.py
```

✅ Deletes KinD cluster  
✅ Removes kubeconfig file  
✅ **Runs even if previous steps failed** (`if: always()`)  
✅ Uploads artifacts before deleting

---

## 📊 Understanding the Reports

### Load Test Metrics Table

| Column | Meaning | Interpretation |
|--------|---------|-----------------|
| **Requests** | Total HTTP calls sent to this host | Higher = more confident result |
| **Success %** | Percentage of 2xx responses | Should be 100% for healthy service |
| **Avg (ms)** | Mean latency across all requests | Lower is better; watch for increases |
| **P90 (ms)** | 90th percentile latency | "Most users see this latency or better" |
| **P95 (ms)** | 95th percentile latency | Upper bound for typical users |
| **P99 (ms)** | 99th percentile latency | Tail latency; indicates outliers |
| **Req/s** | Throughput: requests per second | How many requests/s the service handled |
| **Failures** | Count of non-2xx or timeout responses | Should be 0 |

**Example interpretation:**
```
foo.localhost: avg 1.41ms, p95 1.63ms → Latency is stable & predictable
bar.localhost: 322 req/s → Service can handle ~300 concurrent users
0 failures → No timeouts or errors
```

### Resource Utilization Table

| Metric | Meaning | Healthy Range |
|--------|---------|----------------|
| **CPU (cores)** | Average CPU used during load test | 0.0–0.5 cores per pod (depending on workload) |
| **Memory (MB)** | Average memory consumed | 20–50 MB typical for echo service |
| **Network RX (MB/s)** | Incoming bandwidth | Usually low for HTTP echo |
| **Network TX (MB/s)** | Outgoing bandwidth | Usually low for HTTP echo |
| **Running pods** | Number of replicas active | Should match deployment replicas |

**What to watch for:**
- Memory creeping up → potential memory leak
- CPU spiking → performance issue or inefficient code
- No pods running → deployment failed silently
- Network RX/TX near zero → might indicate packet loss

---

## 💻 Running Locally

### Run Everything (Full Pipeline)

```bash
# Create cluster
python scripts/create_cluster.py

# Deploy workloads
python scripts/deploy.py

# Wait for health
python scripts/check_health.py

# Run load test
python scripts/load_test.py --requests 200 --concurrency 20

# Collect metrics
python scripts/monitor_resources.py --duration 60 --interval 5

# View results
cat artifacts/load-test-results.md
cat artifacts/resource-metrics.md

# Cleanup
python scripts/delete_cluster.py
```

### Run Just Tests

```bash
python scripts/test.py
```

Output:
```
🧪 Running test suite
========================================
[12:42:03] Running state management tests...
[12:42:03]   ✓ State management tests passed
[12:42:03] Running command execution tests...
[12:42:03]   ✓ Command execution tests passed
...
✅ All 5 tests passed!
```

### Run Just Health Checks

```bash
python scripts/check_health.py
```

### Increase Load for Stress Testing

```bash
python scripts/load_test.py \
  --requests 500 \
  --concurrency 50 \
  --timeout 10
```

### Access Prometheus UI (Local)

After deployment:
```bash
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# Then open: http://localhost:9090
```

---

## 🔧 Troubleshooting

### ❌ "connection refused" on ingress apply

**Symptom:**
```
Error from server (InternalError): failed calling webhook
"validate.nginx.ingress.kubernetes.io": failed to call webhook
Post "https://ingress-nginx-controller-admission..."
```

**Root cause:** Admission webhook not yet ready

**Solution:** Already handled! `deploy.py` waits for webhook jobs to complete. If it fails locally, ensure you ran `check_health.py` first.

---

### ❌ Prometheus metrics all show zero

**Symptom:**
```
CPU (cores) | 0.000 | 0.0 | 0.0
Memory (MB) | 0.0 | 0.0 | 0.0
```

**Root cause:** Prometheus scrape not collecting cadvisor metrics, or sampling window too short

**Solution:** 
```bash
# Increase monitoring duration
python scripts/monitor_resources.py --duration 60 --interval 5

# Verify Prometheus has data
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# Visit http://localhost:9090/graph
# Query: container_memory_working_set_bytes
```

---

### ❌ PR comment fails to post

**Symptom:**
```
Error: graphql error: Resource not accessible by integration
```

**Root cause:** GitHub token missing `pull-requests: write` permission

**Solution:** Workflow already sets correct permissions. If running in a fork, you may need to approve the workflow in Settings → Actions.

---

### ❌ Trivy scan fails

**Symptom:**
```
Error: Path does not exist: trivy-results.sarif
```

**Root cause:** Trivy didn't generate SARIF (or network issue downloading DB)

**Solution:** Already handled! Workflow only uploads SARIF if it exists. Trivy output is logged in the Actions tab.

---

### ❌ KinD cluster times out

**Symptom:**
```
Timed out waiting for nodes to be ready
```

**Root cause:** Runner CPU/memory constrained, or Docker daemon issue

**Solution:**
```bash
# Check Docker status
docker ps

# Manually delete stale cluster
kind delete cluster --name ci-loadtest

# Re-run
python scripts/create_cluster.py
```

---

## 🏢 Production Considerations

### Resource Management
- ✅ All pods have CPU/memory requests & limits
- ✅ Prevents "noisy neighbor" interference
- ✅ KinD uses minimal resources (~2 GB)

### Security
- ✅ Trivy scans for vulnerabilities
- ✅ Prometheus RBAC restricted to monitoring namespace
- ✅ No hardcoded secrets; uses GitHub Actions token
- ⏳ Future: GitHub OpenID Connect + HashiCorp Vault

### Observability
- ✅ Structured logging in all scripts
- ✅ Timestamps on every action
- ✅ Error messages include context
- ✅ Artifacts uploaded for post-mortem analysis

### Reliability
- ✅ Retries on transient failures (HTTP 5xx, timeouts)
- ✅ Health checks before proceeding to next stage
- ✅ Cleanup guaranteed with `if: always()`
- ✅ Idempotent operations (safe to re-run)

### Scalability
- Kustomize overlays support multiple environments
- Modular scripts allow component swaps (e.g., k6, Grafana)
- Prometheus foundation enables HPA, alerting, dashboards
- Easily extend with additional load profiles or metrics

