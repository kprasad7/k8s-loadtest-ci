# Interview Preparation Guide

## Technical Decisions & Rationale

### Why Python over Bash/Go?
- **Readability**: Assignment emphasizes maintainable code; Python's syntax is self-documenting
- **Libraries**: Native `requests` for HTTP, `PyGithub` for PR API, no need for `curl` + `jq` gymnastics
- **Error handling**: Structured exceptions vs. fragile exit code checks
- **Testing**: Easy to unit test with pytest (future enhancement)

### Why modular scripts vs. monolithic runner?
- **Separation of concerns**: Each script has single responsibility
- **Debuggability**: Can re-run individual steps (e.g., `load_test.py`) without full teardown
- **Reusability**: `deploy.py` can be used outside CI (local dev, staging)
- **Declarative workflows**: GitHub Actions steps clearly map to pipeline stages

### Why state.json vs. environment variables?
- **Persistence**: Scripts can run independently (non-CI scenarios)
- **Type safety**: JSON schema vs. string parsing
- **Auditability**: State file becomes artifact for debugging

### Load testing approach
- **Warm-up phase**: Prevents skewed latencies from cold starts / DNS resolution
- **Percentile metrics**: p90/p95/p99 reveal tail latencies (better than avg)
- **Randomized traffic**: Simulates real-world patterns vs. sequential hits
- **Failure tracking**: Distinguishes HTTP errors from network timeouts

### Ingress controller choice (nginx)
- **Industry standard**: Most common in production Kubernetes
- **KinD integration**: Official manifests for localhost testing
- **Feature completeness**: Supports host-based routing, rate limiting, TLS

## Observability & Reliability

### Health checks implemented
1. **Node readiness**: `kubectl wait --for=condition=Ready nodes`
2. **Ingress controller**: Wait for `ingress-nginx` pod Ready state
3. **Deployments**: `kubectl rollout status` ensures replica availability
4. **Endpoint warm-up**: Pre-test HTTP requests validate routing before metrics

### Failure scenarios handled
- **Cluster creation timeout**: KinD `--wait` flag with 180s limit
- **Deployment rollout failure**: `kubectl rollout status --timeout=180s`
- **Load test timeouts**: Per-request 10s timeout, logged but doesn't abort test
- **Missing PR context**: Graceful skip when not running in PR environment
- **Cleanup guarantees**: `if: always()` in GitHub Actions

## Potential Interview Questions

### "How would you scale this to 1000 req/s?"
- Replace Python `requests` with `locust` or `k6` (async/concurrent)
- Use `wrk` or `vegeta` for high-throughput benchmarking
- Add resource limits to deployments to test horizontal pod autoscaler (HPA)

### "How would you add monitoring?"
- Deploy Prometheus via Helm chart in `deploy.py`
- Add ServiceMonitor CRDs for echo pods
- Augment load test with `kubectl top pods` snapshot
- Post resource utilization graphs to PR comment

### "What about security?"
- Use GitHub OIDC for cloud provider auth (avoid static secrets)
- Network policies to restrict pod-to-pod traffic
- Pod security standards (restricted baseline)
- Scan container images with Trivy in CI

### "How would you test this locally?"
```bash
# Full pipeline
./scripts/validate.sh
python scripts/create_cluster.py
python scripts/deploy.py
python scripts/check_health.py
python scripts/load_test.py --requests 50
python scripts/delete_cluster.py

# Inspect cluster
export KUBECONFIG=$(pwd)/artifacts/kubeconfig
kubectl get pods -n echo
kubectl get ingress -n echo
curl -H "Host: foo.localhost" http://localhost
```

### "What's missing for production?"
- **Secrets management**: Vault/AWS Secrets Manager for API keys
- **Multi-region**: Deploy to staging/prod with Kustomize overlays
- **Canary deployments**: Flagger + Istio for gradual rollout
- **Alerting**: PagerDuty integration for failed load tests
- **Compliance**: RBAC policies, audit logging, network policies

## Code Quality Highlights

### Follows Python best practices
- Type hints (`from __future__ import annotations`)
- Docstrings on all modules/functions
- Structured logging with timestamps
- Dataclasses for command results
- Context managers for file I/O

### Error handling patterns
- Custom `CommandError` exception for subprocess failures
- Detailed error messages with stdout/stderr
- Graceful degradation (PR comment skips when not applicable)
- Idempotent operations (cluster creation deletes existing first)

### Documentation layers
1. **README.md**: Quick start, local execution
2. **DESIGN.md**: Architecture decisions, system flow
3. **Inline comments**: Non-obvious logic (percentile calculation)
4. **Help text**: All scripts have `--help` flags

## Metrics Reported

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

## CI/CD Best Practices

- ✅ Pinned tool versions (`kind v0.22.0`, `kubectl v1.29.2`)
- ✅ Artifact upload for debugging (kubeconfig, metrics)
- ✅ Cleanup on failure (`if: always()`)
- ✅ Minimal permissions (`pull-requests: write`)
- ✅ Fast feedback (< 10 min total runtime)
- ✅ Declarative workflow (no inline bash scripts)

## Future Enhancements (Discussed in Interview)

1. **Prometheus integration**: Capture CPU/memory during load test
2. **Kustomize overlays**: Reuse manifests for staging/prod
3. **Helm charts**: Package echo app for versioned releases
4. **Synthetic monitoring**: Continuous load testing post-merge
5. **Chaos engineering**: Inject pod failures during load test
6. **Multi-cluster**: Test ingress routing across regions
