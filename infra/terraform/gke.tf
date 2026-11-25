resource "google_container_cluster" "platform" {
  name                     = "corvane-platform-${var.environment}"
  location                 = var.primary_region
  network                  = google_compute_network.corvane.id
  subnetwork               = google_compute_subnetwork.gke_london.id
  remove_default_node_pool = true
  initial_node_count       = 1

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  release_channel {
    channel = "REGULAR"
  }
}

resource "google_container_node_pool" "general" {
  name       = "general"
  cluster    = google_container_cluster.platform.id
  node_count = var.gke_node_count

  node_config {
    machine_type = "e2-standard-4"
    oauth_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    labels       = { team = "platform" }
  }

  autoscaling {
    min_node_count = var.gke_node_count
    max_node_count = var.gke_node_count * 3
  }
}
