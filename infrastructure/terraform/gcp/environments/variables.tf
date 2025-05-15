# Variables for GCP Terraform configuration

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "skipper"
}

variable "environment" {
  description = "Deployment environment (dev, staging, production)"
  type        = string
  default     = "dev"
}

variable "region" {
  description = "GCP region to deploy resources"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP zone to deploy resources"
  type        = string
  default     = "us-central1-a"
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

variable "cluster_ipv4_cidr_block" {
  description = "CIDR block for pods in the GKE cluster"
  type        = string
  default     = "10.1.0.0/16"
}

variable "services_ipv4_cidr_block" {
  description = "CIDR block for services in the GKE cluster"
  type        = string
  default     = "10.2.0.0/16"
}

variable "master_ipv4_cidr_block" {
  description = "CIDR block for the GKE master"
  type        = string
  default     = "172.16.0.0/28"
}

variable "master_authorized_networks" {
  description = "List of CIDRs that can access the GKE master"
  type        = list(object({
    cidr_block   = string
    display_name = string
  }))
  default     = [
    {
      cidr_block   = "0.0.0.0/0"
      display_name = "All"
    }
  ]
}

variable "control_plane_machine_type" {
  description = "Machine type for control plane node pool"
  type        = string
  default     = "e2-standard-2"
}

variable "agents_machine_type" {
  description = "Machine type for agents node pool"
  type        = string
  default     = "e2-medium"
}

variable "db_tier" {
  description = "The machine type to use for the Cloud SQL instance"
  type        = string
  default     = "db-g1-small"
}

variable "db_password" {
  description = "Password for the database user"
  type        = string
  sensitive   = true
}

variable "db_authorized_networks" {
  description = "List of CIDRs that can access the Cloud SQL instance"
  type        = list(object({
    name       = string
    cidr_block = string
  }))
  default     = []
}

variable "redis_memory_size_gb" {
  description = "Memory size in GB for Redis instance"
  type        = number
  default     = 1
}

variable "alert_email" {
  description = "Email address for alerts"
  type        = string
  default     = "alerts@example.com"
}