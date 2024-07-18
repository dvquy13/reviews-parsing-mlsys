# Create cluster

> - Run `export ENV=<ENV>` with the target <ENV>, for example: `export ENV=staging`
> - `cd <ROOT>/deploy/gke/terraform`
> - `terraform apply --var="env=$ENV"

# Install apps in GKE Cluster

> - `cd <ROOT>/deploy/gke`

```
# Init the env vars
export $(cat ../../.env.$ENV | grep -v "^#")
gcloud container clusters get-credentials $APP_NAME --zone $GCP_ZONE --project $GCP_PROJECT_NAME
kubectl config use-context gke_${GCP_PROJECT_NAME}_${GCP_ZONE}_${APP_NAME}
```

---

# Set up Traffic Exposure via Ingress NGINX

## Cert Manager to add TLS
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
```

## Install NGINX controller
Ref:
- https://cert-manager.io/docs/tutorials/acme/nginx-ingress/
- https://kk-shichao.medium.com/expose-service-using-nginx-ingress-in-kind-cluster-from-wsl2-14492e153e99

```
# Get IP_ADDRESS
export IP_ADDRESS=$(gcloud compute addresses list | grep $ENV-$APP_NAME | awk '{print $2}') && echo $IP_ADDRESS

## Create Nginx Ingress Controller to listen to request from the static IP
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm upgrade --install nginx-ingress ingress-nginx/ingress-nginx --set controller.service.loadBalancerIP=$IP_ADDRESS
kubectl wait --for=condition=ready pod --all --timeout=300s
sed -i 's/target: ".*"/target: "'"$IP_ADDRESS"'"/g' openapi.$ENV.yaml
```

```
# Set up Cloud Endpoint to map domain with IP
gcloud endpoints services deploy openapi.$ENV.yaml
```

## Install our custom Ingress
```
kubectl create namespace monitoring
helm upgrade --install \
  --set env=$ENV \
  --set gcpProjectName=$GCP_PROJECT_NAME \
  --set emailForCertIssuer=$USER_EMAIL \
  main-ingress \
  ./ingress \
  -f ingress/values.yaml
```

# Check if the output contains "SSL certificate verify ok"
ssl_check=$(curl -s -I -v --stderr - "$URL" 2>&1)
if echo "$ssl_check" | grep -q "SSL certificate verify ok"; then
    echo "The TLS certificate for $URL is valid."
else
    echo "The TLS certificate for $URL is not valid or could not be verified."
fi

---

# Install MLflow
```
# Install with Helm
helm upgrade --install mlflow oci://registry-1.docker.io/bitnamicharts/mlflow -f ../services/mlflow/values.yaml
export MLFLOW_TRACKING_PASSWORD=$(kubectl get secret --namespace default mlflow-tracking -o jsonpath="{.data.admin-password }" | base64 -d)
sed -i "s/^MLFLOW_TRACKING_PASSWORD=.*/MLFLOW_TRACKING_PASSWORD=$MLFLOW_TRACKING_PASSWORD/" ../../.env.$ENV
kubectl wait --selector='!job-name' --for=condition=ready --all po --timeout=300s 
echo "Try access MLflow UI at: https://$ENV-$APP_NAME.endpoints.$GCP_PROJECT_NAME.cloud.goog/mlflow with $MLFLOW_TRACKING_USERNAME/$MLFLOW_TRACKING_PASSWORD"
# Disable VPA after finding that VPA update can make MLflow Tracking Server to stop working
# Apply VPA
# kubectl apply -f ../services/mlflow/vpa.yaml
```

---

# Model training

The next section works by assuming that we already have a trained model named `reviews-parsing-ner-aspects@champion`.

> [!NOTE]
> To create this model: 
> - Run the notebooks/train.ipynb notebook
> - Register and create the alias `champion` for the trained model on MLflow

---

# Observability

## Prometheus and Grafana
```
# Prometheus
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm upgrade --install prometheus prometheus-community/prometheus \
  --namespace monitoring --create-namespace
kubectl wait -n monitoring --selector='!job-name' --for=condition=ready --all po --timeout=300s

# Grafana
helm upgrade --install grafana grafana/grafana \
  -f ../services/grafana/values.yaml \
  --set 'grafana\.ini'.server.root_url=https://$ENV-$APP_NAME.endpoints.$GCP_PROJECT_NAME.cloud.goog/grafana \
  --namespace monitoring
export GRAFANA_ADMIN_PASSWORD=$(kubectl get secret --namespace monitoring grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo)
sed -i "s/^GRAFANA_ADMIN_PASSWORD=.*/GRAFANA_ADMIN_PASSWORD=$GRAFANA_ADMIN_PASSWORD/" ../../.env.$ENV
kubectl wait -n monitoring --selector='!job-name' --for=condition=ready --all po --timeout=300s
echo "Access Grafana at: https://$ENV-$APP_NAME.endpoints.$GCP_PROJECT_NAME.cloud.goog/grafana with admin/$GRAFANA_ADMIN_PASSWORD"
```

> [!NOTE]
> Connecting Grafana with Prometheus Data Source via this URL: `http://prometheus-server.monitoring.svc.cluster.local:80`
> 
> Starter Grafana Dashboard: K8s Resource Monitoring: id=`17375` and id=`315`

## Jaeger
```
helm upgrade --install jaeger oci://registry-1.docker.io/bitnamicharts/jaeger -n monitoring -f ../services/jaeger/values.yaml
kubectl wait -n monitoring --selector='!job-name' --for=condition=ready --all po --timeout=300s
```

> [!WARNING]
> When deleting Jaeger with `helm delete`, make sure you delete the PVC `data-jaeger-cassandra-0` as well otherwise when restarting we might run into password incorrect error.

---

# Deploy Model Inference Service to K8s with KServe

Ref:
- https://knative.dev/docs/install/yaml-install/serving/install-serving-with-yaml/#prerequisites

## Install cosign
```
# Ref: https://docs.sigstore.dev/system_config/installation/
LATEST_VERSION=$(curl https://api.github.com/repos/sigstore/cosign/releases/latest | grep tag_name | cut -d : -f2 | tr -d "v\", ")
curl -O -L "https://github.com/sigstore/cosign/releases/latest/download/cosign_${LATEST_VERSION}_amd64.deb"
sudo dpkg -i cosign_${LATEST_VERSION}_amd64.deb
rm -rf cosign_${LATEST_VERSION}_amd64.deb
```

## Install required CRDs
```
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.14.1/serving-crds.yaml
```

## Install core components of Knative Serving
```
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.14.1/serving-core.yaml
kubectl wait -n knative-serving --for=condition=ready --all po --timeout=300s
```

## Install Networking Layer with Istio
```
kubectl apply -l knative.dev/crd-install=true -f https://github.com/knative/net-istio/releases/download/knative-v1.14.1/istio.yaml
# Do not apply the raw version of istio.yaml because of high resource request
# kubectl apply -f https://github.com/knative/net-istio/releases/download/knative-v1.14.1/istio.yaml
# Download the istio.yaml file and modify resource request
kubectl apply -f ../services/istio/istio.yaml
kubectl apply -f https://github.com/knative/net-istio/releases/download/knative-v1.14.1/net-istio.yaml
kubectl wait -n istio-system --for=condition=ready --all po --timeout=300s
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.14.1/serving-default-domain.yaml
kubectl wait -n knative-serving --selector='!job-name' --for=condition=ready --all po --timeout=300s
export ISTIO_IP=$(kubectl --namespace istio-system get service istio-ingressgateway | awk 'NR>1 {print $4}')
sed -i "s/^ISTIO_IP=.*/ISTIO_IP=$ISTIO_IP/" ../../.env.$ENV
echo "ISTIO sslip.io available at: $ISTIO_IP.sslip.io"
```

> [!NOTE]
> New approach has already been implemented by downloading the istio.yaml file and modify the resource request there.
> Below is old approach:
> If you encounter unschedulable error with the Inference Service, consider update Istio Resource Request to free up allocable:
> - `kubectl edit deploy istio-ingressgateway --namespace istio-system`, change request 1 CPU and 1Gi Memory to 200m CPU and 200Mi Memory
> - `kubectl edit deploy istiod --namespace istio-system`, change request 500m CPU and 2Gi Memory to 200m CPU and 300Mi Memory
> - Delete all the unscheduled/pending deployments
> - TODO: Modify the installation instruction to download the manifest and modify the resources request there instead.

## Install KServe
```
kubectl apply -f https://github.com/kserve/kserve/releases/download/v0.13.0/kserve.yaml
kubectl wait -n kserve --selector='!job-name' --for=condition=ready --all po --timeout=300s
kubectl apply -f https://github.com/kserve/kserve/releases/download/v0.13.0/kserve-cluster-resources.yaml
kubectl wait -n kserve --selector='!job-name' --for=condition=ready --all po --timeout=300s
```

## Configure Knative cluster to deploy images from private registry

> [!IMPORTANT]
> Update the `../../.env.$ENV` file with your own `PRIVATE_REGISTRY_*` credentials

Ref: https://knative.dev/docs/serving/deploying-from-private-registry/
```
export $(cat ../../.env.$ENV | grep -v "^#")
kubectl create secret --namespace default docker-registry $REGISTRY_CREDENTIAL_SECRETS \
  --docker-server=$PRIVATE_REGISTRY_URL \
  --docker-email=$PRIVATE_REGISTRY_EMAIL \
  --docker-username=$PRIVATE_REGISTRY_USER \
  --docker-password=$PRIVATE_REGISTRY_PASSWORD
```

## Push the MLServer Inference Docker to Dockerhub
```
cd ../../models/reviews-parsing-ner-aspects
make build
make push
cd ../../deploy/gke
```

> [!IMPORTANT]
> Update the model image with tag at `../services/kserve/inference.yaml`

## Deploy the MLServer

### Create app-secret
> [!WARNING]
> Be careful to submit `.env` with single quote enclosing values.
> We may need to preprocess them to make the `--from-env-file` work.
```
kubectl create secret generic app-secret --from-env-file=../../.env.$ENV
```

### Deploy the inferenceservice
```
kubectl apply -f ../services/kserve/inference.yaml --namespace default
# Sleep to wait for the pod predictor to appear before we can wait for it
sleep(5)
kubectl wait --selector='!job-name' --for=condition=ready --all po --timeout=300s
echo "Access the KServe Model Swagger docs at: http://reviews-parsing-ner-aspects-mlserver.default.$ISTIO_IP.sslip.io/v2/models/reviews-parsing-ner-aspects/docs"
```

Test inference:
```
curl -X 'POST' \
  "http://reviews-parsing-ner-aspects-mlserver.default.$ISTIO_IP.sslip.io/v2/models/reviews-parsing-ner-aspects/infer" \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": "string",
  "parameters": {
    "content_type": "string",
    "headers": {},
    "additionalProp1": {}
  },
  "inputs": [
    {
      "name": "input-0",
      "shape": [
        2
      ],
      "datatype": "BYTES",
      "data": ["Delicious food friendly staff and one good celebration!", "What an amazing dining experience"]
    }
  ]
}'
```

---

# Delete all resources
## Delete all resources but retaining cluster
```
./delete-installed.sh
```
## Delete cluster
```
cd terraform
terraform destroy --var="env=$ENV"
# Be careful that the below command would delete all compute disks regardless of them being related to the deleted GKE cluster or not
for disk in $(gcloud compute disks list --format="value(name,zone)" | awk '{print $1}'); do
  zone=$(gcloud compute disks list --filter="name:$disk" --format="value(zone)")
  gcloud compute disks delete $disk --zone=$zone --quiet
done
cd ..
```

---

# Set up VPA

> [!CAUTION]
> In this cluster setup we have observed situations where the VPA updates MLflow Tracking Server resource requests which caused it to stop working
> Because of this, we disable the use of VPA for this cluster

```
kubectl create clusterrolebinding cluster-admin-binding --clusterrole=cluster-admin --user=$GCLOUD_ACCOUNT

git clone https://github.com/kubernetes/autoscaler.git
cd autoscaler/vertical-pod-autoscaler && \
  ./hack/vpa-up.sh && \
  cd ../..
```

---

## Edit VPA's Updater min-replicas from 2 to 1 so that updater can update resource requests based on recommendation

> [!CAUTION]
> Use this with caution. Should only use to test VPA function or when you know what you're doing.
> Known issues: VPA MLflow Tracking Server continuously crashes, probably due to miscalculation from VPA.

Ref: https://github.com/kubernetes/autoscaler/blob/master/vertical-pod-autoscaler/FAQ.md#what-are-the-parameters-to-vpa-updater

> - Run `kubectl edit deploy vpa-updater -n kube-system` to edit Updater deployment
> - Add args to container like this:
>   ```
>   containers:
>   - name: updater
>     image: registry.k8s.io/autoscaling/vpa-updater:0.10.0
>     args:
>     - --min-replicas=1
>     # other existing args
>   ```

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
