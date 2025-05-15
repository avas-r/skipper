# Main Terraform configuration for GCP

# Configure the GCP Provider
provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Create VPC network
resource "google_compute_network" "vpc" {
  name                    = "${var.project_name}-vpc"
  auto_create_subnetworks = false
}

# Create subnets
resource "google_compute_subnetwork" "private_subnet" {
  count         = length(var.private_subnet_cidrs)
  name          = "${var.project_name}-private-subnet-${count.index}"
  ip_cidr_range = var.private_subnet_cidrs[count.index]
  network       = google_compute_network.vpc.id
  region        = var.region
  
  # Enable Private Google Access for reaching Google APIs
  private_ip_google_access = true
  
  # Enable flow logs for security analysis
  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

resource "google_compute_subnetwork" "public_subnet" {
  count         = length(var.public_subnet_cidrs)
  name          = "${var.project_name}-public-subnet-${count.index}"
  ip_cidr_range = var.public_subnet_cidrs[count.index]
  network       = google_compute_network.vpc.id
  region        = var.region
}

# Create GKE cluster
resource "google_container_cluster" "primary" {
  name     = "${var.project_name}-${var.environment}"
  location = var.region
  
  # We can't create a cluster with no node pool defined, but we want to only use
  # separately managed node pools. So we create the smallest possible default
  # node pool and immediately delete it.
  remove_default_node_pool = true
  initial_node_count       = 1
  
  network    = google_compute_network.vpc.name
  subnetwork = google_compute_subnetwork.private_subnet[0].name
  
  # Enable VPC-native cluster (using alias IPs)
  networking_mode = "VPC_NATIVE"
  ip_allocation_policy {
    cluster_ipv4_cidr_block  = var.cluster_ipv4_cidr_block
    services_ipv4_cidr_block = var.services_ipv4_cidr_block
  }
  
  # Enable Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }
  
  # Enable Network Policy
  network_policy {
    enabled  = true
    provider = "CALICO"
  }
  
  # Configure private cluster
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = var.master_ipv4_cidr_block
  }
  
  # Configure master authorized networks
  master_authorized_networks_config {
    dynamic "cidr_blocks" {
      for_each = var.master_authorized_networks
      content {
        cidr_block   = cidr_blocks.value.cidr_block
        display_name = cidr_blocks.value.display_name
      }
    }
  }
  
  # Enable Binary Authorization
  binary_authorization {
    evaluation_mode = "PROJECT_SINGLETON_POLICY_ENFORCE"
  }
}

# Create node pools
resource "google_container_node_pool" "control_plane" {
  name       = "control-plane"
  cluster    = google_container_cluster.primary.id
  node_count = var.environment == "production" ? 3 : 1
  
  node_config {
    preemptible  = var.environment != "production"
    machine_type = var.control_plane_machine_type
    
    # Google recommends custom service accounts that have cloud-platform scope and permissions granted via IAM Roles
    service_account = google_service_account.gke.email
    oauth_scopes    = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
    
    labels = {
      role = "control-plane"
    }
    
    # Enable Workload Identity on the node pool
    workload_metadata_config {
      mode = "GKE_METADATA"
    }
  }
  
  # Configure autoscaling
  autoscaling {
    min_node_count = var.environment == "production" ? 3 : 1
    max_node_count = 5
  }
  
  # Configure auto-repair and auto-upgrade
  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

resource "google_container_node_pool" "agents" {
  name       = "agents"
  cluster    = google_container_cluster.primary.id
  node_count = var.environment == "production" ? 2 : 1
  
  node_config {
    preemptible  = var.environment != "production"
    machine_type = var.agents_machine_type
    
    service_account = google_service_account.gke.email
    oauth_scopes    = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
    
    labels = {
      role = "agent"
    }
    
    # Enable Workload Identity on the node pool
    workload_metadata_config {
      mode = "GKE_METADATA"
    }
  }
  
  # Configure autoscaling
  autoscaling {
    min_node_count = var.environment == "production" ? 2 : 1
    max_node_count = 10
  }
  
  # Configure auto-repair and auto-upgrade
  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

# Create GKE service account
resource "google_service_account" "gke" {
  account_id   = "${var.project_name}-gke-sa"
  display_name = "GKE Service Account for ${var.project_name}"
}

# Grant necessary roles to GKE service account
resource "google_project_iam_member" "gke_roles" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/monitoring.viewer",
    "roles/stackdriver.resourceMetadata.writer",
    "roles/artifactregistry.reader"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.gke.email}"
}

# Create Cloud SQL PostgreSQL instance
resource "google_sql_database_instance" "postgres" {
  name             = "${var.project_name}-${var.environment}-db"
  database_version = "POSTGRES_14"
  region           = var.region
  
  settings {
    tier = var.db_tier
    
    # Enable high availability for production
    availability_type = var.environment == "production" ? "REGIONAL" : "ZONAL"
    
    # Configure backups
    backup_configuration {
      enabled            = true
      binary_log_enabled = false
      start_time         = "02:00"
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = var.environment == "production" ? 14 : 7
        retention_unit   = "COUNT"
      }
    }
    
    # Configure database flags
    database_flags {
      name  = "max_connections"
      value = "100"
    }
    
    # Configure private IP
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
      
      # Configure authorized networks if needed
      dynamic "authorized_networks" {
        for_each = var.db_authorized_networks
        content {
          name  = authorized_networks.value.name
          value = authorized_networks.value.cidr_block
        }
      }
    }
    
    # Configure maintenance window
    maintenance_window {
      day          = 1  # Monday
      hour         = 2  # 2 AM
      update_track = "stable"
    }
    
    # Configure insights
    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
      record_client_address   = true
    }
  }
  
  deletion_protection = var.environment == "production"
}

# Create PostgreSQL database
resource "google_sql_database" "database" {
  name     = "skipper"
  instance = google_sql_database_instance.postgres.name
}

# Create PostgreSQL user
resource "google_sql_user" "user" {
  name     = "skipper"
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
}

# Create Redis instance using Memorystore
resource "google_redis_instance" "cache" {
  name           = "${var.project_name}-${var.environment}-redis"
  memory_size_gb = var.redis_memory_size_gb
  region         = var.region
  
  # Configure Redis version
  redis_version      = "REDIS_6_X"
  
  # Use private IP
  connect_mode       = "PRIVATE_SERVICE_ACCESS"
  authorized_network = google_compute_network.vpc.id
  
  # Configure Redis settings
  redis_configs      = {
    "maxmemory-policy" = "volatile-lru"
  }
  
  # Configure maintenance window
  maintenance_policy {
    weekly_maintenance_window {
      day      = "SUNDAY"
      start_time {
        hours   = 2
        minutes = 0
      }
    }
  }
}

# Create private VPC access for Redis
resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}

resource "google_compute_global_address" "private_ip_address" {
  name          = "${var.project_name}-private-ip-address"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

# Create Pub/Sub topics for message broker
resource "google_pubsub_topic" "task_queue" {
  name = "${var.project_name}-task-queue"
}

resource "google_pubsub_topic" "result_queue" {
  name = "${var.project_name}-result-queue"
}

resource "google_pubsub_topic" "error_queue" {
  name = "${var.project_name}-error-queue"
}

# Create Pub/Sub subscriptions
resource "google_pubsub_subscription" "task_subscription" {
  name  = "${var.project_name}-task-subscription"
  topic = google_pubsub_topic.task_queue.name
  
  # Configure acknowledgement deadline
  ack_deadline_seconds = 60
  
  # Configure retry policy
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
  
  # Configure expiration
  expiration_policy {
    ttl = ""  # Never expire
  }
  
  # Configure dead letter policy
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.error_queue.id
    max_delivery_attempts = 5
  }
}

resource "google_pubsub_subscription" "result_subscription" {
  name  = "${var.project_name}-result-subscription"
  topic = google_pubsub_topic.result_queue.name
  
  ack_deadline_seconds = 60
  
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
  
  expiration_policy {
    ttl = ""
  }
}

resource "google_pubsub_subscription" "error_subscription" {
  name  = "${var.project_name}-error-subscription"
  topic = google_pubsub_topic.error_queue.name
  
  ack_deadline_seconds = 60
  
  expiration_policy {
    ttl = ""
  }
}

# Create Secret Manager for secrets
resource "google_secret_manager_secret" "db_password" {
  secret_id = "${var.project_name}-db-password"
  
  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = var.db_password
}

# Create Cloud Storage bucket for event store
resource "google_storage_bucket" "event_store" {
  name     = "${var.project_name}-${var.environment}-events"
  location = var.region
  
  # Configure versioning
  versioning {
    enabled = true
  }
  
  # Configure object lifecycle
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }
  
  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type = "Delete"
    }
  }
  
  # Configure uniform bucket-level access
  uniform_bucket_level_access = true
  
  # Force destroy for non-production environments
  force_destroy = var.environment != "production"
}

# Set up monitoring for the application
resource "google_monitoring_dashboard" "skipper_dashboard" {
  dashboard_json = jsonencode({
    "displayName": "Skipper Monitoring Dashboard",
    "gridLayout": {
      "widgets": [
        {
          "title": "GKE Cluster CPU Usage",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"k8s_container\" AND resource.labels.cluster_name=\"${google_container_cluster.primary.name}\" AND metric.type=\"kubernetes.io/container/cpu/core_usage_time\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_RATE"
                    }
                  }
                }
              }
            ]
          }
        },
        {
          "title": "GKE Cluster Memory Usage",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"k8s_container\" AND resource.labels.cluster_name=\"${google_container_cluster.primary.name}\" AND metric.type=\"kubernetes.io/container/memory/used_bytes\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_MEAN"
                    }
                  }
                }
              }
            ]
          }
        }
      ]
    }
  })
}

# Create Cloud Logging for centralized logging
resource "google_logging_metric" "error_count" {
  name        = "${var.project_name}_error_count"
  filter      = "resource.type=\"k8s_container\" AND resource.labels.cluster_name=\"${google_container_cluster.primary.name}\" AND severity>=ERROR"
  description = "Count of error logs from Skipper application"
  
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    labels {
      key         = "severity"
      value_type  = "STRING"
      description = "Error severity"
    }
  }
}

# Create alert policy for errors
resource "google_monitoring_alert_policy" "error_alert" {
  display_name = "Skipper Error Rate Alert"
  combiner     = "OR"
  
  conditions {
    display_name = "High Error Rate"
    
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.error_count.name}\" AND resource.type=\"k8s_container\""
      duration        = "60s"
      comparison      = "COMPARISON_GT"
      threshold_value = 10
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
      
      trigger {
        count = 1
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.email.id]
  
  documentation {
    content   = "The Skipper application is experiencing a high error rate. Please investigate."
    mime_type = "text/markdown"
  }
}

# Create notification channel for alerts
resource "google_monitoring_notification_channel" "email" {
  display_name = "Skipper Alert Email"
  type         = "email"
  
  labels = {
    email_address = var.alert_email
  }
}

# Outputs
output "gke_cluster_name" {
  value = google_container_cluster.primary.name
}

output "gke_cluster_endpoint" {
  value = google_container_cluster.primary.endpoint
}

output "postgres_instance_connection_name" {
  value = google_sql_database_instance.postgres.connection_name
}

output "redis_host" {
  value = google_redis_instance.cache.host
}

output "redis_port" {
  value = google_redis_instance.cache.port
}

output "event_store_bucket" {
  value = google_storage_bucket.event_store.name
}