# Claims database (PostgreSQL 15). Holds claimant personal data, injury notes and payments.
resource "google_sql_database_instance" "claimsdb" {
  name             = "claimsdb-${var.environment}"
  region           = var.primary_region
  database_version = "POSTGRES_15"

  settings {
    tier              = var.db_tier
    availability_type = var.claims_db_ha ? "REGIONAL" : "ZONAL"

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
      location                       = "europe-west2"
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.corvane.id
    }

    database_flags {
      name  = "log_min_duration_statement"
      value = "500"
    }
  }
  deletion_protection = true
}

resource "google_sql_database" "claims" {
  name     = "claimsdb"
  instance = google_sql_database_instance.claimsdb.name
}

resource "google_sql_user" "claims_app" {
  name     = "claims_app"
  instance = google_sql_database_instance.claimsdb.name
  password = var.claims_db_password
}

variable "claims_db_password" {
  type      = string
  sensitive = true
  # Supplied by the pipeline from Secret Manager (TF_VAR_claims_db_password); never committed.
}
