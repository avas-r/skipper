# Redis Module for Skipper infrastructure using ElastiCache

# Create ElastiCache Redis cluster
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = var.cluster_id
  engine               = "redis"
  engine_version       = var.engine_version
  node_type            = var.node_type
  num_cache_nodes      = var.num_cache_nodes
  parameter_group_name = aws_elasticache_parameter_group.redis.name
  
  subnet_group_name    = var.subnet_group_name
  security_group_ids   = var.security_group_ids
  
  port                 = 6379
  
  # Enable automatic backup
  snapshot_retention_limit = var.environment == "production" ? 7 : 1
  snapshot_window          = "02:00-03:00"
  
  # Maintenance window
  maintenance_window = "sun:03:00-sun:04:00"
  
  # Enable automatic failover for production
  automatic_failover_enabled = var.environment == "production" && var.num_cache_nodes > 1
  
  # Enable encryption in transit and at rest for production
  transit_encryption_enabled = var.environment == "production"
  at_rest_encryption_enabled = var.environment == "production"
  
  tags = var.tags
}

# Create Redis parameter group
resource "aws_elasticache_parameter_group" "redis" {
  name   = "${var.cluster_id}-params"
  family = "redis6.x"
  
  # Set Redis parameters
  parameter {
    name  = "maxmemory-policy"
    value = "volatile-lru"
  }
  
  parameter {
    name  = "notify-keyspace-events"
    value = "KEA"
  }
  
  parameter {
    name  = "maxmemory-samples"
    value = "10"
  }
  
  parameter {
    name  = "slowlog-log-slower-than"
    value = "10000"
  }
  
  parameter {
    name  = "slowlog-max-len"
    value = "128"
  }
  
  tags = var.tags
}

# Outputs
output "endpoint" {
  value = aws_elasticache_cluster.redis.cache_nodes[0].address
}

output "port" {
  value = aws_elasticache_cluster.redis.cache_nodes[0].port
}

output "connection_string" {
  value = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:${aws_elasticache_cluster.redis.cache_nodes[0].port}"
}