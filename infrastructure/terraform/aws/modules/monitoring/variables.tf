# Variables for Monitoring module

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
}

variable "kubernetes_config" {
  description = "Kubernetes configuration with host, certificate, etc."
  type        = object({
    host                   = string
    cluster_ca_certificate = string
  })
}

variable "prometheus_storage" {
  description = "Size of the storage volume for Prometheus"
  type        = string
  default     = "20Gi"
}

variable "grafana_storage" {
  description = "Size of the storage volume for Grafana"
  type        = string
  default     = "10Gi"
}

variable "prometheus_chart_version" {
  description = "Version of the Prometheus Helm chart"
  type        = string
  default     = "15.10.1"
}

variable "grafana_chart_version" {
  description = "Version of the Grafana Helm chart"
  type        = string
  default     = "6.40.0"
}

variable "redis_exporter_chart_version" {
  description = "Version of the Redis Exporter Helm chart"
  type        = string
  default     = "5.2.0"
}

variable "postgres_exporter_chart_version" {
  description = "Version of the PostgreSQL Exporter Helm chart"
  type        = string
  default     = "2.5.1"
}

variable "grafana_admin_password" {
  description = "Admin password for Grafana"
  type        = string
  sensitive   = true
  default     = "admin"
}

variable "postgres_host" {
  description = "PostgreSQL host for the exporter to connect to"
  type        = string
  default     = "postgres"
}

variable "postgres_user" {
  description = "PostgreSQL user for the exporter"
  type        = string
  default     = "postgres_exporter"
}

variable "postgres_password" {
  description = "PostgreSQL password for the exporter"
  type        = string
  sensitive   = true
  default     = ""
}

variable "postgres_database" {
  description = "PostgreSQL database for the exporter"
  type        = string
  default     = "postgres"
}

variable "environment" {
  description = "Deployment environment (dev, staging, production)"
  type        = string
  default     = "dev"
}

variable "tags" {
  description = "A map of tags to add to all resources"
  type        = map(string)
  default     = {}
}