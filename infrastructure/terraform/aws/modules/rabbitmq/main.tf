# RabbitMQ Module for Skipper infrastructure using Amazon MQ

# Create Amazon MQ RabbitMQ broker
resource "aws_mq_broker" "rabbitmq" {
  broker_name        = var.broker_name
  engine_type        = var.engine_type
  engine_version     = var.engine_version
  host_instance_type = var.host_instance_type
  security_groups    = var.security_groups
  subnet_ids         = var.subnet_ids
  
  deployment_mode = var.environment == "production" ? "CLUSTER_MULTI_AZ" : "SINGLE_INSTANCE"
  
  # Authentication
  authentication_strategy = "simple"
  users {
    username = var.username
    password = var.password
  }
  
  # Configuration
  configuration {
    id       = aws_mq_configuration.rabbitmq.id
    revision = aws_mq_configuration.rabbitmq.latest_revision
  }
  
  # Enable CloudWatch logs
  logs {
    general = true
    audit   = var.environment == "production"
  }
  
  # Auto-minor-version upgrade
  auto_minor_version_upgrade = true
  
  # Maintenance window
  maintenance_window_start_time {
    day_of_week = "SUNDAY"
    time_of_day = "02:00"
    time_zone   = "UTC"
  }
  
  tags = var.tags
}

# Create RabbitMQ configuration
resource "aws_mq_configuration" "rabbitmq" {
  name           = "${var.broker_name}-config"
  engine_type    = var.engine_type
  engine_version = var.engine_version
  
  # RabbitMQ configuration in YAML format
  data = <<-EOF
    # Default RabbitMQ configuration
    rabbitmq.default_vhost = /
    rabbitmq.default_user = skipper
    rabbitmq.default_user_tags.administrator = true
    rabbitmq.default_user_tags.management = true
    
    # Default queues and exchanges
    rabbitmq.queues.0.name = task_queue
    rabbitmq.queues.0.vhost = /
    rabbitmq.queues.0.durable = true
    rabbitmq.queues.0.auto_delete = false
    
    rabbitmq.queues.1.name = result_queue
    rabbitmq.queues.1.vhost = /
    rabbitmq.queues.1.durable = true
    rabbitmq.queues.1.auto_delete = false
    
    rabbitmq.queues.2.name = error_queue
    rabbitmq.queues.2.vhost = /
    rabbitmq.queues.2.durable = true
    rabbitmq.queues.2.auto_delete = false
    
    rabbitmq.exchanges.0.name = task_exchange
    rabbitmq.exchanges.0.vhost = /
    rabbitmq.exchanges.0.type = direct
    rabbitmq.exchanges.0.durable = true
    rabbitmq.exchanges.0.auto_delete = false
    
    # Performance tuning
    rabbitmq.tcp_listen_options.backlog = 4096
    rabbitmq.tcp_listen_options.sndbuf = 32768
    rabbitmq.tcp_listen_options.recbuf = 32768
    
    # Resource limits
    rabbitmq.disk_free_limit.relative = 0.2
    rabbitmq.vm_memory_high_watermark.relative = 0.4
  EOF
  
  tags = var.tags
}

# Outputs
output "broker_id" {
  value = aws_mq_broker.rabbitmq.id
}

output "broker_arn" {
  value = aws_mq_broker.rabbitmq.arn
}

output "broker_endpoints" {
  value = aws_mq_broker.rabbitmq.instances[*].endpoints
}

output "primary_amqp_endpoint" {
  value = [for endpoint in flatten(aws_mq_broker.rabbitmq.instances[*].endpoints) : endpoint if startswith(endpoint, "amqp")][0]
}

output "management_console_url" {
  value = aws_mq_broker.rabbitmq.instances[0].console_url
}

output "connection_string" {
  value     = "amqp://${var.username}:${var.password}@${[for endpoint in flatten(aws_mq_broker.rabbitmq.instances[*].endpoints) : endpoint if startswith(endpoint, "amqp")][0]}"
  sensitive = true
}