#!/bin/bash
set -e

NAMESPACE="alloy"
CONFIG_FILE="./config.alloy"
VALUES_FILE="./values.yaml"
CONFIGMAP_NAME="alloy-config"
HELM_RELEASE_NAME="alloy"
HELM_CHART="grafana/alloy"

function delete_configmap() {
    echo "Deleting old ConfigMap..."
    kubectl delete configmap $CONFIGMAP_NAME -n $NAMESPACE --ignore-not-found
    echo "ConfigMap deleted."
}

function create_configmap() {
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "Error: $CONFIG_FILE not found."
        return
    fi
    echo "Creating new ConfigMap..."
    kubectl create configmap $CONFIGMAP_NAME -n $NAMESPACE --from-file=config.alloy=$CONFIG_FILE
    echo "ConfigMap created."
}

function helm_deploy() {
    if [ ! -f "$VALUES_FILE" ]; then
        echo "Error: $VALUES_FILE not found."
        return
    fi
    # Ensure namespace exists
    if ! kubectl get ns $NAMESPACE >/dev/null 2>&1; then
        echo "Namespace $NAMESPACE not found. Creating..."
        kubectl create ns $NAMESPACE
    fi

    echo "Upgrading/Installing Alloy via Helm..."
    helm upgrade --install $HELM_RELEASE_NAME $HELM_CHART -n $NAMESPACE -f $VALUES_FILE
    echo "Helm deployment complete."

    echo "Checking Alloy pods..."
    kubectl get pods -n $NAMESPACE -l app.kubernetes.io/name=alloy -o wide
}

function show_menu() {
    echo "Select an action:"
    echo "1) Delete ConfigMap"
    echo "2) Create ConfigMap"
    echo "3) Helm Upgrade/Install Alloy"
    echo "4) Exit"
    read -p "Enter your choice [1-4]: " choice
    case $choice in
        1) delete_configmap ;;
        2) create_configmap ;;
        3) helm_deploy ;;
        4) exit 0 ;;
        *) echo "Invalid choice";;
    esac
}

# Main loop
while true; do
    show_menu
    echo ""
done
