# Interview Preparation Guide

## Technical Decisions & Rationale

### Why Python over Bash/Go?
- **Readability**: Assignment emphasizes maintainable code; Python's syntax is self-documenting
- **Libraries**: Native `requests` for HTTP, `PyGithub` for PR API, no need for `curl` + `jq` gymnastics
- **Error handling**: Structured exceptions vs. fragile exit code checks
- **Testing**: Easy to unit test with pytest or built-in unittest

### Why modular scripts vs. monolithic runner?
- **Separation of concerns**: Each script has single responsibility
- **Debuggability**: Can re-run individual steps (e.g., `load_test.py`) without full teardown
- **Reusability**: `deploy.py` can be used outside CI (local dev, staging)
- **Declarative workflows**: GitHub Actions steps clearly map to pipeline stages

### Why Kustomize for configuration management?
- **Declarative over imperative**: Base + overlays pattern avoids script-driven mutations
- **DRY principle**: Shared base manifests with environment-specific patches
- **Native kubectl support**: No external tooling required (vs. Helm)
- **Production-ready**: Easy to add staging/dev overlays with different replica counts and resource limits

### Load testing approach
- **Warm-up phase**: Prevents skewed latencies from cold starts / DNS resolution
- **Percentile metrics**: p90/p95/p99 reveal tail latencies (better than avg)
- **Randomized traffic**: Simulates real-world patterns vs. sequential hits
- **Failure tracking**: Distinguishes HTTP errors from network timeouts
- **Custom implementation**: Demonstrates understanding of metrics vs. black-box tool usage

### Prometheus integration (stretch goal)
- **Real-time visibility**: Captures actual resource usage during load test
- **Industry standard**: PromQL for querying, ServiceMonitor for auto-discovery
- **Kubernetes-native**: Uses service discovery to scrape pods automatically
- **Extensibility**: Foundation for Grafana dashboards, alerting rules

### Security with Trivy
- **Shift-left security**: Catches vulnerabilities before deployment
- **Comprehensive scanning**: Covers OS packages, application dependencies, IaC misconfigurations
- **CI integration**: Automatic SARIF upload to GitHub Security tab
- **No-blocker approach**: Reports findings without failing the build (configurable)

## Observability & Reliability

### Health checks implemented
1. **Node readiness**: `kubectl wait --for=condition=Ready nodes`
2. **Ingress controller**: Wait for `ingress-nginx` pod Ready state
3. **Deployments**: `kubectl rollout status` ensures replica availability
4. **Prometheus**: Deployment rollout + health endpoint check
5. **Endpoint warm-up**: Pre-test HTTP requests validate routing before metrics

### Failure scenarios handled
- **Cluster creation timeout**: KinD `--wait` flag with 180s limit
- **Deployment rollout failure**: `kubectl rollout status --timeout=180s`
- **Load test timeouts**: Per-request 10s timeout, logged but doesn't abort test
- **Missing PR context**: Graceful skip when not running in PR environment
- **Prometheus unavailable**: Resource monitoring is optional, fails gracefully
- **Cleanup guarantees**: `if: always()` in GitHub Actions

### Resource limits and requests
- **Predictable scheduling**: Requests ensure pods get minimum resources
- **Burst protection**: Limits prevent resource exhaustion
- **Production overlay**: Higher limits for production workloads via Kustomize
- **Monitoring validation**: Actual usage vs. configured limits tracked by Prometheus

## Potential Interview Questions

### "How would you scale this to 1000 req/s?"
- Replace Python `requests` with `locust` or `k6` (async/concurrent)
- Use `wrk` or `vegeta` for high-throughput benchmarking
- Add resource limits to deployments to test horizontal pod autoscaler (HPA)
- Deploy multiple load generators in parallel

### "How would you add continuous monitoring post-deployment?"
- Already implemented with Prometheus
- Add Grafana dashboards for visualization
- Configure AlertManager for threshold-based alerts
- Export metrics to external systems (Datadog, New Relic)
- Add ServiceMonitor CRDs for automatic discovery

### "What about security best practices?"
- ✅ Trivy scanning for vulnerability detection
- Use GitHub OIDC for cloud provider auth (avoid static secrets)
- Network policies to restrict pod-to-pod traffic
- Pod security standards (restricted baseline)
- RBAC for least-privilege access
- Secrets management with External Secrets Operator

### "How would you test this locally?"
```bash
# Full pipeline
python scripts/validate.py
python scripts/test.py
python scripts/create_cluster.py
python scripts/deploy.py
python scripts/check_health.py
python scripts/load_test.py --requests 50
python scripts/monitor_resources.py --duration 30
python scripts/delete_cluster.py

# Inspect cluster
export KUBECONFIG=$(pwd)/artifacts/kubeconfig
kubectl get pods -n echo
kubectl get pods -n monitoring
kubectl get ingress -n echo
curl -H "Host: foo.localhost" http://localhost

# Query Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090
curl "http://localhost:9090/api/v1/query?query=up"
```

### "What's missing for production?"
- **Secrets management**: Vault/AWS Secrets Manager for API keys
- **Multi-region**: Deploy to staging/prod with Kustomize overlays (partial impl.)
- **Canary deployments**: Flagger + Istio for gradual rollout
- **Alerting**: PagerDuty integration for failed load tests
- **Compliance**: Audit logging, network policies, OPA/Gatekeeper
- **High availability**: Multi-replica Prometheus with persistent storage

### "How does Kustomize improve maintainability?"
- **Base/overlay pattern**: Shared manifests with environment-specific patches
- **No templating**: Pure YAML transformations (vs. Helm's Go templates)
- **Strategic merge**: Patch only changed fields, inherit the rest
- **Example**: Production overlay increases replicas and CPU limits without duplicating entire manifests

## Code Quality Highlights

### Follows Python best practices
- Type hints (`from __future__ import annotations`)
- Docstrings on all modules/functions
- Structured logging with timestamps
- Dataclasses for command results
- Context managers for file I/O
- Executable scripts with `if __name__ == "__main__"`

### Error handling patterns
- Custom `CommandError` exception for subprocess failures
- Detailed error messages with stdout/stderr
- Graceful degradation (PR comment skips when not applicable, resource monitoring optional)
- Idempotent operations (cluster creation deletes existing first)

### Testing approach
- Unit tests for utilities (state management, command execution)
- Integration tests for manifest validation
- Percentile calculation verification
- PR context discovery edge cases
- All tests run in CI before deployment

### Documentation layers
1. **README.md**: Quick start, local execution, CI overview
2. **DESIGN.md**: Architecture decisions, system flow, extensibility
3. **INTERVIEW_PREP.md**: Technical rationale, interview Q&A
4. **Inline comments**: Non-obvious logic (percentile calculation, PromQL queries)
5. **Help text**: All scripts have `--help` flags

## Metrics Reported

### Load Test Metrics
| Metric | Purpose |
|--------|---------|
| Avg latency | Baseline performance |
| P50 (median) | Typical user experience |
| P90 | 90th percentile (outlier threshold) |
| P95 | High-priority SLA target |
| P99 | Worst-case user experience |
| Max latency | Detect catastrophic failures |
| Success rate | Application-level correctness |
| Req/s | Throughput capacity |
| Failures | Network/timeout errors |

### Resource Metrics (Prometheus)
| Metric | Purpose |
|--------|---------|
| CPU cores | Compute utilization |
| Memory MB | RAM consumption |
| Network RX/TX | Bandwidth usage |
| Running pods | Availability verification |

## CI/CD Best Practices Demonstrated

- ✅ **Validation stage**: Catches syntax/structural errors early
- ✅ **Testing stage**: Automated unit/integration tests
- ✅ **Security scanning**: Trivy for vulnerability detection
- ✅ **Pinned tool versions** (`kind v0.22.0`, `kubectl v1.29.2`)
- ✅ **Artifact upload** for debugging (kubeconfig, metrics, security reports)
- ✅ **Cleanup on failure** (`if: always()`)
- ✅ **Minimal permissions** (`pull-requests: write`)
- ✅ **Fast feedback** (< 10 min total runtime)
- ✅ **Declarative workflow** (no inline bash scripts)
- ✅ **Resource limits** on workloads for predictable behavior
- ✅ **Monitoring integration** (Prometheus during load test)

## Stretch Goals Implemented

1. ✅ **Prometheus monitoring**: Captures CPU/memory/network during load test
2. ✅ **Kustomize overlays**: Base + production configuration management
3. ✅ **Security scanning**: Trivy integration with SARIF upload
4. ✅ **Automated testing**: Unit and integration test suite
5. ✅ **Resource limits**: Requests/limits on all workloads
6. ✅ **Comprehensive docs**: DESIGN.md + INTERVIEW_PREP.md

## Future Enhancements (Discussion Points)

1. **Grafana dashboards**: Real-time visualization during load tests
2. **HorizontalPodAutoscaler**: Test auto-scaling behavior under load
3. **Chaos engineering**: Inject pod failures during load test (Chaos Mesh)
4. **Multi-cluster**: Test ingress routing across regions
5. **Service mesh**: Istio for advanced traffic management and observability
6. **GitOps**: FluxCD/ArgoCD for declarative cluster state
7. **Cost optimization**: Vertical Pod Autoscaler, spot instances
8. **Compliance**: OPA/Gatekeeper policies, admission webhooks

## Key Differentiators

| Aspect | Basic Implementation | This Implementation |
|--------|---------------------|---------------------|
| Config management | Hard-coded manifests | Kustomize base/overlays |
| Monitoring | None | Prometheus with resource metrics |
| Security | None | Trivy scanning + SARIF upload |
| Testing | Manual verification | Automated test suite |
| Documentation | README only | README + DESIGN + INTERVIEW_PREP |
| Error handling | Fail-fast | Graceful degradation + cleanup |
| Resource management | No limits | Requests/limits on all pods |
| Observability | Load test only | Load test + resource utilization |

**This implementation demonstrates senior-level thinking: production-ready practices, extensibility, and comprehensive observability.**
