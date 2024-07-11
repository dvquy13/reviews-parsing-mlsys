# Install apps in GKE Cluster

> - Run `export ENV=<ENV>` with the target <ENV>, for example: `export ENV=dev`

```
# Init the env vars
export $(cat ../../.env.$ENV | grep -v "^#")
```

# Set up Traffic Exposure via Ingress NGINX

Ref:
- https://cert-manager.io/docs/tutorials/acme/nginx-ingress/
- https://kk-shichao.medium.com/expose-service-using-nginx-ingress-in-kind-cluster-from-wsl2-14492e153e99

```
# Check list of static IP address
gcloud compute addresses list

# Ref: https://serverfault.com/questions/796881/error-creating-gce-load-balancer-requested-address-ip-is-neither-static-nor-ass
# Must create regional static IP address (global not work)
# Choose the same region as your GKE cluster
gcloud compute addresses create $APP_NAME-$ENV --region $GCP_REGION
# Get IP_ADDRESS
export IP_ADDRESS=$(gcloud compute addresses list | grep $APP_NAME-$ENV | awk '{print $2}') && echo $IP_ADDRESS

## Create Nginx Ingress Controller to listen to request from the static IP
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm upgrade --install nginx-ingress ingress-nginx/ingress-nginx --set controller.service.loadBalancerIP=$IP_ADDRESS

kubectl wait --for=condition=ready pod --all --timeout=300s
```

> - Update openapi-$ENV.yaml with `<IP_ADDRESS>`

```
# Set up Cloud Endpoint to map domain with IP
gcloud endpoints services deploy openapi.$ENV.yaml
```

# Cert Manager to add TLS
Ref: Install with Helm: https://cert-manager.io/docs/installation/helm/
```
helm repo add jetstack https://charts.jetstack.io --force-update
helm repo update
helm install \
  cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --version v1.15.0 \
  --set crds.enabled=true

kubectl wait --namespace cert-manager --for=condition=ready --all pod --timeout=300s

kubectl apply -f cert-issuer.$ENV.yaml
```

# Install our custom Ingress
```
helm upgrade --install \
  --set env=$ENV \
  --set gcpProjectName=$GCP_PROJECT_NAME \
  main-ingress \
  ./ingress \
  -f ingress/values.yaml
```

# Install MLflow directly from Bitnami
```
helm upgrade --install mlflow oci://registry-1.docker.io/bitnamicharts/mlflow -f ../services/mlflow/values.$ENV.yaml

export MLFLOW_TRACKING_PASSWORD=$(kubectl get secret --namespace default mlflow-tracking -o jsonpath="{.data.admin-password }" | base64 -d)
sed -i "s/^MLFLOW_TRACKING_PASSWORD=.*/MLFLOW_TRACKING_PASSWORD=$MLFLOW_TRACKING_PASSWORD/" ../../.env.$ENV
```

> [!NOTE] Manual
> - Access MLflow UI at $ENV-$APP_NAME.endpoints.$GCP_PROJECT_NAME.cloud.goog/mlflow


---

# Delete all resources
```
helm list | awk 'NR>1 {print $1}' | xargs helm delete
kubectl delete --all ing
kubectl delete --all secret
kubectl get cm | grep -v "kube" | awk 'NR>1 {print $1}' | xargs kubectl delete cm
kubectl delete --all pvc
kubectl delete --all pv
kubectl delete --all po
kubectl delete ns cert-manager
kubectl delete -f cert-issuer.$ENV.yaml
```


---

# Archive

## Troubleshoot

### Set admissionWebhook to false to enable two ingress w.r.t. to one hostname and path

Error:
```
Error: UPGRADE FAILED: failed to create resource: admission webhook "validate.nginx.ingress.kubernetes.io" denied the request: host "XXX" and path "/mlflow/api(/|$)(.*)" is already defined in ingress default/main-ingress-mlflow
```

Workaround:
```
# Ref: https://github.com/kubernetes/ingress-nginx/issues/8216#issuecomment-1029586665
# To solve the MLflow issue of serving both UI and API behind reverse proxy
# Ref: https://github.com/mlflow/mlflow/issues/4484
# helm upgrade --install nginx-ingress ingress-nginx/ingress-nginx --set controller.service.loadBalancerIP=$IP_ADDRESS --set controller.admissionWebhooks.enabled=false
```
