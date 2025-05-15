# Skipper Deployment Guide

## Production Requirements

- Kubernetes cluster (v1.25+)
- PostgreSQL database (v14+)
- RabbitMQ (v3.9+)
- Redis (v6+)
- HashiCorp Vault (v1.12+)

## Deployment Options

### Kubernetes Deployment

1. Create namespace:
   ```bash
   kubectl create namespace skipper
   ```

2. Create configuration:
   ```bash
   kubectl create secret generic skipper-secrets \
     --from-literal=database_url="postgresql://user:password@host:port/database" \
     --from-literal=rabbitmq_url="amqp://user:password@host:port" \
     --from-literal=redis_url="redis://host:port" \
     --from-literal=vault_addr="https://vault.example.com" \
     --from-literal=vault_token="s.token" \
     --namespace skipper
   ```

3. Deploy components:
   ```bash
   kubectl apply -f deployment/kubernetes/ --namespace skipper
   ```

### Helm Chart (Alternative)

[Helm chart documentation will be added]

## Environment Variables

### Common Variables

- : Logging level (default: info)
- : Environment name (default: production)

### Backend Variables

- : PostgreSQL connection string
- : RabbitMQ connection string
- : Redis connection string
- : Secret for JWT tokens
- : Allowed CORS origins

[Additional environment variables]

## Scaling Considerations

[Scaling guidelines for each component]

## Monitoring

[Monitoring setup instructions]

## Backup and Recovery

[Backup and recovery procedures]
