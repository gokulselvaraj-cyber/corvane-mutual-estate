variable "project_id" {
  type        = string
  description = "GCP project for this environment"
}

variable "environment" {
  type        = string
  description = "dev, test or prod"
}

variable "primary_region" {
  type        = string
  default     = "europe-west2"
  description = "London. ADR-0007: UK customer data must stay in this region."
}

variable "dr_region" {
  type        = string
  default     = "us-east1"
  description = "Disaster-recovery region for US business and shared tooling."
}

variable "gke_node_count" {
  type    = number
  default = 3
}

variable "db_tier" {
  type    = string
  default = "db-custom-2-7680"
}

variable "claims_db_ha" {
  type    = bool
  default = false
}
