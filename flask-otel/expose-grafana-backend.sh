#!/bin/bash
# Expose Loki, Tempo, and Mimir publicly via 0.0.0.0
# Use this only in a controlled lab environment (not production)

set -e

echo "Starting port forwarding on 0.0.0.0 for Loki, Tempo, and Mimir..."

# Kill any previous port-forwards
pkill -f "kubectl port-forward" || true

# Loki
kubectl port-forward svc/loki-gateway -n loki 3100:80 --address 0.0.0.0 &
sleep 2

# Tempo
kubectl port-forward svc/tempo-gateway -n tempo-test 3200:80 --address 0.0.0.0 &
sleep 2

# Mimir
kubectl port-forward svc/mimir-gateway -n mimir-test 9090:80 --address 0.0.0.0 &
sleep 2

echo "----------------------------------------------------------------"
echo "Grafana Data Source Endpoints:"
echo "  Loki:  http://0.0.0.0:3100"
echo "  Tempo: http://0.0.0.0:3200"
echo "  Mimir: http://0.0.0.0:9090"
echo "----------------------------------------------------------------"
echo "Access from outside EC2 via: http://<your-ec2-public-ip>:<port>"
echo "----------------------------------------------------------------"

wait
