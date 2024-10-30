output "cluster_name" {
  value = google_container_cluster.primary.name
}

output "endpoint" {
  value = google_container_cluster.primary.endpoint
}

output "main_ingress_static_ip_address" {
  value = google_compute_address.main_ingress_static_ip.address
}
