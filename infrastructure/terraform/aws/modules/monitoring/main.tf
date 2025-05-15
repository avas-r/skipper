# Monitoring Module for Skipper infrastructure
# Deploys Prometheus and Grafana on Kubernetes using Helm

# Set up Kubernetes provider
provider "kubernetes" {
  host                   = var.kubernetes_config.host
  cluster_ca_certificate = base64decode(var.kubernetes_config.cluster_ca_certificate)
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    args        = ["eks", "get-token", "--cluster-name", var.cluster_name]
    command     = "aws"
  }
}

# Set up Helm provider
provider "helm" {
  kubernetes {
    host                   = var.kubernetes_config.host
    cluster_ca_certificate = base64decode(var.kubernetes_config.cluster_ca_certificate)
    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      args        = ["eks", "get-token", "--cluster-name", var.cluster_name]
      command     = "aws"
    }
  }
}

# Create namespace for monitoring
resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = "monitoring"
    
    labels = {
      "app.kubernetes.io/name"       = "monitoring"
      "app.kubernetes.io/instance"   = "monitoring"
      "app.kubernetes.io/managed-by" = "terraform"
    }
  }
}

# Deploy Prometheus using Helm chart
resource "helm_release" "prometheus" {
  name       = "prometheus"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "prometheus"
  version    = var.prometheus_chart_version
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  
  # General Prometheus settings
  set {
    name  = "server.persistentVolume.enabled"
    value = "true"
  }
  
  set {
    name  = "server.persistentVolume.size"
    value = var.prometheus_storage
  }
  
  set {
    name  = "server.retention"
    value = var.environment == "production" ? "15d" : "7d"
  }
  
  # Configure Alertmanager
  set {
    name  = "alertmanager.enabled"
    value = "true"
  }
  
  set {
    name  = "alertmanager.persistentVolume.enabled"
    value = "true"
  }
  
  set {
    name  = "alertmanager.persistentVolume.size"
    value = "5Gi"
  }
  
  # Configure Node Exporter
  set {
    name  = "nodeExporter.enabled"
    value = "true"
  }
  
  # Configure service
  set {
    name  = "server.service.type"
    value = "ClusterIP"
  }
  
  # Add custom scrape configs
  values = [
    <<-EOT
    server:
      global:
        scrape_interval: 15s
        evaluation_interval: 15s
      resources:
        limits:
          cpu: 500m
          memory: 512Mi
        requests:
          cpu: 200m
          memory: 256Mi
      extraScrapeConfigs: |
        - job_name: 'rabbitmq'
          static_configs:
            - targets: ['rabbitmq:15692']
        - job_name: 'redis'
          static_configs:
            - targets: ['redis-exporter:9121']
        - job_name: 'postgres'
          static_configs:
            - targets: ['postgres-exporter:9187']
        - job_name: 'local-agents'
          kubernetes_sd_configs:
            - role: pod
          relabel_configs:
            - source_labels: [__meta_kubernetes_pod_label_app]
              regex: local-agent
              action: keep
    alertmanager:
      resources:
        limits:
          cpu: 200m
          memory: 256Mi
        requests:
          cpu: 100m
          memory: 128Mi
      config:
        global:
          resolve_timeout: 5m
        route:
          group_by: ['alertname', 'job']
          group_wait: 30s
          group_interval: 5m
          repeat_interval: 12h
          receiver: 'slack'
        receivers:
        - name: 'slack'
          slack_configs:
          - api_url: 'https://hooks.slack.com/services/YOUR_SLACK_WEBHOOK'
            channel: '#alerts'
            send_resolved: true
    EOT
  ]
  
  tags = var.tags
}

# Deploy Grafana using Helm chart
resource "helm_release" "grafana" {
  name       = "grafana"
  repository = "https://grafana.github.io/helm-charts"
  chart      = "grafana"
  version    = var.grafana_chart_version
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  
  depends_on = [helm_release.prometheus]
  
  # General Grafana settings
  set {
    name  = "persistence.enabled"
    value = "true"
  }
  
  set {
    name  = "persistence.size"
    value = var.grafana_storage
  }
  
  # Configure admin user
  set {
    name  = "adminUser"
    value = "admin"
  }
  
  set {
    name  = "adminPassword"
    value = var.grafana_admin_password
  }
  
  # Configure service
  set {
    name  = "service.type"
    value = "ClusterIP"
  }
  
  # Configure datasources and dashboards
  values = [
    <<-EOT
    datasources:
      datasources.yaml:
        apiVersion: 1
        datasources:
        - name: Prometheus
          type: prometheus
          url: http://prometheus-server.monitoring.svc.cluster.local
          access: proxy
          isDefault: true
    
    dashboardProviders:
      dashboardproviders.yaml:
        apiVersion: 1
        providers:
        - name: 'default'
          orgId: 1
          folder: ''
          type: file
          disableDeletion: false
          editable: true
          options:
            path: /var/lib/grafana/dashboards/default
    
    dashboards:
      default:
        kubernetes-cluster:
          gnetId: 6417
          revision: 1
          datasource: Prometheus
        rabbitmq:
          gnetId: 10991
          revision: 1
          datasource: Prometheus
        redis:
          gnetId: 763
          revision: 1
          datasource: Prometheus
        postgres:
          gnetId: 9628
          revision: 1
          datasource: Prometheus
        node-exporter:
          gnetId: 1860
          revision: 21
          datasource: Prometheus
    
    resources:
      limits:
        cpu: 200m
        memory: 256Mi
      requests:
        cpu: 100m
        memory: 128Mi
    
    plugins:
      - grafana-piechart-panel
      - grafana-clock-panel
      - briangann-gauge-panel
    EOT
  ]
  
  tags = var.tags
}

# Create Redis Exporter for monitoring Redis
resource "helm_release" "redis_exporter" {
  name       = "redis-exporter"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "prometheus-redis-exporter"
  version    = var.redis_exporter_chart_version
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  
  set {
    name  = "redisAddress"
    value = "redis://redis:6379"
  }
  
  set {
    name  = "serviceMonitor.enabled"
    value = "true"
  }
  
  tags = var.tags
}

# Create PostgreSQL Exporter for monitoring PostgreSQL
resource "helm_release" "postgres_exporter" {
  name       = "postgres-exporter"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "prometheus-postgres-exporter"
  version    = var.postgres_exporter_chart_version
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  
  set {
    name  = "config.datasource.host"
    value = var.postgres_host
  }
  
  set {
    name  = "config.datasource.user"
    value = var.postgres_user
  }
  
  set {
    name  = "config.datasource.password"
    value = var.postgres_password
  }
  
  set {
    name  = "config.datasource.database"
    value = var.postgres_database
  }
  
  set {
    name  = "serviceMonitor.enabled"
    value = "true"
  }
  
  tags = var.tags
}

# Outputs
output "prometheus_url" {
  value = "http://prometheus-server.${kubernetes_namespace.monitoring.metadata[0].name}.svc.cluster.local"
}

output "grafana_url" {
  value = "http://grafana.${kubernetes_namespace.monitoring.metadata[0].name}.svc.cluster.local"
}