"""Builder E: writes infra/ (terraform, k8s, helm, ansible, observability) and docker-compose.yml.
Run: python3 -I e_infra.py <estate_root>"""
import os, sys

ROOT = sys.argv[1]


def W(path, text):
    p = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(text.lstrip("\n"))


# name, image, port, team, replicas (prod), cpu, mem, needs_db, kind
SERVICES = [
    ("policy-admin", "policy-admin", 8080, "policy-core", 3, "500m", "1Gi", "oracle"),
    ("claims-service", "claims-service", 8080, "claims-platform", 3, "500m", "1Gi", "postgres"),
    ("fraud-scoring", "fraud-scoring", 8080, "fraud-analytics", 3, "1", "2Gi", None),
    ("payments-gateway", "payments-gateway", 8080, "payments", 1, "250m", "256Mi", "postgres"),
    ("notifications", "notifications", 8080, "digital", 3, "250m", "512Mi", None),
    ("broker-commissions", "broker-commissions", 8080, "distribution", 3, "250m", "512Mi", "sqlserver"),
    ("warehouse-loader", "warehouse-loader", 8080, "data-platform", 3, "500m", "1Gi", "postgres"),
    ("customer-portal", "customer-portal", 8080, "digital", 3, "100m", "128Mi", None),
]

# ---------------------------------------------------------------- Terraform
T = "infra/terraform/"
W(T + "versions.tf", """
terraform {
  required_version = ">= 1.7.0"
  required_providers {
    google = { source = "hashicorp/google", version = "~> 5.40" }
  }
  backend "gcs" {
    bucket = "corvane-tfstate"
    prefix = "platform"
  }
}

provider "google" {
  project = var.project_id
  region  = var.primary_region
}

provider "google" {
  alias   = "dr"
  project = var.project_id
  region  = var.dr_region
}
""")

W(T + "variables.tf", """
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
""")

W(T + "network.tf", """
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
""")

W(T + "gke.tf", """
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
""")

W(T + "databases.tf", """
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
""")

W(T + "storage.tf", """
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
""")

W(T + "kafka.tf", """
# Kafka runs on Confluent Cloud; topics are declared here through the Confluent provider module.
module "kafka_topics" {
  source      = "./modules/kafka-topics"
  environment = var.environment
  topics = {
    "policies.bound.v1"    = { partitions = 6, retention_hours = 168 }
    "claims.registered.v1" = { partitions = 12, retention_hours = 168 }
    "claims.approved.v1"   = { partitions = 6, retention_hours = 336 }
    "payments.settled.v1"  = { partitions = 6, retention_hours = 336 }
    "claims.closed.v1"     = { partitions = 6, retention_hours = 168 }
    "claims.reopened.v1"   = { partitions = 3, retention_hours = 168 }
  }
}
""")

W(T + "modules/kafka-topics/main.tf", """
variable "environment" {
  type = string
}

variable "topics" {
  type = map(object({ partitions = number, retention_hours = number }))
}

resource "confluent_kafka_topic" "this" {
  for_each         = var.topics
  topic_name       = each.key
  partitions_count = each.value.partitions
  config = {
    "retention.ms"   = tostring(each.value.retention_hours * 3600000)
    "cleanup.policy" = "delete"
  }
}
""")

W(T + "iam.tf", """
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
""")

for env, nodes, ha in (("dev", 1, "false"), ("test", 2, "false"), ("prod", 4, "true")):
    W(T + f"env/{env}.tfvars", f"""
project_id     = "corvane-platform-{env}"
environment    = "{env}"
gke_node_count = {nodes}
claims_db_ha   = {ha}
db_tier        = "{'db-custom-4-15360' if env == 'prod' else 'db-custom-2-7680'}"
""")

W(T + "_old/README.md", """
# _old (do not apply)

The 2023 Terraform layout from before the move to one root module per environment. Kept for reference during the
migration and never applied since March 2024. It still points at the retired `corvane-claims-v1` VM.
""")
W(T + "_old/main.tf", """
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
""")

# ---------------------------------------------------------------- Kubernetes
K = "infra/k8s/"
for name, image, port, team, _r, cpu, mem, db in SERVICES:
    env_lines = ["        - name: SPRING_PROFILES_ACTIVE\n          valueFrom: {configMapKeyRef: {name: corvane-env, key: profile}}"]
    if db:
        env_lines.append(f"        - name: DB_PASSWORD\n          valueFrom: {{secretKeyRef: {{name: {name}-db, key: password}}}}")
    if name == "claims-service":
        env_lines.append("        - name: POLICY_ADMIN_URL\n          value: http://policy-admin:8080\n"
                         "        - name: FRAUD_SCORING_URL\n          value: http://fraud-scoring:8080")
    W(K + f"base/{name}.yaml", f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
  labels: {{app: {name}, team: {team}}}
spec:
  replicas: 3
  selector:
    matchLabels: {{app: {name}}}
  template:
    metadata:
      labels: {{app: {name}, team: {team}}}
    spec:
      serviceAccountName: {name}
      containers:
      - name: {name}
        image: europe-west2-docker.pkg.dev/corvane-platform/apps/{image}:${{IMAGE_TAG}}
        ports:
        - containerPort: {port}
        env:
{chr(10).join(env_lines)}
        resources:
          requests: {{cpu: "{cpu}", memory: "{mem}"}}
          limits: {{memory: "{mem}"}}
        readinessProbe:
          httpGet: {{path: {'/actuator/health/readiness' if name in ('policy-admin', 'claims-service') else '/healthz'}, port: {port}}}
          periodSeconds: 10
        livenessProbe:
          httpGet: {{path: {'/actuator/health/liveness' if name in ('policy-admin', 'claims-service') else '/healthz'}, port: {port}}}
          initialDelaySeconds: 30
---
apiVersion: v1
kind: Service
metadata:
  name: {name}
spec:
  selector: {{app: {name}}}
  ports:
  - port: {port}
    targetPort: {port}
""")

W(K + "base/hpa.yaml", """
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: claims-service
spec:
  scaleTargetRef: {apiVersion: apps/v1, kind: Deployment, name: claims-service}
  minReplicas: 3
  maxReplicas: 12
  metrics:
  - type: Resource
    resource: {name: cpu, target: {type: Utilization, averageUtilization: 70}}
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fraud-scoring
spec:
  scaleTargetRef: {apiVersion: apps/v1, kind: Deployment, name: fraud-scoring}
  minReplicas: 3
  maxReplicas: 8
  metrics:
  - type: Resource
    resource: {name: cpu, target: {type: Utilization, averageUtilization: 65}}
""")

W(K + "base/kustomization.yaml", "resources:\n" + "".join(f"- {s[0]}.yaml\n" for s in SERVICES) + "- hpa.yaml\n")

for env in ("dev", "test", "prod"):
    W(K + f"overlays/{env}/kustomization.yaml", f"""
namespace: corvane-{env}
resources:
- ../../base
- env-config.yaml
patches:
- path: replicas.yaml
- path: claims-service.yaml
- path: notifications.yaml
""")
    W(K + f"overlays/{env}/env-config.yaml", f"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: corvane-env
data:
  profile: {env}
  kafka.bootstrap: {'kafka-' + env + '.corvane.internal:9092' if env != 'prod' else 'pkc-corvane-prod.europe-west2.gcp.confluent.cloud:9092'}
  fraud.llm-triage.enabled: "{'true' if env != 'dev' else 'false'}"
  policy.premium-engine: {'mainframe' if env == 'prod' else 'java'}
""")
    reps = {"dev": 1, "test": 2, "prod": None}[env]
    body = []
    for s in SERVICES:
        r = reps if reps else s[4]
        body.append(f"apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: {s[0]}\nspec:\n  replicas: {r}\n")
    W(K + f"overlays/{env}/replicas.yaml", "---\n".join(body))
    W(K + f"overlays/{env}/notifications.yaml", f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: notifications
spec:
  template:
    spec:
      containers:
      - name: notifications
        env:
        - name: SMTP_HOST
          value: smtp.corvane.internal
        - name: SMTP_PORT
          value: "587"
        - name: ADMIN_URL
          value: http://notifications:8081
        - name: SMS_PROVIDER_URL
          value: https://sms.textwave.example
""")
    pa_port = 8081 if env == "test" else 8080  # X1: test overlay copy-pasted from notifications ADMIN_URL
    W(K + f"overlays/{env}/claims-service.yaml", f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: claims-service
spec:
  template:
    spec:
      containers:
      - name: claims-service
        env:
        - name: POLICY_ADMIN_URL
          value: http://policy-admin:{pa_port}
        - name: FRAUD_SCORING_URL
          value: http://fraud-scoring:8080
        - name: CLAIMS_TRIAGE_AUTO_APPROVE_LIMIT
          value: "{5000 if env == 'prod' else 2500}"
""")

# ---------------------------------------------------------------- Helm
H = "infra/helm/corvane-platform/"
W(H + "Chart.yaml", """
apiVersion: v2
name: corvane-platform
description: Umbrella chart for the Corvane insurance platform services
type: application
version: 4.2.0
appVersion: "2026.11"
""")
W(H + "values.yaml", "global:\n  imageRegistry: europe-west2-docker.pkg.dev/corvane-platform/apps\n  imageTag: latest\n  region: europe-west2\n\nservices:\n" + "".join(
    f"  {s[0]}:\n    replicas: 2\n    port: {s[2]}\n    resources: {{cpu: \"{s[5]}\", memory: \"{s[6]}\"}}\n" for s in SERVICES))
W(H + "values-prod.yaml", "global:\n  imageTag: \"2026.11.3\"\n\nservices:\n" + "".join(
    f"  {s[0]}:\n    replicas: {s[4]}\n" for s in SERVICES))
W(H + "templates/deployment.yaml", """
{{- range $name, $svc := .Values.services }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ $name }}
  labels:
    app: {{ $name }}
    chart: {{ $.Chart.Name }}-{{ $.Chart.Version }}
spec:
  replicas: {{ $svc.replicas }}
  selector:
    matchLabels:
      app: {{ $name }}
  template:
    metadata:
      labels:
        app: {{ $name }}
    spec:
      containers:
        - name: {{ $name }}
          image: "{{ $.Values.global.imageRegistry }}/{{ $name }}:{{ $.Values.global.imageTag }}"
          ports:
            - containerPort: {{ $svc.port }}
          resources:
            requests:
              cpu: {{ $svc.resources.cpu | quote }}
              memory: {{ $svc.resources.memory | quote }}
---
{{- end }}
""")
W(H + "templates/service.yaml", """
{{- range $name, $svc := .Values.services }}
apiVersion: v1
kind: Service
metadata:
  name: {{ $name }}
spec:
  selector:
    app: {{ $name }}
  ports:
    - port: {{ $svc.port }}
      targetPort: {{ $svc.port }}
---
{{- end }}
""")

# ---------------------------------------------------------------- Ansible (SFTP / landing host for the mainframe file)
A = "infra/ansible/"
W(A + "site.yml", """
# Configures the billing landing host that receives the mainframe nightly file (PRMNIGHT STEP040)
# and the Airflow worker that runs the premium_billing_load DAG.
- import_playbook: playbooks/landing-host.yml
- import_playbook: playbooks/airflow-worker.yml
""")
W(A + "hosts.ini", """
[landing]
landing-01.corvane.internal ansible_host=10.20.4.11

[airflow_workers]
airflow-w1.corvane.internal ansible_host=10.20.4.21
airflow-w2.corvane.internal ansible_host=10.20.4.22

[all:vars]
ansible_user=corvane-ops
""")
W(A + "playbooks/landing-host.yml", """
- name: Billing landing host
  hosts: landing
  become: true
  roles:
    - sftp_landing
""")
W(A + "playbooks/airflow-worker.yml", """
- name: Airflow workers
  hosts: airflow_workers
  become: true
  roles:
    - airflow_worker
""")
W(A + "roles/sftp_landing/tasks/main.yml", """
- name: Create the mainframe transfer user
  ansible.builtin.user:
    name: "{{ mainframe_sftp_user }}"
    shell: /usr/sbin/nologin
    home: /landing

- name: Create the billing landing folder
  ansible.builtin.file:
    path: /landing/billing
    state: directory
    owner: "{{ mainframe_sftp_user }}"
    mode: "0750"

- name: Chroot SFTP for the mainframe user
  ansible.builtin.template:
    src: sshd_landing.conf.j2
    dest: /etc/ssh/sshd_config.d/landing.conf
    mode: "0644"
  notify: restart sshd

- name: Sync landed files to the landing bucket every 5 minutes
  ansible.builtin.cron:
    name: landing-to-gcs
    minute: "*/5"
    job: "gsutil -m rsync /landing/billing gs://{{ landing_bucket }}/billing"
""")
W(A + "roles/sftp_landing/handlers/main.yml", """
- name: restart sshd
  ansible.builtin.service:
    name: ssh
    state: restarted
""")
W(A + "roles/sftp_landing/templates/sshd_landing.conf.j2", """
# Managed by Ansible ({{ ansible_managed }})
Match User {{ mainframe_sftp_user }}
    ChrootDirectory /landing
    ForceCommand internal-sftp -d /billing
    AllowTcpForwarding no
    PasswordAuthentication no
""")
W(A + "roles/airflow_worker/tasks/main.yml", """
- name: Install Airflow worker
  ansible.builtin.pip:
    name: "apache-airflow[celery,google]=={{ airflow_version }}"
    virtualenv: /opt/airflow/venv

- name: Deploy DAGs from the warehouse-loader repo
  ansible.builtin.git:
    repo: "https://git.corvane.internal/data/warehouse-loader.git"
    dest: /opt/airflow/dags/warehouse-loader
    version: main

- name: Airflow worker service
  ansible.builtin.systemd:
    name: airflow-worker
    state: started
    enabled: true
""")
W(A + "group_vars/all.yml", """
mainframe_sftp_user: corvmf
landing_bucket: corvane-billing-landing-prod
airflow_version: "2.9.3"
timezone: Europe/London
""")

# ---------------------------------------------------------------- Observability
O = "infra/observability/"
W(O + "corvane.rules.yml", """
groups:
- name: claims
  rules:
  - alert: ClaimsApiErrorRateHigh
    expr: sum(rate(http_server_requests_seconds_count{app="claims-service",status=~"5.."}[5m])) / sum(rate(http_server_requests_seconds_count{app="claims-service"}[5m])) > 0.02
    for: 10m
    labels: {severity: page, team: claims-platform}
    annotations:
      summary: Claims API 5xx rate above 2%
      runbook: ops/runbooks/claims-api-errors.md
  - alert: FraudScoringSlow
    expr: histogram_quantile(0.95, sum(rate(fraud_score_seconds_bucket[5m])) by (le)) > 3
    for: 15m
    labels: {severity: ticket, team: fraud-analytics}
    annotations:
      summary: Fraud scoring p95 above 3 s (LLM triage latency)
- name: payments
  rules:
  - alert: PayoutFailures
    expr: increase(payouts_failed_total[15m]) > 5
    labels: {severity: page, team: payments}
    annotations:
      summary: ClearRiver payouts failing
      runbook: ops/runbooks/payout-failures.md
  - alert: PaymentsGatewayDown
    expr: up{app="payments-gateway"} == 0
    for: 2m
    labels: {severity: page, team: payments}
    annotations:
      summary: payments-gateway has no healthy pod (prod runs a single replica)
- name: kafka
  rules:
  - alert: ConsumerLagHigh
    expr: max(kafka_consumergroup_lag) by (consumergroup) > 5000
    for: 10m
    labels: {severity: ticket}
    annotations:
      runbook: ops/runbooks/kafka-lag.md
- name: batch
  rules:
  - alert: BillingFileNotLanded
    expr: time() - landing_last_file_timestamp_seconds{folder="billing"} > 4 * 3600
    labels: {severity: page, team: mainframe}
    annotations:
      summary: No billing file from PRMNIGHT in 4 hours
      runbook: ops/runbooks/prmnight-failure.md
  - record: corvane:billing_rows_loaded:1d
    expr: sum(increase(warehouse_rows_loaded_total{table="premium_billing"}[1d]))
""")
W(O + "slo-claims-api.yaml", """
apiVersion: openslo/v1
kind: SLO
metadata:
  name: claims-api-availability
  displayName: Claims API availability
spec:
  service: claims-service
  description: FNOL and claim status calls succeed
  budgetingMethod: Occurrences
  objectives:
  - displayName: 99.5% of requests succeed over 28 days
    target: 0.995
  timeWindow:
  - duration: 28d
    isRolling: true
  indicator:
    metadata: {name: claims-good-requests}
    spec:
      ratioMetric:
        good: {metricSource: {type: Prometheus, spec: {query: 'sum(rate(http_server_requests_seconds_count{app="claims-service",status!~"5.."}[5m]))'}}}
        total: {metricSource: {type: Prometheus, spec: {query: 'sum(rate(http_server_requests_seconds_count{app="claims-service"}[5m]))'}}}
""")

# ---------------------------------------------------------------- docker-compose (local dev)
W("docker-compose.yml", """
# Local development stack. Secrets come from your shell (.env is git-ignored).
services:
  postgres:
    image: postgres:15.8
    environment:
      POSTGRES_DB: claimsdb
      POSTGRES_USER: claims_app
      POSTGRES_PASSWORD: ${CLAIMS_DB_PASSWORD}
    volumes:
      - ./data/postgres:/docker-entrypoint-initdb.d:ro
    ports: ["5432:5432"]
  kafka:
    image: bitnami/kafka:3.7
    environment:
      KAFKA_CFG_NODE_ID: "1"
      KAFKA_CFG_PROCESS_ROLES: broker,controller
      KAFKA_CFG_LISTENERS: PLAINTEXT://:9092,CONTROLLER://:9093
      KAFKA_CFG_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093
      KAFKA_CFG_CONTROLLER_LISTENER_NAMES: CONTROLLER
    ports: ["9092:9092"]
  policy-admin:
    build: ./services/policy-admin
    environment:
      SPRING_PROFILES_ACTIVE: dev
      LEDGER_DB_PASSWORD: ${LEDGER_DB_PASSWORD}
    ports: ["8080:8080"]
  claims-service:
    build: ./services/claims-service
    environment:
      SPRING_PROFILES_ACTIVE: dev
      POLICY_ADMIN_URL: http://policy-admin:8080
      FRAUD_SCORING_URL: http://fraud-scoring:8080
      DB_PASSWORD: ${CLAIMS_DB_PASSWORD}
    depends_on: [postgres, kafka, policy-admin]
    ports: ["8081:8080"]
  fraud-scoring:
    build: ./services/fraud-scoring
    environment:
      FRAUD_LLM_TRIAGE_ENABLED: "false"
      AI_GATEWAY_TOKEN: ${AI_GATEWAY_TOKEN}
    ports: ["8082:8080"]
  payments-gateway:
    build: ./services/payments-gateway
    environment:
      CLEARRIVER_BASE_URL: http://wiremock:8080/payouts/v2
      CLEARRIVER_API_KEY: ${CLEARRIVER_API_KEY}
    depends_on: [postgres, kafka]
  notifications:
    build: ./services/notifications
    environment:
      SMTP_HOST: mailhog
      SMTP_PORT: "1025"
    depends_on: [kafka, mailhog]
  customer-portal:
    build: ./web/customer-portal
    ports: ["3000:8080"]
  mailhog:
    image: mailhog/mailhog:v1.0.1
  wiremock:
    image: wiremock/wiremock:3.9.1
""")
print("infra written")
