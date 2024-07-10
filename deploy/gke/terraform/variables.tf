variable "project_id" {
  description = "The project ID to deploy to"
  type        = string
  default     = "cold-embrace-240710"
}

variable "cluster_version" {
  description = "The Kubernetes version for the GKE cluster"
  type        = string
  default     = "1.29.4-gke.1043004"
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
  default     = "e2-medium"
}

variable "hp_node_pool_name" {
  description = "The name of the GKE high-perf node pool"
  type        = string
  default     = "high-perf"
}

variable "hp_node_machine_type" {
  description = "The machine type for the GKE high-perf node pool"
  type        = string
  default     = "e2-standard-4"
}

variable "disk_size" {
  description = "The disk size for the GKE nodes"
  type        = number
  default     = 100
}
