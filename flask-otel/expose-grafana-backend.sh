#!/bin/bash
set -e

echo "Starting port forwarding on 0.0.0.0 for Loki, Tempo, and Mimir..."

# Loki (namespace: default)
kubectl port-forward svc/loki-test-gateway -n default 3100:80 --address=0.0.0.0 &
LOKI_PID=$!

# Tempo (namespace: tempo-test)
kubectl port-forward svc/tempo-query-frontend -n tempo-test 3200:3200 --address=0.0.0.0 &
TEMPO_PID=$!

# Mimir (namespace: mimir-test)
kubectl port-forward svc/mimir-gateway -n mimir-test 9090:80 --address=0.0.0.0 &
MIMIR_PID=$!

echo "----------------------------------------------------------------"
echo "Grafana Data Source Endpoints:"
echo "  Loki:  http://0.0.0.0:3100"
echo "  Tempo: http://0.0.0.0:3200"
echo "  Mimir: http://0.0.0.0:9090"
echo "----------------------------------------------------------------"
echo "Access from outside EC2 via: http://<your-ec2-public-ip>:<port>"
echo "----------------------------------------------------------------"

trap "kill $LOKI_PID $TEMPO_PID $MIMIR_PID" EXIT
wait
