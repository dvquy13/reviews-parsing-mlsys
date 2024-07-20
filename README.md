# Reviews Parsing MLSys

This project focuses on applying engineering practices to build a Machine Learning System in the domain of public reviews data.

# High-level architecture

![Architecture Diagram](static/RPMLS%20Architecture%20v1.drawio.svg)

[View in full screen](https://bit.ly/rpmls-architecture)

# Repo structure
```
├── deploy: Scripts to create the deployment resources
│   ├── gke: Deploy on Google Cloud Kubernetes Engine (GKE)
│   │   ├── ingress: Helm chart for our main custom Ingress resources specifying service endpoints
│   │   │   ├── templates
│   │   │   │   ├── cert-issuer.yaml: define TLS certificates for each namespace
│   │   │   │   ├── _helpers.tpl
│   │   │   │   └── ingress.yaml: define the Nginx Ingress rules to services in all namespaces
│   │   │   ├── Chart.yaml
│   │   │   └── values.yaml
│   │   ├── terraform: Manage the creation and deletion of GCP resources
│   │   │   ├── main.tf
│   │   │   ├── outputs.tf
│   │   │   ├── provider.tf
│   │   │   ├── README.md
│   │   │   ├── terraform.tfstate
│   │   │   ├── terraform.tfstate.backup
│   │   │   └── variables.tf
│   │   ├── openapi.dev.yaml: (gitignored) Contains the actual values for the GCP Endpoints config which defines the main FQDN for our application
│   │   ├── openapi.example.yaml: placeholder for the actual file
│   │   ├── README.md
│   ├── kind: (WIP) Deploy on local Kind cluster
│   └── services: Defines customized configs for the services installed in the K8s cluster
│       ├── grafana
│       ├── istio
│       │   └── istio.yaml: Customize resource request for istiod and istio-ingressgateway to fit the testing cluster
│       ├── jaeger
│       ├── jenkins
│       │   ├── k8s-auth: Define the credentials needed to provide to jenkins so that it is able to authenticate itself with the target GKE cluster
│       │   └── values.yaml
│       ├── kserve
│       │   └── inference.yaml
│       └── mlflow
│           ├── values.yaml
│           └── vpa.yaml: (Deprecated) VPA was experimentally applied to MLflow to auto adjust resource request but causing troubles so temporarily removed
├── models: Define MLServer models and its serving dependencies
│   └── reviews-parsing-ner-aspects
├── notebooks
├── scripts: Utility scripts
├── Jenkinsfile
├── poetry.lock: Poetry's internal file to manage the main Python dependencies
├── pyproject.toml: Poetry main file where we can register the desired Python libraries
└── README.md
```

# Set up

## Python

Install these prerequisites:
- Virtual environment with Python 3.9. You can choose to install Miniconda to choose which Python version to create a new virtual env with.
- Poetry >= 1.8.3. Make sure Poetry use the correct Python executable from the above venv by running `poetry env info`.

### Install packages

```
# Create a new Python 3.9 environment
# Example conda environment at current dir
conda create --prefix ./.venv python=3.9
poetry env use ./.venv/bin/python

# This command will automatically install all packages specified in `poetry.lock` file.
poetry install
```

## Set up GKE
Follow instructions at [deploy/gke](deploy/gke/README.md)

# Deploy new KServe model
## Alias the champion model with new version
```
poetry run python scripts/alias_new_mlflow_model_as_champion.py --run_id=<RUN_ID> --model_name=reviews-parsing-ner-aspects
```

## Restart KServe Inference Service and update latest model
```
kubectl annotate -n default inferenceservice reviews-parsing-ner-aspects-mlserver deploy_timestamp=$(date -u +'%Y-%m-%dT%H:%M:%SZ') --overwrite
```

---
To get an idea about the output of this repo, check out this [demo video on Youtube](https://www.youtube.com/watch?v=O-8_Q1GgJpM).
