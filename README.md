# k8s-loadtest-ci

Automation exercise that provisions a multi-node KinD cluster on each pull request, deploys echo services behind an NGINX ingress, executes an HTTP load test, and reports the outcome back to the GitHub PR thread.

## Repository layout

- `manifests/`
  - `base/` – Kustomize base layer with deployment manifests
  - `overlays/production/` – Production-specific resource adjustments
  - `foo-deployment.yaml` / `bar-deployment.yaml` – deployments + services for the echo workloads with resource limits
  - `ingress.yaml` – host-routed ingress targeting the echo services
  - `prometheus.yaml` – Prometheus deployment for monitoring (stretch goal)
- `scripts/`
  - `create_cluster.py` – provisions a three-node KinD cluster and captures kubeconfig
  - `deploy.py` – installs ingress-nginx, Prometheus, and applies the manifests
  - `check_health.py` – waits for node readiness, ingress controller, deployments, and Prometheus health
  - `load_test.py` – warms the endpoints, generates randomized traffic, and records metrics
  - `monitor_resources.py` – captures CPU/memory/network utilization from Prometheus
  - `post_comment.py` – publishes load-test and resource metrics to the PR
  - `delete_cluster.py` – tears down the KinD cluster and removes local kubeconfig
  - `validate.py` – validates environment dependencies and project structure
  - `test.py` – runs unit and integration tests for pipeline components
  - `utils.py` – shared logging/state/subprocess helpers across scripts
- `docs/DESIGN.md` – design rationale and execution flow
- `docs/INTERVIEW_PREP.md` – technical decision rationale and interview Q&A
- `.github/workflows/ci.yml` – GitHub Actions workflow with validation, security scan, and monitoring stages
- `requirements.txt` – Python dependencies (`requests`, `PyGithub`)
- `artifacts/` – runtime output (kubeconfig, load-test reports, metrics); ignored by git

## Local execution

1. Install prerequisites: Docker, `kind`, `kubectl`, Python 3.11+.
2. Install Python requirements: `pip install -r requirements.txt`.
3. Run the pipeline scripts in order:

   ```bash
   python scripts/validate.py  # Pre-flight checks
   python scripts/test.py      # Run test suite
   python scripts/create_cluster.py
   python scripts/deploy.py
   python scripts/check_health.py
   python scripts/load_test.py --requests 200
   # Optionally post a comment when running against a PR clone with GITHUB_TOKEN configured
   python scripts/post_comment.py
   python scripts/delete_cluster.py
   ```	 Tip: export `KUBECONFIG=$(pwd)/artifacts/kubeconfig` if you want to inspect the cluster manually between steps.

4. Review generated artifacts under `artifacts/` (JSON + Markdown load-test summaries, kubeconfig, pipeline state).

## CI workflow

- Triggered on every `pull_request` targeting `main`.
- Installs Python deps and pins `kind` v0.22.0 and `kubectl` v1.29.2 on the GitHub runner.
- **Validation**: Verifies environment dependencies and project structure.
- **Testing**: Runs unit and integration tests for pipeline components.
- **Infrastructure**: Creates cluster → deploys workloads → validates health.
- **Load testing**: Executes randomized traffic and captures metrics.
- **Reporting**: Posts results to PR as automated comment.
- **Security**: Scans codebase with Trivy and uploads results to GitHub Security tab.
- **Cleanup**: Tears down cluster and uploads artifacts (logs, metrics, security reports).

## Load testing & reporting

- Traffic generator uses Python `requests` to send randomized load across `foo.localhost` and `bar.localhost` via ingress-nginx.
- Warm-up attempts precede measurement to avoid skewing the latency distribution.
- Metrics cover latency percentiles (avg, p50/p90/p95/p99, max), requests-per-second, success ratio, and failure counts per host plus combined totals.
- **Resource monitoring** (stretch goal): Prometheus captures CPU, memory, and network utilization during the load test.
- Combined markdown summary (load test + resource metrics) and raw JSON payloads land in `artifacts/` and, in CI, on the PR discussion thread.

## Cleanup & failure handling

- Teardown script runs in an `always()` block to delete the KinD cluster even after failures.
- Shared utilities standardise logging and surface detailed stdout/stderr for failing commands to aid triage.

## Future enhancements

- ~~Layer on Prometheus/Grafana to attach utilisation snapshots alongside the load-test results~~ ✅ **Implemented**
- ~~Replace ad-hoc manifests with Kustomize/Helm for better reuse across environments~~ ✅ **Kustomize base/overlays added**
- ~~Add security scanning with Trivy~~ ✅ **Implemented**
- Swap the bespoke load generator for a dedicated tool such as k6 or Vegeta for higher-throughput scenarios
- Add Grafana dashboards for real-time visualization during load tests
- Implement HorizontalPodAutoscaler (HPA) to test auto-scaling behavior
- ~~Replace ad-hoc manifests with Kustomize/Helm for better reuse across environments~~ ✅ **Kustomize base/overlays added**
- Swap the bespoke load generator for a dedicated tool such as k6 or Vegeta for higher-throughput scenarios
- Add Grafana dashboards for real-time visualization during load tests
- Implement HorizontalPodAutoscaler (HPA) to test auto-scaling behavior
