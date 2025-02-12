set dotenv-load
# List available recipes
default:
    @just --list

#### Variables ####
kubernetes_dir:="k8s"
terraform_dir:=kubernetes_dir/"scripts"
backend_dir:="backend"
analysis_dir:=kubernetes_dir/"analysis"
manifests_dir:=kubernetes_dir/"manifests"

# Setup required GCP APIs
setup:
    #!/bin/bash
    gcloud services enable cloudresourcemanager.googleapis.com
    gcloud services enable compute.googleapis.com
    gcloud services enable iam.googleapis.com
    gcloud services enable container.googleapis.com
    gcloud services enable storage.googleapis.com

# Initialize terraform
init:
    cd {{terraform_dir}} && terraform init

# Create and configure the cluster
up spot="":
    #!/bin/bash
    set -e
    cd {{terraform_dir}}
    # Create GCS bucket
    terraform apply -auto-approve

    echo $(pwd)

    # Set kOps state store
    export KOPS_STATE_STORE="gs://$(terraform output -raw kops_state_store_bucket_name)"

    echo $NODE_SIZE

    # Create cluster configuration
    echo "Creating cluster configuration..."
    kops create cluster \
        --name="${CLUSTER_NAME}" \
        --state="${KOPS_STATE_STORE}" \
        --zones="${TF_VAR_zone}" \
        --control-plane-zones="${TF_VAR_zone}" \
        --node-count="${NODE_COUNT}" \
        --control-plane-size="${CONTROL_PLANE_SIZE}" \
        --node-size="${NODE_SIZE}" \
        --control-plane-count=1 \
        --networking=cilium \
        --cloud=gce \
        --project="${TF_VAR_project_id}" \
        --set="spec.kubeAPIServer.enableAdmissionPlugins=PodNodeSelector" \
        --set="spec.kubeAPIServer.enableAdmissionPlugins=PodTolerationRestriction" \
        --set="spec.metricsServer.enabled=true" \
        --set="spec.metricsServer.insecure=true" \
        --yes

    if [ -n "$spot" ]; then
        # Configure spot instances
        echo "Modifying instance groups to use spot instances..."
        kops get ig --name "${CLUSTER_NAME}" -o yaml > ig_specs.yaml
        sed -i '/spec:/a\  gcpProvisioningModel: SPOT' ig_specs.yaml
        kops replace -f ig_specs.yaml
    fi

    # Create and validate cluster
    echo "Creating the cluster..."
    kops update cluster --name="${CLUSTER_NAME}" --yes
    kops export kubeconfig --admin
    
    echo "Waiting for cluster to be ready..."
    kops validate cluster --wait 10m

    # Label the node as the OXN host
    OXN_NODE_HOST=$(kubectl get nodes -o jsonpath='{.items[?(@.metadata.labels.node-role\.kubernetes\.io/node=="")].metadata.name}' | awk '{print $1}')
    kubectl label node "$OXN_NODE_HOST" "app=oxn-host"


# Install SUE and OXN
install dev="false":
    #!/bin/bash
    echo "Installing OpenEBS..."
    kubectl apply -f https://openebs.github.io/charts/openebs-operator.yaml

    echo "Installing Prometheus Stack..."
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update
    helm install kube-prometheus prometheus-community/kube-prometheus-stack \
        --namespace oxn-external-monitoring \
        --create-namespace \
        --version 62.5.1 \
        -f {{manifests_dir}}/values_kube_prometheus.yaml

    echo "Installing OpenTelemetry Demo..."
    helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
    helm repo update
    helm install astronomy-shop open-telemetry/opentelemetry-demo \
        --namespace system-under-evaluation \
        --create-namespace \
        --version 0.34.2 \
        -f {{manifests_dir}}/values_opentelemetry_demo.yaml

    echo "Installing OXN Platform..."
    kubectl create namespace oxn --dry-run=client -o yaml | kubectl apply -f -
    if [ {{dev}} == "true" ]; then helm install oxn-platform {{kubernetes_dir}}/oxn-platform --set backend-chart.enabled=false --set backend-dev-chart.enabled=true; else helm install oxn-platform {{kubernetes_dir}}/oxn-platform; fi

    echo "Waiting for OpenTelemetry Demo pods to be ready..."
    kubectl wait --for=condition=ready pod \
        --all \
        -n system-under-evaluation \
        --timeout=300s

# Destroy the cluster and clean up resources
down:
    #!/bin/bash
    set -e
    cd {{terraform_dir}}
    export KOPS_STATE_STORE="gs://$( terraform output -raw kops_state_store_bucket_name)"
    kops delete cluster --name "${CLUSTER_NAME}" --yes
    terraform destroy -auto-approve

# Validate cluster status
validate:
    export KOPS_STATE_STORE="gs://$( cd {{terraform_dir}} && terraform output -raw kops_state_store_bucket_name)" && \
    kops validate cluster

# Get cluster info
get-cluster:
    export KOPS_STATE_STORE="gs://$( cd {{terraform_dir}} && terraform output -raw kops_state_store_bucket_name)" && \
    kops get cluster

# Export kubeconfig
get-kubeconfig:
    export KOPS_STATE_STORE="gs://$( cd {{terraform_dir}} && terraform output -raw kops_state_store_bucket_name)" && \
    kops export kubeconfig --admin

datamodels:
    datamodel-codegen --input backend/internal/schemas/experiment_schema.json --input-file-type jsonschema --output backend/internal/models/experiment.py
build-dev:
    docker build -t $OXN_DEV_REPOSITORY/oxn-dev:latest --push {{backend_dir}}

# TODO
run-batch-experiment config_path="" output_path="" times="1":
    #!/bin/bash
    if [ ! -f {{config_path}} ]; then echo "Config file {{config_path}} not found"; exit 1; fi
    # first get backend pod
    backend_pod=$(kubectl get pods -n oxn | grep ^backend | awk '{print $1}')
    # then port forward 8000 in a separate process
    kubectl port-forward -n oxn $backend_pod 8000:8000 &
    sleep 3
    config_json=$(cat {{config_path}})
    echo $config_json
    # Create the experiment and extract the id
    experiment_id=$(curl -X POST \
        'http://localhost:8000/experiments/batch' \
        -H 'accept: application/json' \
        -H 'Content-Type: application/json' \
        -d "$config_json" | jq -r '.id')

    # Run the experiment (this blocks until the experiment is finished)
    curl -X POST \
        "http://localhost:8000/experiments/batch/${experiment_id}/run?analyze=true" \
        -H 'accept: application/json' \
        -H 'Content-Type: application/json' \
        -d '{"runs": '{{times}}', "output_formats": ["json"]}'

    sleep 10
    # then get the zip file (the results ) from this endpoint
    curl -X GET \
        "http://localhost:8000/experiments/${experiment_id}/data" \
        -H 'accept: application/json' \
        -O
    mv data {{output_path}}.zip
    # Clean up port-forward - this may fail if the port-forward is not running because you might have created a separate port-forward
    pkill -f "kubectl port-forward.*8000:8000"

run-single-experiment config_path="" output_path="" times="1":
    #!/bin/bash
    if [ ! -f {{config_path}} ]; then echo "Config file {{config_path}} not found"; exit 1; fi
    # first get backend pod
    backend_pod=$(kubectl get pods -n oxn | grep ^backend | awk '{print $1}')
    # then port forward 8000 in a separate process
    kubectl port-forward -n oxn $backend_pod 8000:8000 &
    sleep 3
    config_json=$(cat {{config_path}})
    echo $config_json
    # Create the experiment and extract the id
    experiment_id=$(curl -X POST \
        'http://localhost:8000/experiments' \
        -H 'accept: application/json' \
        -H 'Content-Type: application/json' \
        -d "$config_json" | jq -r '.id')
    # Run the experiment (this blocks until the experiment is finished)
    curl -X POST \
        "http://localhost:8000/experiments/${experiment_id}/runsync" \
        -H 'accept: application/json' \
        -H 'Content-Type: application/json' \
        -d '{"runs": '{{times}}', "output_formats": ["json"]}'

    sleep 10
    # then get the zip file (the results ) from this endpoint
    curl -X GET \
        "http://localhost:8000/experiments/${experiment_id}/data" \
        -H 'accept: application/json' \
        -O
    mv data {{output_path}}.zip
    # Clean up port-forward
    pkill -f "kubectl port-forward.*8000:8000"

upgrade:
    helm upgrade astronomy-shop open-telemetry/opentelemetry-demo --namespace system-under-evaluation  -f {{manifests_dir}}/values_opentelemetry_demo.yaml
generate-env:
    #!/usr/bin/env bash
    if [ -f .env ]; then
        echo ".env file already exists. Please remove it first if you want to generate a new one."
        exit 1
    fi
    
    RANDOM_SUFFIX=$(LC_ALL=C tr -dc 'a-z0-9' < /dev/urandom | head -c 6)
    
    cat > .env << EOF
    TF_VAR_project_id="advanced-cloud-prototyping"
    CLUSTER_NAME="cluster-${RANDOM_SUFFIX}.com"
    TF_VAR_zone="europe-west1-b"
    NODE_COUNT="3"
    CONTROL_PLANE_SIZE="e2-standard-2"
    NODE_SIZE="e2-standard-2"
    TF_VAR_bucket_name="kops-state-${RANDOM_SUFFIX}"
    TF_VAR_bucket_location="EU"
    EOF
    
    echo ".env file generated with default values. Please modify as needed."
    echo "The variables are automatically sourced :)"

env-check:
    echo $TF_VAR_project_id
    echo $CLUSTER_NAME
    echo $TF_VAR_zone
    echo $NODE_COUNT
    echo $CONTROL_PLANE_SIZE
    echo $NODE_SIZE
    echo $TF_VAR_bucket_name
    echo $TF_VAR_bucket_location