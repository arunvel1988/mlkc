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

function update_configmap() {
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "Error: $CONFIG_FILE not found."
        return
    fi
    echo "Updating ConfigMap..."
    delete_configmap
    create_configmap
    echo "ConfigMap updated successfully."
}

function restart_alloy() {
    echo "Restarting Alloy pods..."
    
    # Check if it's a deployment or daemonset
    if kubectl get deployment -n $NAMESPACE -l app.kubernetes.io/name=alloy &>/dev/null; then
        kubectl rollout restart deployment -n $NAMESPACE -l app.kubernetes.io/name=alloy
        echo "Waiting for rollout to complete..."
        kubectl rollout status deployment -n $NAMESPACE -l app.kubernetes.io/name=alloy --timeout=120s
    elif kubectl get daemonset -n $NAMESPACE -l app.kubernetes.io/name=alloy &>/dev/null; then
        kubectl rollout restart daemonset -n $NAMESPACE -l app.kubernetes.io/name=alloy
        echo "Waiting for rollout to complete..."
        kubectl rollout status daemonset -n $NAMESPACE -l app.kubernetes.io/name=alloy --timeout=120s
    else
        echo "No deployment or daemonset found for Alloy. Trying to delete pods..."
        kubectl delete pods -n $NAMESPACE -l app.kubernetes.io/name=alloy
    fi
    
    echo "Restart complete."
    echo ""
    echo "Checking Alloy pods..."
    kubectl get pods -n $NAMESPACE -l app.kubernetes.io/name=alloy -o wide
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

function full_update() {
    echo "=== Performing Full Update ==="
    update_configmap
    echo ""
    restart_alloy
}

function show_logs() {
    echo "Fetching logs from Alloy pods..."
    POD=$(kubectl get pods -n $NAMESPACE -l app.kubernetes.io/name=alloy -o jsonpath='{.items[0].metadata.name}')
    if [ -z "$POD" ]; then
        echo "No Alloy pods found."
        return
    fi
    echo "Showing logs for pod: $POD"
    kubectl logs -n $NAMESPACE $POD --tail=50 -f
}

function show_pod_status() {
    echo "=== Alloy Pod Status ==="
    kubectl get pods -n $NAMESPACE -l app.kubernetes.io/name=alloy -o wide
    echo ""
    echo "=== Recent Events ==="
    kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' | grep -i alloy | tail -10
}

function show_menu() {
    echo "======================================"
    echo "       Alloy Deployment Menu"
    echo "======================================"
    echo "1) Delete ConfigMap"
    echo "2) Create ConfigMap"
    echo "3) Update ConfigMap (Delete + Create)"
    echo "4) Restart Alloy Pods (Rollout Restart)"
    echo "5) Full Update (ConfigMap + Restart)"
    echo "6) Helm Upgrade/Install Alloy"
    echo "7) Show Alloy Logs"
    echo "8) Show Pod Status"
    echo "9) Exit"
    echo "======================================"
    read -p "Enter your choice [1-9]: " choice
    
    case $choice in
        1) delete_configmap ;;
        2) create_configmap ;;
        3) update_configmap ;;
        4) restart_alloy ;;
        5) full_update ;;
        6) helm_deploy ;;
        7) show_logs ;;
        8) show_pod_status ;;
        9) exit 0 ;;
        *) echo "Invalid choice";;
    esac
}

# Main loop
while true; do
    show_menu
    echo ""
    read -p "Press Enter to continue..."
    clear
done
