resource "google_container_cluster" "primary" {
  name                = var.cluster_name
  location            = var.zone
  initial_node_count  = 1
  deletion_protection = false

  min_master_version       = var.cluster_version
  remove_default_node_pool = true

  network    = "projects/${var.project_id}/global/networks/default"
  subnetwork = "projects/${var.project_id}/regions/${var.region}/subnetworks/default"

  release_channel {
    channel = "REGULAR"
  }

  addons_config {
    http_load_balancing {
      disabled = false
    }
    horizontal_pod_autoscaling {
      disabled = false
    }
  }

  logging_service       = "logging.googleapis.com/kubernetes"
  monitoring_service    = "monitoring.googleapis.com/kubernetes"
  enable_shielded_nodes = true

  cluster_autoscaling {
    autoscaling_profile = "OPTIMIZE_UTILIZATION"
  }
}

resource "google_container_node_pool" "default" {
  cluster    = google_container_cluster.primary.name
  location   = google_container_cluster.primary.location
  name       = var.default_node_pool_name
  node_count = 1

  autoscaling {
    min_node_count = 1
    max_node_count = 3
  }

  management {
    auto_upgrade = true
    auto_repair  = true
  }

  node_config {
    machine_type = var.default_node_machine_type
    disk_size_gb = var.disk_size
    disk_type    = var.disk_type
    image_type   = "COS_CONTAINERD"
    preemptible  = true

    oauth_scopes = [
      "https://www.googleapis.com/auth/devstorage.read_only",
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring",
      "https://www.googleapis.com/auth/servicecontrol",
      "https://www.googleapis.com/auth/service.management.readonly",
      "https://www.googleapis.com/auth/trace.append"
    ]

    metadata = {
      disable-legacy-endpoints = "true"
    }

    shielded_instance_config {
      enable_integrity_monitoring = true
      enable_secure_boot          = true
    }
  }
}

resource "google_container_node_pool" "high_perf" {
  cluster    = google_container_cluster.primary.name
  location   = google_container_cluster.primary.location
  name       = var.hp_node_pool_name
  node_count = 0

  autoscaling {
    min_node_count = 0
    max_node_count = 2
  }

  management {
    auto_upgrade = true
    auto_repair  = true
  }

  node_config {
    machine_type = var.hp_node_machine_type
    disk_type    = var.disk_type
    disk_size_gb = var.disk_size
    image_type   = "COS_CONTAINERD"
    preemptible  = true

    oauth_scopes = [
      "https://www.googleapis.com/auth/devstorage.read_only",
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring",
      "https://www.googleapis.com/auth/servicecontrol",
      "https://www.googleapis.com/auth/service.management.readonly",
      "https://www.googleapis.com/auth/trace.append"
    ]

    metadata = {
      disable-legacy-endpoints = "true"
    }

    shielded_instance_config {
      enable_integrity_monitoring = true
      enable_secure_boot          = true
    }
  }
}

resource "google_compute_address" "main_ingress_static_ip" {
  name   = "${var.env}-${var.app_name}"
  region = var.region
}
