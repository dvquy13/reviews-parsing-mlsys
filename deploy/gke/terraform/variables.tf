variable "app_name" {
  description = "The main name of the application"
  type        = string
  default     = "reviews-parsing-mlsys"
}

variable "project_id" {
  description = "The project ID to deploy to"
  type        = string
  default     = "cold-embrace-240710"
}

variable "cluster_version" {
  description = "The Kubernetes version for the GKE cluster"
  type        = string
  default     = "1.29.6-gke.1038001"
}

variable "region" {
  description = "The region to deploy to"
  type        = string
  default     = "asia-southeast1"
}

variable "zone" {
  description = "The zone to deploy to"
  type        = string
  default     = "asia-southeast1-a"
}

variable "cluster_name" {
  description = "The name of the GKE cluster"
  type        = string
  default     = "reviews-parsing-mlsys"
}

variable "default_node_pool_name" {
  description = "The name of the GKE default node pool"
  type        = string
  default     = "default"
}

variable "default_node_machine_type" {
  description = "The machine type for the GKE default node pool"
  type        = string
  default     = "e2-standard-2"
  # Use e2-standard-2 here to maximize free trial quota (since e2-medium only request 50% of 2 vCPUS if I'm correct)
  # default     = "e2-medium"
}

variable "hp_node_pool_name" {
  description = "The name of the GKE high-perf node pool"
  type        = string
  default     = "high-perf"
}

variable "hp_node_machine_type" {
  description = "The machine type for the GKE high-perf node pool"
  type        = string
  default     = "e2-standard-2"
}

variable "disk_type" {
  description = "The disk type for the GKE nodes"
  type        = string
  default     = "pd-standard"
}

variable "disk_size" {
  description = "The disk size for the GKE nodes"
  type        = number
  # Reduce from 100 to 70 due to suddenly got this error: `Quota 'SSD_TOTAL_GB' exceeded. Limit: 250.0 in region`
  default = 70
}

variable "env" {
  description = "The environment (e.g. dev, staging, prod)"
  type        = string
  default     = ""
}
