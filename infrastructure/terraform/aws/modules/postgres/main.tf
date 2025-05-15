# PostgreSQL Module for Skipper infrastructure

# Create PostgreSQL RDS instance
resource "aws_db_instance" "postgres" {
  identifier           = var.identifier
  engine               = var.engine
  engine_version       = var.engine_version
  instance_class       = var.instance_class
  allocated_storage    = var.allocated_storage
  storage_type         = "gp2"
  storage_encrypted    = true
  
  db_name              = var.name
  username             = var.username
  password             = var.password
  port                 = 5432
  
  vpc_security_group_ids = var.vpc_security_group_ids
  db_subnet_group_name   = aws_db_subnet_group.postgres.name
  
  backup_retention_period = var.backup_retention_period
  backup_window           = "03:00-04:00"
  maintenance_window      = "mon:04:00-mon:05:00"
  
  multi_az               = var.environment == "production"
  deletion_protection    = var.deletion_protection
  skip_final_snapshot    = var.environment != "production"
  final_snapshot_identifier = var.environment == "production" ? "${var.identifier}-final-snapshot" : null
  
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  
  # Disable performance insights for non-production
  performance_insights_enabled = var.environment == "production"
  
  # Enable auto minor version upgrades for security patches
  auto_minor_version_upgrade = true
  
  tags = var.tags
}

# Create DB subnet group if not provided
resource "aws_db_subnet_group" "postgres" {
  count      = var.db_subnet_group_name == null ? 1 : 0
  name       = "${var.identifier}-subnet-group"
  subnet_ids = var.subnet_ids
  
  tags = merge(
    var.tags,
    {
      Name = "${var.identifier}-subnet-group"
    }
  )
}

# Outputs
output "endpoint" {
  value = aws_db_instance.postgres.endpoint
}

output "address" {
  value = aws_db_instance.postgres.address
}

output "port" {
  value = aws_db_instance.postgres.port
}

output "name" {
  value = aws_db_instance.postgres.db_name
}

output "username" {
  value = aws_db_instance.postgres.username
}

output "connection_string" {
  value     = "postgresql://${aws_db_instance.postgres.username}:${var.password}@${aws_db_instance.postgres.endpoint}/${aws_db_instance.postgres.db_name}"
  sensitive = true
}