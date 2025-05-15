# Skipper Infrastructure

This directory contains the infrastructure code for the Skipper distributed agent management system.

## Directory Structure

```
infra/
├── docker/                      # Docker configuration files
│   ├── config/                  # Configuration for Docker services
│   │   ├── grafana/             # Grafana configuration
│   │   ├── loki/                # Loki configuration
│   │   ├── prometheus/          # Prometheus configuration
│   │   ├── promtail/            # Promtail configuration
│   │   └── redis/               # Redis configuration
│   └── init-scripts/            # Initialization scripts for services
│       ├── postgres/            # PostgreSQL initialization scripts
│       └── rabbitmq/            # RabbitMQ initialization scripts
├── scripts/                     # Management scripts
│   ├── deploy.sh                # Deployment management script
│   └── setup-dev.sh             # Development environment setup script
├── terraform/                   # Terraform configurations
│   ├── aws/                     # AWS Terraform configuration
│   │   ├── environments/        # Environment-specific variables
│   │   └── modules/             # Terraform modules for AWS
│   └── gcp/                     # GCP Terraform configuration
│       └── environments/        # Environment-specific variables
└── docker-compose.yml           # Local development Docker Compose file
```

## Local Development

The local development environment uses Docker Compose to set up all required services.

### Prerequisites

- Docker and Docker Compose
- Git
- Python 3.10+
- Node.js 18+

### Setup

1. Run the development environment setup script:

```bash
cd infra/scripts
chmod +x setup-dev.sh
./setup-dev.sh
```

2. Start the local environment:

```bash
docker-compose -f infra/docker-compose.yml up -d
```

3. Access the services:

   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/docs
   - RabbitMQ Management: http://localhost:15672 (guest/guest)
   - Grafana: http://localhost:3001 (admin/admin)
   - Prometheus: http://localhost:9090
   - PGAdmin: http://localhost:5050 (admin@example.com/admin)
   - Mailhog: http://localhost:8025
   - MinIO: http://localhost:9001 (minioadmin/minioadmin)

## Cloud Deployment

The cloud deployment uses Terraform to provision resources on AWS or GCP.

### AWS Deployment

#### Infrastructure Components

- **VPC** with public and private subnets
- **EKS Cluster** for running the Skipper components
- **RDS PostgreSQL** for persistent storage
- **Amazon MQ (RabbitMQ)** for message broker
- **ElastiCache Redis** for caching
- **S3 Bucket** for event store
- **HashiCorp Vault** for secrets management
- **Prometheus and Grafana** for monitoring

#### Deployment Steps

1. Initialize Terraform:

```bash
cd infra/scripts
chmod +x deploy.sh
./deploy.sh --provider aws --environment dev --init
```

2. Edit the environment variables:

```bash
vi ../terraform/aws/environments/dev.tfvars
```

3. Apply the Terraform configuration:

```bash
./deploy.sh --provider aws --environment dev --apply
```

### GCP Deployment

#### Infrastructure Components

- **VPC** with public and private subnets
- **GKE Cluster** for running the Skipper components
- **Cloud SQL PostgreSQL** for persistent storage
- **Pub/Sub** for message broker
- **Memorystore Redis** for caching
- **Cloud Storage** for event store
- **Secret Manager** for secrets management
- **Cloud Monitoring** for monitoring

#### Deployment Steps

1. Initialize Terraform:

```bash
cd infra/scripts
chmod +x deploy.sh
./deploy.sh --provider gcp --environment dev --init
```

2. Edit the environment variables:

```bash
vi ../terraform/gcp/environments/dev.tfvars
```

3. Apply the Terraform configuration:

```bash
./deploy.sh --provider gcp --environment dev --apply
```

## Architecture Overview

The Skipper infrastructure follows a microservices architecture with the following components:

### Control Plane

- **Web & API Portal**: User interface for managing agents and viewing reports
- **User Agent**: Handles authentication and authorization
- **Scheduler Agent**: Distributes tasks among available agents
- **Execution Agent**: Monitors task execution and collects results
- **Error-Handling Agent**: Processes failures and retries
- **Audit & Compliance Agent**: Tracks all operations for compliance

### Infrastructure

- **Message Broker**: RabbitMQ for task distribution and event handling
- **Credential Vault**: HashiCorp Vault for secure credential management
- **PostgreSQL DB**: Persistent storage for agents, tasks, and results
- **Event Store**: Long-term storage for audit events
- **Observability Suite**: Prometheus/Grafana for metrics and monitoring

### Endpoints

- **Local Agent Cluster**: Distributed agents that execute tasks and report status

## Communication Patterns

The communication between components follows these patterns:

1. **Command Flow**: UI → Auth → Scheduler → Broker → Local Agent
2. **Result Flow**: Local Agent → Broker → Execution Agent → DB
3. **Monitoring Flow**: Local Agent → Broker → Observability Suite
4. **Error Flow**: Local Agent → Broker → Error-Handling Agent → Scheduler

## Security Considerations

### AWS Security

- **VPC Security Groups**: Restrict traffic between services
- **IAM Roles**: Use least privilege principle for service accounts
- **KMS Encryption**: Encrypt data at rest
- **Private Subnets**: Run critical infrastructure in private subnets
- **Network ACLs**: Control traffic at subnet level
- **Security Hub**: Monitor security best practices

### GCP Security

- **VPC Service Controls**: Restrict resource access
- **IAM Roles**: Use least privilege principle for service accounts
- **KMS Encryption**: Encrypt data at rest
- **Private Networks**: Run critical infrastructure in private networks
- **Cloud Armor**: DDoS protection and WAF
- **Security Command Center**: Monitor security best practices

## Scaling Considerations

The infrastructure is designed to scale independently:

- **Horizontal Scaling**: Add more nodes to the Kubernetes clusters
- **Vertical Scaling**: Increase resources for individual services
- **Auto Scaling**: Configure auto-scaling for workloads
- **Regional Deployments**: Deploy across multiple regions for resilience
- **Load Balancing**: Distribute traffic across instances

## Monitoring and Observability

The monitoring solution includes:

- **Prometheus**: Metrics collection
- **Grafana**: Metrics visualization
- **Loki**: Log aggregation
- **Jaeger**: Distributed tracing
- **Alertmanager**: Alert notifications

## Backup and Recovery

The backup strategy includes:

- **Database Backups**: Automated backups for PostgreSQL
- **Object Storage Versioning**: Versioning for event store data
- **Snapshot Backups**: Regular snapshots of critical infrastructure
- **Disaster Recovery**: Cross-region replication for critical data
- **Restore Testing**: Regular testing of backup restoration

## Maintenance Procedures

### Database Maintenance

- Run `VACUUM ANALYZE` regularly
- Monitor disk space usage
- Keep indexes optimized

### Kubernetes Maintenance

- Update Kubernetes version regularly
- Rotate node certificates
- Apply security patches promptly

### Certificate Rotation

- Monitor certificate expiration dates
- Rotate certificates before expiration
- Use automated certificate management

## Troubleshooting

### Common Issues

#### Database Connection Issues

```bash
# Check database connectivity
kubectl exec -it deploy/backend -- psql -h postgres -U skipper -d skipper -c "SELECT 1"
```

#### Message Broker Issues

```bash
# Check RabbitMQ queues
kubectl exec -it deploy/rabbitmq -- rabbitmqctl list_queues
```

#### Agent Connectivity Issues

```bash
# Check agent logs
kubectl logs deploy/local-agent
```

## Contributing to Infrastructure

1. Follow Infrastructure as Code (IaC) principles
2. Test changes in development before applying to production
3. Document all infrastructure changes
4. Use pull requests for infrastructure changes
5. Follow the principle of least privilege when granting permissions

## License

[License information goes here]