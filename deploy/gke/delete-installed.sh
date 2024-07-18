#!/bin/bash

helm list | awk 'NR>1 {print $1}' | xargs helm delete
kubectl delete --all ing
kubectl delete --all secret
kubectl get cm | grep -v "kube" | awk 'NR>1 {print $1}' | xargs kubectl delete cm
kubectl delete --all pvc
kubectl delete --all pv
kubectl delete --all po
kubectl delete --all job
kubectl delete ns cert-manager
kubectl delete ns monitoring