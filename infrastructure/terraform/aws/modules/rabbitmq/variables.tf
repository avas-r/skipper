# Variables for RabbitMQ module

variable "broker_name" {
  description = "Name of the Amazon MQ broker"
  type        = string
}

variable "engine_type" {
  description = "Type of broker engine"
  type        = string
  default     = "RabbitMQ"
}

variable "engine_version" {
  description = "Version of the broker engine"
  type        = string
  default     = "3.10.20"
}

variable "host_instance_type" {
  description = "EC2 instance type for the broker"
  type        = string
  default     = "mq.t3.micro"
}

variable "security_groups" {
  description = "List of security group IDs to attach to the broker"
  type        = list(string)
}

variable "subnet_ids" {
  description = "List of subnet IDs for the broker. Use only one for single-instance deployment mode."
  type        = list(string)
}

variable "username" {
  description = "Username for the RabbitMQ broker"
  type        = string
}

variable "password" {
  description = "Password for the RabbitMQ broker"
  type        = string
  sensitive   = true
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