#!/bin/bash
if [ $# -ne 2 ]; then
    echo "Usage: $0 <remote-results-path> <local-destination-dir>"
    echo "Example: $0 /opt/oxn/results /local/path/to/results"
    exit 1
fi

REMOTE_PATH="$1"
LOCAL_PATH="$2"
CONTROL_PLANE_NODE=$(kubectl get nodes --selector=node-role.kubernetes.io/control-plane -o jsonpath='{.items[0].metadata.name}')

mkdir -p "${LOCAL_PATH}"
gcloud compute scp --recurse "${CONTROL_PLANE_NODE}:${REMOTE_PATH}/*" "${LOCAL_PATH}/"
