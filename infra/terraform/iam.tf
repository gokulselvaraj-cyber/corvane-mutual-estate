resource "google_service_account" "workload" {
  for_each     = toset(["policy-admin", "claims-service", "fraud-scoring", "payments-gateway", "notifications", "broker-commissions", "warehouse-loader"])
  account_id   = "${each.key}-${var.environment}"
  display_name = "Workload identity for ${each.key}"
}

resource "google_storage_bucket_iam_member" "claims_docs_writer" {
  bucket = google_storage_bucket.claims_docs.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.workload["claims-service"].email}"
}

resource "google_storage_bucket_iam_member" "landing_reader" {
  bucket = google_storage_bucket.billing_landing.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.workload["warehouse-loader"].email}"
}

resource "google_secret_manager_secret" "clearriver_api_key" {
  secret_id = "clearriver-api-key-${var.environment}"
  replication {
    user_managed {
      replicas { location = "europe-west2" }
    }
  }
}
