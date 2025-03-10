# Windows PowerShell Commands for OXN Setup

## Environment Variables
```powershell
$env:TF_VAR_project_id = "advanced-cloud-prototyping"
$env:CLUSTER_NAME = "cluster-abc123.com"
$env:TF_VAR_zone = "europe-west1-b"
$env:NODE_COUNT = "3"
$env:CONTROL_PLANE_SIZE = "e2-standard-2"
$env:NODE_SIZE = "e2-standard-2"
$env:TF_VAR_bucket_name = "kops-state-abc123"
$env:TF_VAR_bucket_location = "EU"
```

## Up Command (Create Cluster)
```powershell
# Navigate to terraform directory
cd k8s/scripts

# Create GCS bucket
terraform apply -auto-approve

# Set kOps state store
$env:KOPS_STATE_STORE = "gs://$(terraform output -raw kops_state_store_bucket_name)"

# Create cluster configuration
Write-Host "Creating cluster configuration..."
kops create cluster `
    --name="$env:CLUSTER_NAME" `
    --state="$env:KOPS_STATE_STORE" `
    --zones="$env:TF_VAR_zone" `
    --control-plane-zones="$env:TF_VAR_zone" `
    --node-count="$env:NODE_COUNT" `
    --control-plane-size="$env:CONTROL_PLANE_SIZE" `
    --node-size="$env:NODE_SIZE" `
    --control-plane-count=1 `
    --networking=cilium `
    --cloud=gce `
    --project="$env:TF_VAR_project_id" `
    --set="spec.kubeAPIServer.enableAdmissionPlugins=PodNodeSelector" `
    --set="spec.kubeAPIServer.enableAdmissionPlugins=PodTolerationRestriction" `
    --set="spec.metricsServer.enabled=true" `
    --set="spec.metricsServer.insecure=true" `
    --yes

# Create and validate cluster
Write-Host "Creating the cluster..."
kops update cluster --name="$env:CLUSTER_NAME" --yes
kops export kubeconfig --admin

Write-Host "Waiting for cluster to be ready..."


# Label the node as the OXN host
$OXN_NODE_HOST = (kubectl get nodes -o jsonpath='{.items[?(@.metadata.labels.node-role\.kubernetes\.io/node=="")].metadata.name}' | Select-String -Pattern '\S+' | ForEach-Object { $_.Matches.Value } | Select-Object -First 1)
kubectl label node "$OXN_NODE_HOST" "app=oxn-host"
```

## Install Command
```powershell
# Install OpenEBS
Write-Host "Installing OpenEBS..."
kubectl apply -f https://openebs.github.io/charts/openebs-operator.yaml

# Install Jaeger storage
kubectl apply -f k8s/manifests/jaeger_pv.yaml
kubectl apply -f k8s/manifests/jaeger_pvc.yaml

# Install Prometheus Stack
Write-Host "Installing Prometheus Stack..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install kube-prometheus prometheus-community/kube-prometheus-stack `
    --namespace oxn-external-monitoring `
    --create-namespace `
    --version 62.5.1 `
    -f k8s/manifests/values_kube_prometheus.yaml

# Install OpenTelemetry Demo
Write-Host "Installing OpenTelemetry Demo..."
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm repo update
helm install astronomy-shop open-telemetry/opentelemetry-demo `
    --namespace system-under-evaluation `
    --create-namespace `
    --version 0.34.2 `
    -f k8s/manifests/values_opentelemetry_demo.yaml

# Install OXN Platform
Write-Host "Installing OXN Platform..."
kubectl create namespace oxn --dry-run=client -o yaml | kubectl apply -f -
# For development mode, uncomment the following line and comment out the next line
# helm install oxn-platform k8s/oxn-platform --set backend-chart.enabled=false --set backend-dev-chart.enabled=true
helm install oxn-platform k8s/oxn-platform

# Wait for OpenTelemetry Demo pods
Write-Host "Waiting for OpenTelemetry Demo pods to be ready..."
kubectl wait --for=condition=ready pod `
    --all `
    -n system-under-evaluation `
    --timeout=300s
```

## Down Command (Destroy Cluster)
```powershell
# Navigate to terraform directory
cd k8s/scripts

# Set kOps state store
$env:KOPS_STATE_STORE = "gs://$(terraform output -raw kops_state_store_bucket_name)"

# Delete the cluster
Write-Host "Deleting cluster..."
kops delete cluster --name "$env:CLUSTER_NAME" --yes

# Destroy terraform resources
Write-Host "Destroying terraform resources..."
terraform destroy -auto-approve
```

## Run Batch Experiment Command
```powershell
# Function to run batch experiments
function Run-BatchExperiment {
    param(
        [Parameter(Mandatory=$true)]
        [string]$ConfigPath,
        
        [Parameter(Mandatory=$false)]
        [int]$Times = 1
    )

    # Check if config file exists
    if (-not (Test-Path $ConfigPath)) {
        Write-Error "Config file $ConfigPath not found"
        exit 1
    }

    # Get backend pod
    $backendPod = (kubectl get pods -n oxn | Select-String "^backend" | ForEach-Object { $_.Line.Split()[0] })

    # Start port-forward in background
    $portForwardJob = Start-Job -ScriptBlock {
        param($pod, $namespace)
        kubectl port-forward -n $namespace $pod 8000:8000
    } -ArgumentList $backendPod, "oxn"

    # Wait for port-forward to be ready
    Start-Sleep -Seconds 3

    # Read config file
    $configJson = Get-Content $ConfigPath -Raw
    Write-Host $configJson

    # Create the experiment and extract the id
    $experimentId = (Invoke-RestMethod -Uri "http://localhost:8000/experiments/batch" `
        -Method Post `
        -Headers @{
            "accept" = "application/json"
            "Content-Type" = "application/json"
        } `
        -Body $configJson).id

    # Run the experiment
    Invoke-RestMethod -Uri "http://localhost:8000/experiments/batch/$experimentId/run?analyze=true" `
        -Method Post `
        -Headers @{
            "accept" = "application/json"
            "Content-Type" = "application/json"
        } `
        -Body (ConvertTo-Json @{
            runs = $Times
            output_formats = @("json")
        })

    # Wait for results to be ready
    Start-Sleep -Seconds 10

    # Download results
    Invoke-WebRequest -Uri "http://localhost:8000/experiments/$experimentId/data" `
        -Headers @{
            "accept" = "application/json"
        } `
        -OutFile "data"

    # Move results to desired location
    Move-Item -Path "data" -Destination "C:\Users\lucca\Documents\Uni\oxn-data\$experimentId.zip" -Force

    # Clean up port-forward
    Stop-Job -Job $portForwardJob
    Remove-Job -Job $portForwardJob
}

# Example usage:
# Run-BatchExperiment -ConfigPath "path/to/config.json" -Times 1
```

## Notes
1. Make sure you have the following tools installed:
   - PowerShell
   - kubectl
   - helm
   - terraform
   - kops
   - gcloud CLI

2. Before running these commands:
   - Make sure you're authenticated with Google Cloud (`gcloud auth login`)
   - Have the correct project selected (`gcloud config set project advanced-cloud-prototyping`)
   - Have the necessary permissions in your Google Cloud project

3. The environment variables are set for the current PowerShell session only. If you open a new PowerShell window, you'll need to set them again.

4. For development mode, uncomment the development helm install line and comment out the production line in the install section. 