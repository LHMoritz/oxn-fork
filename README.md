# OXN - Observability Experiment Engine

OXN is a powerful tool for experimenting with and benchmarking observability software and fault detection mechanisms in Kubernetes environments. It allows users to perform controlled experiments on systems like Prometheus and other fault detection mechanisms, while also enabling fault injection into microservice systems.

## Features

- **Fault Injection**: Inject network delays, packet losses, and other faults into specific Kubernetes pods
- **Experiment Configuration**: Design experiments via JSON/YAML configuration files
- **Batch Experimentation**: Run multiple experiment configurations sequentially and automatically
- **Fault Detection Benchmarking**: Evaluate the effectiveness of different fault detection mechanisms
- **UI**: Client-server architecture with a web UI
- **Kubernetes Integration**: Native support for Kubernetes environments
- **Extensible Design**: Easy to add new fault detection mechanisms and treatments

## Prerequisites

- Kubernetes cluster 
- Helm 
- kubectl
- just
- Docker (for development)
- Python 3.8+ (for development)
- Node.js 16+ (for frontend development)

## Quick Start

### Using an Existing Kubernetes Cluster

1. Clone the repository:
```bash
git clone https://github.com/LHMoritz/oxn-fork.git
cd oxn
```

2. Install OXN using Helm:
```bash
helm install oxn k8s/oxn-platform
```

### Setting up a New Cluster on Google Cloud

1. Clone the repository and set up your environment:
```bash
git clone https://github.com/LHMoritz/oxn-fork.git
cd oxn
```

2. Use the provided justfile commands to set up your cluster:
```bash
just setup  # Enable required GCP APIs
just generate-env # Generates the .env file
just init   # Initialize terraform
just up     # Create and configure the cluster
just install # Install SUE and OXN
just down # Destroy the cluster 
```

## Project Structure

- [`frontend/`](frontend/): Next.js-based web UI
- [`backend/`](backend/): FastAPI-based backend service
- [`analysis/`](analysis/): FastAPI-based ML fault detection service
- [`k8s/`](k8s/): Kubernetes manifests and Helm charts
- [`experiments/`](experiments/): Example experiment configurations

## Development

### Local Development Setup

1. Build development Docker images:
```bash
just build-dev
```

2. Start the development environment:
```bash
just up dev=true
```

### Adding New Treatments

To create a new treatment:

1. Read the treatment interface in [`backend/internal/models/treatment.py`](backend/internal/models/treatment.py)
2. Create a new treatment class in [`backend/internal/treatments.py`](backend/internal/treatments.py)
3. Update the treatment key dictionary in [`backend/internal/runner.py`](backend/internal/runner.py)

### Example Treatment Configuration

```json
{
      "kubernetes_prometheus_rules": {
        "action": "kubernetes_prometheus_rules",
        "params": {
          "latency_threshold": 100,
          "evaluation_window": "120s",
          "quantile": 0.90
        }
      }
    }
```

## Known Issues

1. **Jaeger 500 Errors**
   - Sometimes returns 500 errors due to malformed trace timestamps
   - This can cause data loss in experiments
   - Status: High Memory usage is a possible cause

2. **Security Context Treatment**
   - The add security context treatment (for delay and packet loss treatments) may require 1-2 extra experiment runs to fully take effect
   - Failed experiments can be quickly restarted
   - Status: Known behavior
