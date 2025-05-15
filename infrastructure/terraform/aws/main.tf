# Main Terraform configuration for AWS

# Configure the AWS Provider
provider "aws" {
  region = var.aws_region
}

# Create VPC and networking components
module "vpc" {
  source = "./modules/vpc"
  
  vpc_name        = "${var.project_name}-vpc"
  vpc_cidr        = var.vpc_cidr
  azs             = var.availability_zones
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs
  
  enable_nat_gateway = true
  single_nat_gateway = var.environment != "production"
  
  tags = local.common_tags
}

# EKS Cluster for running the Skipper components
module "eks" {
  source = "./modules/eks"
  
  cluster_name    = "${var.project_name}-${var.environment}"
  cluster_version = var.kubernetes_version
  
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnets
  
  # Node groups for different workloads
  node_groups = {
    control_plane = {
      instance_types = ["t3.medium"]
      min_size       = 2
      max_size       = 3
      desired_size   = 2
      labels = {
        role = "control-plane"
      }
    },
    agents = {
      instance_types = ["t3.small"]
      min_size       = 2
      max_size       = 10
      desired_size   = 3
      labels = {
        role = "agent"
      }
    }
  }
  
  tags = local.common_tags
}

# RDS PostgreSQL instance for persistent storage
module "postgres" {
  source = "./modules/postgres"
  
  identifier           = "${var.project_name}-${var.environment}-db"
  engine               = "postgres"
  engine_version       = "14"
  instance_class       = var.db_instance_class
  allocated_storage    = var.db_allocated_storage
  
  name                 = "skipper"
  username             = "skipper"
  password             = var.db_password
  
  vpc_security_group_ids = [module.vpc.database_security_group_id]
  subnet_ids             = module.vpc.database_subnets
  
  backup_retention_period = 7
  deletion_protection     = var.environment == "production"
  
  tags = local.common_tags
}

# Amazon MQ (RabbitMQ) for message broker
module "rabbitmq" {
  source = "./modules/rabbitmq"
  
  broker_name        = "${var.project_name}-${var.environment}-broker"
  engine_type        = "RabbitMQ"
  engine_version     = "3.10.20"
  host_instance_type = var.rabbitmq_instance_type
  
  security_groups    = [module.vpc.broker_security_group_id]
  subnet_ids         = [module.vpc.private_subnets[0]]
  
  username           = "skipper"
  password           = var.rabbitmq_password
  
  tags = local.common_tags
}

# ElastiCache Redis for caching and temporary storage
module "redis" {
  source = "./modules/redis"
  
  cluster_id           = "${var.project_name}-${var.environment}-redis"
  node_type            = var.redis_node_type
  engine_version       = "6.x"
  num_cache_nodes      = 1
  
  subnet_group_name    = module.vpc.elasticache_subnet_group_name
  security_group_ids   = [module.vpc.redis_security_group_id]
  
  tags = local.common_tags
}

# HashiCorp Vault for secrets management (deployed on EKS)
module "vault" {
  source = "./modules/vault"
  
  cluster_name      = module.eks.cluster_name
  kubernetes_config = module.eks.kubeconfig
  
  storage_class     = "gp2"
  replica_count     = var.environment == "production" ? 3 : 1
  
  tags = local.common_tags
}

# Prometheus and Grafana for observability (deployed on EKS)
module "monitoring" {
  source = "./modules/monitoring"
  
  cluster_name      = module.eks.cluster_name
  kubernetes_config = module.eks.kubeconfig
  
  prometheus_storage = "20Gi"
  grafana_storage    = "10Gi"
  
  tags = local.common_tags
}

# S3 bucket for event store and long-term storage
module "event_store" {
  source = "./modules/event_store"
  
  bucket_name  = "${var.project_name}-${var.environment}-events"
  versioning   = true
  
  lifecycle_rules = [{
    id      = "archive-after-90-days"
    enabled = true
    
    transition = [{
      days          = 90
      storage_class = "GLACIER"
    }]
    
    expiration = {
      days = 365
    }
  }]
  
  tags = local.common_tags
}