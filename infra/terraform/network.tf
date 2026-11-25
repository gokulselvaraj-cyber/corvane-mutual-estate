resource "google_compute_network" "corvane" {
  name                    = "corvane-${var.environment}"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "gke_london" {
  name          = "gke-london-${var.environment}"
  region        = var.primary_region
  network       = google_compute_network.corvane.id
  ip_cidr_range = "10.20.0.0/20"

  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = "10.24.0.0/14"
  }
  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = "10.28.0.0/20"
  }
}

resource "google_compute_router_nat" "egress" {
  name                               = "corvane-egress-${var.environment}"
  router                             = google_compute_router.london.name
  region                             = var.primary_region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}

resource "google_compute_router" "london" {
  name    = "corvane-london-${var.environment}"
  region  = var.primary_region
  network = google_compute_network.corvane.id
}
