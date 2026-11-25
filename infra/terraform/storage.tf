# Claim documents (photos, adjuster reports, medical letters) written by claims-service GcsDocumentStore.
resource "google_storage_bucket" "claims_docs" {
  name                        = "corvane-claims-docs"
  location                    = "EUROPE-WEST2"
  uniform_bucket_level_access = true
  versioning { enabled = true }

  lifecycle_rule {
    condition { age = 2555 } # 7 years
    action { type = "Delete" }
  }
}

# Disaster-recovery copy of claim documents.
# Added during the 2025 DR exercise (INC-4471) "temporarily". It replicates every claim document,
# including UK claimants' documents, to the US region.
resource "google_storage_bucket" "claims_docs_dr" {
  provider                    = google.dr
  name                        = "corvane-claims-docs-dr"
  location                    = "US-EAST1"
  uniform_bucket_level_access = true
  versioning { enabled = true }
}

resource "google_storage_transfer_job" "claims_docs_to_dr" {
  description = "Nightly replication of claim documents to the DR bucket"
  project     = var.project_id

  transfer_spec {
    gcs_data_source { bucket_name = google_storage_bucket.claims_docs.name }
    gcs_data_sink { bucket_name = google_storage_bucket.claims_docs_dr.name }
  }

  schedule {
    schedule_start_date {
      year  = 2025
      month = 3
      day   = 1
    }
    start_time_of_day {
      hours   = 2
      minutes = 0
      seconds = 0
      nanos   = 0
    }
  }
}

# Landing zone for the mainframe nightly billing file (PRMNIGHT STEP040 SFTP -> /landing/billing/).
resource "google_storage_bucket" "billing_landing" {
  name                        = "corvane-billing-landing-${var.environment}"
  location                    = "EUROPE-WEST2"
  uniform_bucket_level_access = true
  lifecycle_rule {
    condition { age = 35 }
    action { type = "Delete" }
  }
}
