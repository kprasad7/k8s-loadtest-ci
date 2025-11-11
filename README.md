# k8s-loadtest-ci

Automation exercise that provisions a multi-node KinD cluster on each pull request, deploys echo services behind an NGINX ingress, executes an HTTP load test, and reports the outcome back to the GitHub PR thread.

## Repository layout

- `manifests/`
	- `foo-deployment.yaml` / `bar-deployment.yaml` – deployments + services for the echo workloads.
	- `ingress.yaml` – host-routed ingress targeting the echo services.
- `scripts/`
	- `create_cluster.py` – provisions a three-node KinD cluster and captures kubeconfig.
	- `deploy.py` – installs ingress-nginx and applies the manifests.
	- `check_health.py` – waits for node readiness, ingress controller health, and deployment rollout.
	- `load_test.py` – warms the endpoints, generates randomized traffic, and records metrics.
	- `post_comment.py` – publishes the Markdown load-test summary to the originating PR.
	- `delete_cluster.py` – tears down the KinD cluster and removes local kubeconfig.
	- `utils.py` – shared logging/state/subprocess helpers across scripts.
- `docs/DESIGN.md` – design rationale and execution flow.
- `.github/workflows/ci.yml` – GitHub Actions workflow invoking each script sequentially on every PR.
- `requirements.txt` – Python dependencies (`requests`, `PyGithub`).
- `artifacts/` – runtime output (kubeconfig, load-test reports); ignored by git.

## Local execution

1. Install prerequisites: Docker, `kind`, `kubectl`, Python 3.11+.
2. Install Python requirements: `pip install -r requirements.txt`.
3. Run the pipeline scripts in order:

	 ```bash
	 python scripts/create_cluster.py
	 python scripts/deploy.py
	 python scripts/check_health.py
	 python scripts/load_test.py --requests 200
	 # Optionally post a comment when running against a PR clone with GITHUB_TOKEN configured
	 python scripts/post_comment.py
	 python scripts/delete_cluster.py
	 ```

	 Tip: export `KUBECONFIG=$(pwd)/artifacts/kubeconfig` if you want to inspect the cluster manually between steps.

4. Review generated artifacts under `artifacts/` (JSON + Markdown load-test summaries, kubeconfig, pipeline state).

## CI workflow

- Triggered on every `pull_request` targeting `main`.
- Installs Python deps and pins `kind` v0.22.0 and `kubectl` v1.29.2 on the GitHub runner.
- Executes the modular scripts: create cluster → deploy → health check → load test → PR comment → teardown.
- Uploads the `artifacts/` directory for post-run inspection even on failure.

## Load testing & reporting

- Traffic generator uses Python `requests` to send randomized load across `foo.localhost` and `bar.localhost` via ingress-nginx.
- Warm-up attempts precede measurement to avoid skewing the latency distribution.
- Metrics cover latency percentiles (avg, p50/p90/p95/p99, max), requests-per-second, success ratio, and failure counts per host plus combined totals.
- Markdown summary and raw JSON payload land in `artifacts/` and, in CI, on the PR discussion thread.

## Cleanup & failure handling

- Teardown script runs in an `always()` block to delete the KinD cluster even after failures.
- Shared utilities standardise logging and surface detailed stdout/stderr for failing commands to aid triage.

## Future enhancements

- Layer on Prometheus/Grafana to attach utilisation snapshots alongside the load-test results.
- Replace ad-hoc manifests with Kustomize/Helm for better reuse across environments.
- Swap the bespoke load generator for a dedicated tool such as k6 or Vegeta for higher-throughput scenarios.
