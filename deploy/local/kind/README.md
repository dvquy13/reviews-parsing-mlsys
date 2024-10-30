
```
kind create cluster --config kind-config.yaml

# Set up Ingress NGINX
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s

# Install directly from Bitnami
helm install mlflow oci://registry-1.docker.io/bitnamicharts/mlflow -f values.yaml
```