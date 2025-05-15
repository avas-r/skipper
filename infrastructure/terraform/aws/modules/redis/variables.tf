# Variables for Redis module

variable "cluster_id" {
  description = "ID for the ElastiCache cluster"
  type        = string
}

variable "engine_version" {
  description = "Version of the Redis engine"
  type        = string
  default     = "6.x"
}

variable "node_type" {
  description = "Instance type for the Redis nodes"
  type        = string
  default     = "cache.t3.small"
}

variable "num_cache_nodes" {
  description = "Number of cache nodes in the cluster"
  type        = number
  default     = 1
}

variable "subnet_group_name" {
  description = "Name of the ElastiCache subnet group"
  type        = string
}

variable "security_group_ids" {
  description = "List of security group IDs to attach to the cluster"
  type        = list(string)
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