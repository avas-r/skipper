# VPC Module for Skipper infrastructure

# Create VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  
  tags = merge(
    var.tags,
    {
      Name = var.vpc_name
    }
  )
}

# Create Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  
  tags = merge(
    var.tags,
    {
      Name = "${var.vpc_name}-igw"
    }
  )
}

# Create public subnets
resource "aws_subnet" "public" {
  count                   = length(var.public_subnets)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnets[count.index]
  availability_zone       = var.azs[count.index % length(var.azs)]
  map_public_ip_on_launch = true
  
  tags = merge(
    var.tags,
    {
      Name = "${var.vpc_name}-public-${var.azs[count.index % length(var.azs)]}"
      "kubernetes.io/role/elb" = "1"
    }
  )
}

# Create private subnets
resource "aws_subnet" "private" {
  count                   = length(var.private_subnets)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.private_subnets[count.index]
  availability_zone       = var.azs[count.index % length(var.azs)]
  
  tags = merge(
    var.tags,
    {
      Name = "${var.vpc_name}-private-${var.azs[count.index % length(var.azs)]}"
      "kubernetes.io/role/internal-elb" = "1"
    }
  )
}

# Create NAT Gateway for private subnets
resource "aws_eip" "nat" {
  count = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.public_subnets)) : 0
  domain = "vpc"
  
  tags = merge(
    var.tags,
    {
      Name = "${var.vpc_name}-nat-eip-${count.index}"
    }
  )
}

resource "aws_nat_gateway" "main" {
  count         = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.public_subnets)) : 0
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
  
  tags = merge(
    var.tags,
    {
      Name = "${var.vpc_name}-nat-gw-${count.index}"
    }
  )
  
  depends_on = [aws_internet_gateway.main]
}

# Route tables for public subnets
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  
  tags = merge(
    var.tags,
    {
      Name = "${var.vpc_name}-public-rt"
    }
  )
}

resource "aws_route_table_association" "public" {
  count          = length(var.public_subnets)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Route tables for private subnets
resource "aws_route_table" "private" {
  count  = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.private_subnets)) : 0
  vpc_id = aws_vpc.main.id
  
  tags = merge(
    var.tags,
    {
      Name = "${var.vpc_name}-private-rt${count.index}"
    }
  )
}

resource "aws_route" "private_nat_gateway" {
  count                  = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.private_subnets)) : 0
  route_table_id         = aws_route_table.private[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.main[var.single_nat_gateway ? 0 : count.index].id
}

resource "aws_route_table_association" "private" {
  count          = length(var.private_subnets)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[var.single_nat_gateway ? 0 : count.index].id
}

# Security Groups for different components
resource "aws_security_group" "database" {
  name        = "${var.vpc_name}-database-sg"
  description = "Security group for PostgreSQL database"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = var.private_subnets
    description = "Allow PostgreSQL access from private subnets"
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(
    var.tags,
    {
      Name = "${var.vpc_name}-database-sg"
    }
  )
}

resource "aws_security_group" "broker" {
  name        = "${var.vpc_name}-broker-sg"
  description = "Security group for RabbitMQ message broker"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    from_port   = 5671
    to_port     = 5672
    protocol    = "tcp"
    cidr_blocks = var.private_subnets
    description = "Allow RabbitMQ AMQP access from private subnets"
  }
  
  ingress {
    from_port   = 15672
    to_port     = 15672
    protocol    = "tcp"
    cidr_blocks = var.private_subnets
    description = "Allow RabbitMQ management UI access from private subnets"
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(
    var.tags,
    {
      Name = "${var.vpc_name}-broker-sg"
    }
  )
}

resource "aws_security_group" "redis" {
  name        = "${var.vpc_name}-redis-sg"
  description = "Security group for Redis"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = var.private_subnets
    description = "Allow Redis access from private subnets"
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(
    var.tags,
    {
      Name = "${var.vpc_name}-redis-sg"
    }
  )
}

# Create DB subnet group
resource "aws_db_subnet_group" "database" {
  name       = "${var.vpc_name}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id
  
  tags = merge(
    var.tags,
    {
      Name = "${var.vpc_name}-db-subnet-group"
    }
  )
}

# Create ElastiCache subnet group
resource "aws_elasticache_subnet_group" "redis" {
  name       = "${var.vpc_name}-redis-subnet-group"
  subnet_ids = aws_subnet.private[*].id
  
  tags = merge(
    var.tags,
    {
      Name = "${var.vpc_name}-redis-subnet-group"
    }
  )
}

# Outputs
output "vpc_id" {
  value = aws_vpc.main.id
}

output "private_subnets" {
  value = aws_subnet.private[*].id
}

output "public_subnets" {
  value = aws_subnet.public[*].id
}

output "database_subnet_group" {
  value = aws_db_subnet_group.database.name
}

output "elasticache_subnet_group_name" {
  value = aws_elasticache_subnet_group.redis.name
}

output "database_security_group_id" {
  value = aws_security_group.database.id
}

output "broker_security_group_id" {
  value = aws_security_group.broker.id
}

output "redis_security_group_id" {
  value = aws_security_group.redis.id
}