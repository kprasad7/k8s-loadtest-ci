# System Design Overview

This project automates the validation of a lightweight ingress + echo stack on KinD for every pull request targeting `main`. The workflow provisions a multi-node cluster, deploys workloads, validates readiness, runs a load test, and posts results back to the contributing pull request.

## High-level flow

1. **Validation** – `scripts/validate.py` verifies Python version, dependencies, binaries, and project structure before proceeding.
2. **Testing** – `scripts/test.py` runs unit and integration tests covering state management, command execution, manifest validity, percentile calculations, and PR context discovery.
3. **Cluster provisioning** – `scripts/create_cluster.py` builds a three-node KinD cluster (control-plane + two workers) and captures the kubeconfig in `artifacts/` for downstream steps. The script also writes shared state to `artifacts/state.json` and exports `KUBECONFIG` when running inside GitHub Actions.
4. **Deployment** – `scripts/deploy.py` ensures the `echo` namespace exists, installs ingress-nginx, and applies the declarative manifests for the `foo` and `bar` deployments and ingress routing.
5. **Health checks** – `scripts/check_health.py` waits for node readiness, confirms the ingress controller is healthy, and verifies both deployments have rolled out successfully.
6. **Load test** – `scripts/load_test.py` sends randomized traffic to `foo.localhost` and `bar.localhost`, records latency percentiles, success ratios, and requests-per-second statistics, and emits both JSON and Markdown summaries.
7. **PR comment** – `scripts/post_comment.py` posts the Markdown summary on the originating pull request when executed in CI. The script is idempotent and skips gracefully when the run is not associated with a PR.
8. **Security scanning** – Trivy scans the codebase for vulnerabilities and uploads results to GitHub Security tab for continuous monitoring.
9. **Teardown** – `scripts/delete_cluster.py` removes the KinD cluster and cleans up the generated kubeconfig so that ephemeral CI workers remain clean.

## Shared utilities

- `scripts/utils.py` centralises logging, subprocess execution, state management, and environment handling. All scripts depend on it for consistent behaviour and structured error handling.
- Temporary data (kubeconfig, metrics, failure logs) is stored under `artifacts/` and uploaded as GitHub Actions artifacts for post-run inspection.

## Failure handling

- Every critical subprocess call is wrapped to produce verbose logs and actionable error messages.
- Health-check loops apply bounded retries with informative logging to simplify debugging transient Kubernetes issues.
- Each script prefers declarative operations (`kubectl apply`, `kind create --config`) over imperative mutation to remain idempotent.

## Extensibility considerations

- Additional workloads can be introduced by adding manifests and extending `deploy.py`/`check_health.py` without altering the rest of the pipeline.
- Replacing the Python load generator with `k6`, `vegeta`, or another tool only requires modifying `scripts/load_test.py` and the dependency list.
- Observability additions (e.g., Prometheus/Grafana) can hook into the same lifecycle stages and publish supplementary artifacts for richer PR reporting.
