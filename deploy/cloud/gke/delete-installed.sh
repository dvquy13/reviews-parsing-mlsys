#!/bin/bash

helm list | awk 'NR>1 {print $1}' | xargs helm delete

resources=("ing" "secret" "cm" "pvc" "pv" "po" "job")

for resource in "${resources[@]}"; do
  if [ "$resource" == "cm" ]; then
    kubectl get cm | grep -v "kube" | awk 'NR>1 {print $1}' | xargs kubectl delete cm
  else
    kubectl delete --all "$resource"
  fi
done

kubectl delete ns cert-manager
kubectl delete ns monitoring