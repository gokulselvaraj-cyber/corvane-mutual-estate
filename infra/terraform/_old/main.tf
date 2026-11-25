# RETIRED 2024-03: replaced by ../gke.tf and ../databases.tf
resource "google_compute_instance" "claims_v1" {
  name         = "corvane-claims-v1"
  machine_type = "n1-standard-4"
  zone         = "europe-west2-a"

  boot_disk {
    initialize_params { image = "debian-cloud/debian-11" }
  }

  network_interface {
    network = "default"
    access_config {}
  }

  metadata_startup_script = "systemctl start tomcat9"
}
