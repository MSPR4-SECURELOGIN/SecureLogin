#!/bin/bash
set -e

# Check prerequisites
for cmd in docker kubectl helm faas-cli; do
    if ! command -v $cmd >/dev/null 2>&1; then
        echo "Error: $cmd is required but not installed." >&2
        exit 1
    fi
done

# Install OpenFaaS if not already installed
if ! kubectl get namespace openfaas >/dev/null 2>&1; then
    echo "Installing OpenFaaS via helm..."
    helm repo add openfaas https://openfaas.github.io/faas-netes/
    kubectl apply -f https://raw.githubusercontent.com/openfaas/faas-netes/master/namespaces.yml
    PASSWORD=$(head -c 12 /dev/urandom | shasum | cut -d' ' -f1)
    kubectl -n openfaas create secret generic basic-auth \
      --from-literal=basic-auth-user=admin \
      --from-literal=basic-auth-password="$PASSWORD"
    helm upgrade --install openfaas openfaas/openfaas \
      --namespace openfaas \
      --set basic_auth=true \
      --set functionNamespace=openfaas-fn \
      --set serviceType=NodePort \
      --wait
else
    PASSWORD=$(kubectl -n openfaas get secret basic-auth -o jsonpath='{.data.basic-auth-password}' | base64 --decode)
    echo "OpenFaaS already installed."
fi

# Port-forward gateway
kubectl -n openfaas port-forward svc/gateway 8080:8080 &
PF_PID=$!
sleep 5

# Deploy Postgres
kubectl apply -f postgres-init.yaml
kubectl apply -f postgres-deployment.yaml

# Wait for Postgres
kubectl -n openfaas wait --for=condition=ready pod -l app=postgres --timeout=180s

# Deploy functions
for stack in functions/*/stack.yml; do
    faas-cli deploy -f "$stack"
done

# Update frontend password
sed -i "s/const faasPassword = \".*\";/const faasPassword = \"$PASSWORD\";/" frontend/script.js

# Start frontend container
docker compose up -d

printf '\nFrontend available at http://localhost:8081\n'
printf 'OpenFaaS gateway at http://localhost:8080 (admin/%s)\n' "$PASSWORD"
printf 'Press Ctrl+C to stop port-forwarding when finished.\n'
wait $PF_PID
