# Variables for Vault module

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

variable "replica_count" {
  description = "Number of Vault replicas for HA setup"
  type        = number
  default     = 1
}

variable "create_storage_class" {
  description = "Whether to create a custom storage class for Vault"
  type        = bool
  default     = false
}

variable "storage_class" {
  description = "Storage class to use for Vault if not creating a custom one"
  type        = string
  default     = "gp2"
}

variable "storage_size" {
  description = "Size of the storage volume for Vault"
  type        = string
  default     = "10Gi"
}

variable "vault_chart_version" {
  description = "Version of the Vault Helm chart"
  type        = string
  default     = "0.23.0"
}

variable "vault_version" {
  description = "Version of Vault to deploy"
  type        = string
  default     = "1.13.1"
}

variable "aws_access_key" {
  description = "AWS access key for Vault to use"
  type        = string
  sensitive   = true
  default     = ""
}

variable "aws_secret_key" {
  description = "AWS secret key for Vault to use"
  type        = string
  sensitive   = true
  default     = ""
}

variable "tags" {
  description = "A map of tags to add to all resources"
  type        = map(string)
  default     = {}
}