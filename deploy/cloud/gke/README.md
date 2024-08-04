TOC:
- [Prerequisite](#prerequisite)
- [Create cluster](#create-cluster)
- [Install apps in GKE Cluster](#install-apps-in-gke-cluster)
  - [Get GKE cluster credentials](#get-gke-cluster-credentials)
  - [Set up Traffic Exposure via Ingress Nginx](#set-up-traffic-exposure-via-ingress-nginx)
    - [Cert Manager to add TLS](#cert-manager-to-add-tls)
    - [Install NGINX controller](#install-nginx-controller)
      - [Set up Cloud Endpoints to map a FQDN with our static IP](#set-up-cloud-endpoints-to-map-a-fqdn-with-our-static-ip)
    - [Install our custom Ingress](#install-our-custom-ingress)
      - [Check TLS applies OK](#check-tls-applies-ok)
  - [Observability](#observability)
    - [Prometheus and Grafana](#prometheus-and-grafana)
    - [Jaeger](#jaeger)
  - [CI/CD](#cicd)
    - [Jenkins](#jenkins)
      - [Deploy Jenkins on K8s](#deploy-jenkins-on-k8s)
      - [Manually configure Jenkins](#manually-configure-jenkins)
      - [Connect Jenkins with GKE](#connect-jenkins-with-gke)
  - [MLflow](#mlflow)
  - [Model training](#model-training)
  - [Deploy Model Inference Service to K8s with KServe](#deploy-model-inference-service-to-k8s-with-kserve)
    - [Install cosign](#install-cosign)
    - [Install required CRDs](#install-required-crds)
    - [Install core components of Knative Serving](#install-core-components-of-knative-serving)
    - [Install Networking Layer with Istio](#install-networking-layer-with-istio)
    - [Install KServe](#install-kserve)
    - [Configure Knative cluster to deploy images from private registry](#configure-knative-cluster-to-deploy-images-from-private-registry)
    - [Push the MLServer Inference Docker to Dockerhub](#push-the-mlserver-inference-docker-to-dockerhub)
    - [Deploy the MLServer](#deploy-the-mlserver)
      - [Create app-secret](#create-app-secret)
      - [Deploy the inferenceservice](#deploy-the-inferenceservice)
      - [Test inference](#test-inference)
- [Delete all resources](#delete-all-resources)
  - [Delete all resources but retaining cluster](#delete-all-resources-but-retaining-cluster)
  - [Delete cluster](#delete-cluster)
- [Set up VPA](#set-up-vpa)
  - [Edit VPA's Updater min-replicas from 2 to 1 so that updater can update resource requests based on recommendation](#edit-vpas-updater-min-replicas-from-2-to-1-so-that-updater-can-update-resource-requests-based-on-recommendation)
- [Archive](#archive)
  - [Troubleshoot](#troubleshoot)
    - [Set admissionWebhook to false to enable two ingress w.r.t. to one hostname and path](#set-admissionwebhook-to-false-to-enable-two-ingress-wrt-to-one-hostname-and-path)


# Prerequisite

- A working GCP project
- Gcloud SDK CLI
  - Make sure you have run `gcloud init` and `gcloud auth application-default login` 
- Terraform CLI
- HuggingFace account to host the HF model
- Dockerhub account to store the custom MLServer Docker Image

> [!CAUTION]
> Following these steps creates a GKE cluster with 4 e2-standard-2 nodes
> Keep this cluster running for a day might cost about 10 - 20 USD

> [!TIP]
> The formatted code block in this README is intended to be pasted in to CLI and run there.
> 
> In between there would be manual steps required.

# Create cluster
> At repo root:
> - `export ROOT_DIR=$(pwd) && echo $ROOT_DIR`
> - Run `export ENV=<ENV>` with the target `$ENV`, for example: `export ENV=dev`
> - `cd $ROOT_DIR/deploy/cloud/gke/terraform`
> - `terraform apply --var="env=$ENV"`

# Install apps in GKE Cluster
```
cd $ROOT_DIR
cp .env.example .env.$ENV
```

> [!NOTE]
> Update your own credentials/values for the "Starter constants" section in the new `.env.$ENV`

## Get GKE cluster credentials

```
cd deploy/cloud/gke
# Init the env vars by exporting the .env.$ENV file
export $(cat ../../../.env.$ENV | grep -v "^#")
gcloud container clusters get-credentials $APP_NAME --zone $GCP_ZONE --project $GCP_PROJECT_NAME
kubectl config use-context gke_${GCP_PROJECT_NAME}_${GCP_ZONE}_${APP_NAME}
```

---

## Set up Traffic Exposure via Ingress Nginx

### Cert Manager to add TLS
Ref: Install with Helm: https://cert-manager.io/docs/installation/helm/
```
helm repo add jetstack https://charts.jetstack.io --force-update
helm repo update 
helm upgrade --install \
  cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --version v1.15.0 \
  --set crds.enabled=true
kubectl wait --namespace cert-manager --for=condition=ready --all pod --timeout=300s
```

### Install NGINX controller
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
```

#### Set up Cloud Endpoints to map a FQDN with our static IP
```
cp openapi.example.yaml openapi.$ENV.yaml
sed -i 's/target: ".*"/target: "'"$IP_ADDRESS"'"/g' openapi.$ENV.yaml

# ---
# Replace the placeholders in openapi.$ENV.yaml

## Find all placeholders in the format <PLACEHOLDER>
placeholders=$(grep -o "<[^>]*>" "openapi.$ENV.yaml" | sort | uniq)

## Iterate over each placeholder
echo "$placeholders" | while read -r placeholder; 
do
  # Remove the enclosing <>
  var_name="${placeholder:1:-1}"
  
  # Get the value of the environment variable
  var_value=$(eval echo \$$var_name)
  
  # Escape special characters in the variable value
  escaped_value=$(echo "$var_value" | sed 's/[\/&]/\\&/g')

  # Substitute the placeholder with the variable value
  sed -i "s/$placeholder/$escaped_value/g" "openapi.$ENV.yaml"
done

# ---
```

```
gcloud endpoints services deploy openapi.$ENV.yaml
```

### Install our custom Ingress
```
# Create in advance the `monitoring` and `cicd` namespaces so that the ingress.yaml runs without complaining
kubectl create namespace monitoring
kubectl create namespace cicd
helm upgrade --install \
  -n default \
  --set env=$ENV \
  --set gcpProjectName=$GCP_PROJECT_NAME \
  --set emailForCertIssuer=$USER_EMAIL \
  main-ingress \
  ./ingress \
  -f ingress/values.yaml
kubectl wait --for=condition=ready pod --all --timeout=30s
```

#### Check TLS applies OK
```
kubectl wait --for=condition=ready cert --all --timeout=300s
export BASE_URL=$ENV-$APP_NAME.endpoints.$GCP_PROJECT_NAME.cloud.goog
sed -i "s/^BASE_URL=.*/BASE_URL=$BASE_URL/" ../../../.env.$ENV
# Check if the output contains "SSL certificate verify ok"
URL=https://$BASE_URL
ssl_check=$(curl -s -I -v --stderr - "$URL" 2>&1)
if echo "$ssl_check" | grep -q "SSL certificate verify ok"; then
    echo "The TLS certificate for $URL is valid."
else
    echo "The TLS certificate for $URL is not valid or could not be verified."
fi
```

---

## Observability

### Prometheus and Grafana
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
  -f ../../services/grafana/values.yaml \
  --set 'grafana\.ini'.server.root_url=https://$ENV-$APP_NAME.endpoints.$GCP_PROJECT_NAME.cloud.goog/grafana \
  --namespace monitoring
export GRAFANA_ADMIN_PASSWORD=$(kubectl get secret --namespace monitoring grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo)
sed -i "s/^GRAFANA_ADMIN_PASSWORD=.*/GRAFANA_ADMIN_PASSWORD=$GRAFANA_ADMIN_PASSWORD/" ../../../.env.$ENV
kubectl wait -n monitoring --selector='!job-name' --for=condition=ready --all po --timeout=300s
echo "Access Grafana at: https://$ENV-$APP_NAME.endpoints.$GCP_PROJECT_NAME.cloud.goog/grafana with admin/$GRAFANA_ADMIN_PASSWORD"
```

> [!NOTE]
> Connecting Grafana with Prometheus Data Source via this URL: `http://prometheus-server.monitoring.svc.cluster.local:80`
> 
> Starter Grafana Dashboard: K8s Resource Monitoring: id=`17375` and id=`315`

### Jaeger
```
helm upgrade --install jaeger oci://registry-1.docker.io/bitnamicharts/jaeger -n monitoring -f ../../services/jaeger/values.yaml
kubectl wait -n monitoring --selector='!job-name' --for=condition=ready --all po --timeout=300s
```

> [!NOTE]
> You can connect Grafana to Jaeger by using the URL: `http://jaeger-query.monitoring.svc.cluster.local:16686/jaeger`. Notice the endpoint `/jaeger` added to the end of the URL
> 
> Ref: https://stackoverflow.com/a/72904828

> [!WARNING]
> When deleting Jaeger with `helm delete`, make sure you delete the PVC `data-jaeger-cassandra-0` as well otherwise when restarting we might run into password incorrect error.

---

## CI/CD

### Jenkins
#### Deploy Jenkins on K8s
```
helm repo add jenkins https://charts.jenkins.io
helm repo update
helm install jenkins jenkins/jenkins --namespace cicd --create-namespace \
  --set controller.jenkinsUrl=https://$ENV-$APP_NAME.endpoints.$GCP_PROJECT_NAME.cloud.goog/jenkins \
  --set controller.jenkinsUriPrefix=/jenkins
kubectl wait -n cicd --for=condition=ready --all po --timeout=300s
export JENKINS_ADMIN_PASSWORD=$(kubectl exec --namespace cicd -it svc/jenkins -c jenkins -- /bin/cat /run/secrets/additional/chart-admin-password && echo)
sed -i "s/^JENKINS_ADMIN_PASSWORD=.*/JENKINS_ADMIN_PASSWORD=$JENKINS_ADMIN_PASSWORD/" ../../../.env.$ENV
echo "Try access Jenkins UI at: https://$ENV-$APP_NAME.endpoints.$GCP_PROJECT_NAME.cloud.goog/jenkins with admin/$JENKINS_ADMIN_PASSWORD"
```

#### Manually configure Jenkins

Install the following Jenkins plugins:
- Kubernetes CLI
- Github
- Github Branch Source

Set up Github Webhooks:
- Go to Github repo > Settings > Webhooks
  - Payload URL: https://dev-reviews-parsing-mlsys.endpoints.cold-embrace-240710.cloud.goog/jenkins/github-webhook/ (notice the trailing `/`)
  - Content type: application/json

Create Github Access Token:
- Go to Github > Settings (Personal) > Developer settings
- Create Personal access tokens (classic)
- Manually select all permissions
- Save the token

Set up Jenkins Pipeline:
- Create new Multibranch Pipeline item in Jenkins
- Branch Sources: Github
  - Username: Github username
  - Password: use the above Github Access Token
- If want to trigger build only on certain branches, add a new "Filter by name: `^main$`", else select "All branches"

Go to Manage Jenkins > Settings > Github API usage > Choose Never check rate limit

#### Connect Jenkins with GKE

Get a secret token from inside K8s cluster to later bind it to a Jenkins credentials
```
cd ../../services/jenkins/k8s-auth/manual
kubectl apply -f jenkins-service-account.yaml
kubectl apply -f jenkins-clusterrolebinding.yaml
kubectl apply -f jenkins-token-secret.yaml

echo "Waiting for secret jenkins-robot-token to appear..."

# Loop until the secret exists
until kubectl get secret jenkins-robot-token > /dev/null 2>&1; do
  echo "Waiting for secret jenkins-robot-token..."
  sleep 1  # Wait for 1 second before checking again
done

echo "Secret jenkins-robot-token has appeared."

export JENKINS_ROBOT_TOKEN=$(kubectl get secret jenkins-robot-token -o jsonpath='{.data.token}' | base64 --decode) && echo "JENKINS_ROBOT_TOKEN: $JENKINS_ROBOT_TOKEN"
export CLUSTER_API_SERVER_URL=$(kubectl cluster-info | grep "Kubernetes control plane" | grep -oP 'https?://\S+') && echo "CLUSTER_API_SERVER_URL: $CLUSTER_API_SERVER_URL"
cd $ROOT_DIR/deploy/cloud/gke
```

> [!NOTE]
> Go to Manage Jenkins > Credentials > System > Global credentials (unrestricted)
> - Add the value of `JENKINS_ROBOT_TOKEN` variable to Jenkins Credentials > Secret text with id credential ID: `rpmls-jenkins-robot-token`
> - Add the value of `CLUSTER_API_SERVER_URL` variable to Jenkins Credentials > Secret text with id credential ID: `gke-cluster-api-server-url`

---

## MLflow
```
# Install with Helm
helm upgrade --install mlflow oci://registry-1.docker.io/bitnamicharts/mlflow -f ../../services/mlflow/values.yaml
kubectl wait --selector='!job-name' --for=condition=ready --all po --timeout=300s
export MLFLOW_TRACKING_USERNAME=$(kubectl get secret --namespace default mlflow-tracking -o jsonpath="{ .data.admin-user }" | base64 -d)
sed -i "s/^MLFLOW_TRACKING_USERNAME=.*/MLFLOW_TRACKING_USERNAME=$MLFLOW_TRACKING_USERNAME/" ../../../.env.$ENV
export MLFLOW_TRACKING_PASSWORD=$(kubectl get secret --namespace default mlflow-tracking -o jsonpath="{.data.admin-password }" | base64 -d)
sed -i "s/^MLFLOW_TRACKING_PASSWORD=.*/MLFLOW_TRACKING_PASSWORD=$MLFLOW_TRACKING_PASSWORD/" ../../../.env.$ENV
export MLFLOW_TRACKING_URI=https://$ENV-$APP_NAME.endpoints.$GCP_PROJECT_NAME.cloud.goog/mlflow
sed -i "s#^MLFLOW_TRACKING_URI=.*#MLFLOW_TRACKING_URI=$MLFLOW_TRACKING_URI#" ../../../.env.$ENV
echo "Try access MLflow UI at: $MLFLOW_TRACKING_URI with $MLFLOW_TRACKING_USERNAME/$MLFLOW_TRACKING_PASSWORD"
# Disable VPA after finding that VPA update can make MLflow Tracking Server to stop working
# Apply VPA
# kubectl apply -f ../../services/mlflow/vpa.yaml
```

---

## Model training

The next section works by assuming that we already have a trained model named `reviews-parsing-ner-aspects@champion`.

> [!NOTE]
> To create this model: 
> - Run the notebooks/train.ipynb notebook
> - Register the model with name `reviews-parsing-ner-aspects` and create the alias `champion` for the newly trained version on MLflow

---

## Deploy Model Inference Service to K8s with KServe

Ref:
- https://knative.dev/docs/install/yaml-install/serving/install-serving-with-yaml/#prerequisites

### Install cosign
```
# Ref: https://docs.sigstore.dev/system_config/installation/
LATEST_VERSION=$(curl https://api.github.com/repos/sigstore/cosign/releases/latest | grep tag_name | cut -d : -f2 | tr -d "v\", ")
curl -O -L "https://github.com/sigstore/cosign/releases/latest/download/cosign_${LATEST_VERSION}_amd64.deb"
sudo dpkg -i cosign_${LATEST_VERSION}_amd64.deb
rm -rf cosign_${LATEST_VERSION}_amd64.deb
```

### Install required CRDs
```
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.14.1/serving-crds.yaml
```

### Install core components of Knative Serving
```
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.14.1/serving-core.yaml
kubectl wait -n knative-serving --for=condition=ready --all po --timeout=300s
```

### Install Networking Layer with Istio
```
kubectl apply -l knative.dev/crd-install=true -f https://github.com/knative/net-istio/releases/download/knative-v1.14.1/istio.yaml
# Do not apply the raw version of istio.yaml because of high resource request
# kubectl apply -f https://github.com/knative/net-istio/releases/download/knative-v1.14.1/istio.yaml
# Download the istio.yaml file and modify resource request
kubectl apply -f ../../services/istio/istio.yaml
kubectl apply -f https://github.com/knative/net-istio/releases/download/knative-v1.14.1/net-istio.yaml
kubectl wait -n istio-system --for=condition=ready --all po --timeout=300s
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.14.1/serving-default-domain.yaml
kubectl wait -n knative-serving --selector='!job-name' --for=condition=ready --all po --timeout=300s
while true; do
  export ISTIO_IP=$(kubectl --namespace istio-system get service istio-ingressgateway -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
  if [ -n "$ISTIO_IP" ]; then
    echo "Istio IP is ready: $ISTIO_IP"
    break
  else
    echo "Istio IP is not ready yet. Waiting..."
    sleep 10
  fi
done
sed -i "s/^ISTIO_IP=.*/ISTIO_IP=$ISTIO_IP/" ../../../.env.$ENV
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

### Install KServe
```
kubectl apply -f https://github.com/kserve/kserve/releases/download/v0.13.0/kserve.yaml
kubectl wait -n kserve --selector='!job-name' --for=condition=ready --all po --timeout=300s
kubectl apply -f https://github.com/kserve/kserve/releases/download/v0.13.0/kserve-cluster-resources.yaml
kubectl wait -n kserve --selector='!job-name' --for=condition=ready --all po --timeout=300s
```

### Configure Knative cluster to deploy images from private registry

> [!IMPORTANT]
> Update the `../../../.env.$ENV` file with your own `PRIVATE_REGISTRY_*` credentials

Ref: https://knative.dev/docs/serving/deploying-from-private-registry/
```
export $(cat ../../../.env.$ENV | grep -v "^#")
kubectl create secret --namespace default docker-registry $REGISTRY_CREDENTIAL_SECRETS \
  --docker-server=$PRIVATE_REGISTRY_URL \
  --docker-email=$PRIVATE_REGISTRY_EMAIL \
  --docker-username=$PRIVATE_REGISTRY_USER \
  --docker-password=$PRIVATE_REGISTRY_PASSWORD
```

### Push the MLServer Inference Docker to Dockerhub
```
cd ../../../models/reviews-parsing-ner-aspects
make build
make push
cd ../../deploy/cloud/gke
```

> [!IMPORTANT]
> Update the model image with tag at `../../services/kserve/inference.yaml`

### Deploy the MLServer

#### Create app-secret
> [!WARNING]
> Be careful to submit `.env` with single quote enclosing values.
> We may need to preprocess them to make the `--from-env-file` work.
```
kubectl create secret generic app-secret --from-env-file=../../../.env.$ENV
```

#### Deploy the inferenceservice
```
kubectl apply -f ../../services/kserve/inference.yaml --namespace default
kubectl wait --for=condition=ready --all revision --timeout=30s
latest_revision=$(kubectl get revisions -l serving.knative.dev/service=reviews-parsing-ner-aspects-mlserver-predictor -o jsonpath='{.items[-1:].metadata.name}')
kubectl wait --for=condition=ready revision $latest_revision --timeout=300s
kubectl wait --selector='!job-name' --for=condition=ready --all po --timeout=300s
echo "Access the KServe Model Swagger docs at: http://reviews-parsing-ner-aspects-mlserver.default.$ISTIO_IP.sslip.io/v2/models/reviews-parsing-ner-aspects/docs"
```

#### Test inference
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
