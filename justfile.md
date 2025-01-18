# OXN Platform Just Commands Guide

## Prerequisites
- just (command runner)
- Google Cloud SDK
- Terraform >= 1.0
- kubectl
- kOps >= 1.25
- Helm >= 3.0
- GCP Project with billing enabled

## Quick Start

1. Generate environment variables:
```bash
just generate-env
```

2. Verify environment:
```bash
just env-check
```

3. Setup GCP and create cluster:
```bash
just setup
just init
just up
# For spot instances:
just up spot
```

4. Install OXN Platform:
```bash
just install
# For development version:
just install dev=true
```

5. Tear down:
```bash
just down
```

## Development Commands

Build development image:
```bash
just build-dev
```

## Cluster Management

Check cluster status:
```bash
just validate
just get-cluster
just get-kubeconfig
```

## Port Forwarding Quick Reference

Grafana:
```bash
kubectl port-forward -n oxn-external-monitoring svc/kube-prometheus-grafana 3000:80
# http://localhost:3000 (admin/admin)
```

OpenTelemetry Demo:
```bash
kubectl port-forward -n system-under-evaluation svc/astronomy-shop-frontendproxy 8080:8080
# http://localhost:8080
# Jaeger UI: http://localhost:8080/jaeger/ui/
```

## Environment Variables
Generated in .env file:
- TF_VAR_project_id: GCP project ID
- CLUSTER_NAME: Kubernetes cluster name
- TF_VAR_zone: GCP zone
- NODE_COUNT: Number of nodes
- CONTROL_PLANE_SIZE: Control plane machine type
- NODE_SIZE: Worker node machine type
- TF_VAR_bucket_name: kOps state store bucket
- TF_VAR_bucket_location: Bucket location 