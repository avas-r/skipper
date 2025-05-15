# Vault Module for Skipper infrastructure
# Deploys HashiCorp Vault on Kubernetes using Helm

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

# Create namespace for Vault
resource "kubernetes_namespace" "vault" {
  metadata {
    name = "vault"
    
    labels = {
      "app.kubernetes.io/name"       = "vault"
      "app.kubernetes.io/instance"   = "vault"
      "app.kubernetes.io/managed-by" = "terraform"
    }
  }
}

# Create storage class if custom storage is needed
resource "kubernetes_storage_class" "vault" {
  count = var.create_storage_class ? 1 : 0
  
  metadata {
    name = "vault-storage"
  }
  
  storage_provisioner = "kubernetes.io/aws-ebs"
  reclaim_policy      = "Retain"
  parameters = {
    type = "gp2"
  }
  
  allow_volume_expansion = true
}

# Deploy Vault using Helm chart
resource "helm_release" "vault" {
  name       = "vault"
  repository = "https://helm.releases.hashicorp.com"
  chart      = "vault"
  version    = var.vault_chart_version
  namespace  = kubernetes_namespace.vault.metadata[0].name
  
  # General Vault settings
  set {
    name  = "server.ha.enabled"
    value = var.replica_count > 1 ? "true" : "false"
  }
  
  set {
    name  = "server.ha.replicas"
    value = var.replica_count
  }
  
  # Configure storage
  set {
    name  = "server.dataStorage.enabled"
    value = "true"
  }
  
  set {
    name  = "server.dataStorage.size"
    value = var.storage_size
  }
  
  set {
    name  = "server.dataStorage.storageClass"
    value = var.create_storage_class ? kubernetes_storage_class.vault[0].metadata[0].name : var.storage_class
  }
  
  # Configure UI
  set {
    name  = "ui.enabled"
    value = "true"
  }
  
  # Configure logging
  set {
    name  = "server.logs.enabled"
    value = "true"
  }
  
  # Configure service
  set {
    name  = "server.service.type"
    value = "ClusterIP"
  }
  
  # Set Vault configuration
  values = [
    <<-EOT
    server:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchLabels:
                app.kubernetes.io/name: vault
                app.kubernetes.io/instance: vault
                component: server
            topologyKey: kubernetes.io/hostname
      extraSecretEnvironmentVars:
        - envName: AWS_ACCESS_KEY_ID
          secretName: vault-aws-creds
          secretKey: access_key
        - envName: AWS_SECRET_ACCESS_KEY
          secretName: vault-aws-creds
          secretKey: secret_key
      ha:
        enabled: ${var.replica_count > 1 ? "true" : "false"}
        replicas: ${var.replica_count}
        raft:
          enabled: true
          setNodeId: true
      auditStorage:
        enabled: true
        size: 5Gi
      resources:
        requests:
          memory: 256Mi
          cpu: 250m
        limits:
          memory: 512Mi
          cpu: 500m
    EOT
  ]
  
  tags = var.tags
}

# Create AWS credentials secret for Vault
resource "kubernetes_secret" "vault_aws_creds" {
  metadata {
    name      = "vault-aws-creds"
    namespace = kubernetes_namespace.vault.metadata[0].name
  }
  
  data = {
    access_key = var.aws_access_key
    secret_key = var.aws_secret_key
  }
  
  type = "Opaque"
}

# Create Vault initialization and unsealing job
resource "kubernetes_config_map" "vault_init" {
  metadata {
    name      = "vault-init-script"
    namespace = kubernetes_namespace.vault.metadata[0].name
  }
  
  data = {
    "init.sh" = <<-EOT
    #!/bin/sh
    
    # Wait for Vault to be ready
    until nslookup vault-0.vault-internal; do
      echo "Waiting for Vault to be ready..."
      sleep 5
    done
    
    # Check if Vault is already initialized
    INIT_STATUS=$(vault status -format=json | jq -r '.initialized')
    
    if [ "$INIT_STATUS" = "false" ]; then
      echo "Initializing Vault..."
      # Initialize Vault and save the output to a file
      vault operator init -format=json > /vault/data/init-output.json
      
      # Extract keys and token
      cat /vault/data/init-output.json | jq -r '.root_token' > /vault/data/root-token
      cat /vault/data/init-output.json | jq -r '.unseal_keys_b64[0]' > /vault/data/unseal-key-0
      cat /vault/data/init-output.json | jq -r '.unseal_keys_b64[1]' > /vault/data/unseal-key-1
      cat /vault/data/init-output.json | jq -r '.unseal_keys_b64[2]' > /vault/data/unseal-key-2
      
      # Save keys to AWS Secrets Manager
      AWS_REGION=$(curl -s http://169.254.169.254/latest/meta-data/placement/region)
      
      aws secretsmanager create-secret --name "vault/root-token" --secret-string "$(cat /vault/data/root-token)" --region $AWS_REGION
      aws secretsmanager create-secret --name "vault/unseal-keys" --secret-string "$(cat /vault/data/init-output.json | jq -r '.unseal_keys_b64')" --region $AWS_REGION
      
      echo "Vault initialized and keys saved to AWS Secrets Manager"
      
      # Unseal Vault
      echo "Unsealing Vault..."
      vault operator unseal $(cat /vault/data/unseal-key-0)
      vault operator unseal $(cat /vault/data/unseal-key-1)
      vault operator unseal $(cat /vault/data/unseal-key-2)
      
      # Login to Vault
      vault login $(cat /vault/data/root-token)
      
      # Enable audit logging
      vault audit enable file file_path=/vault/logs/audit.log
      
      # Enable secrets engines
      vault secrets enable -path=skipper/kv kv-v2
      vault secrets enable -path=skipper/database database
      
      # Create policies
      echo 'path "skipper/kv/data/*" { capabilities = ["create", "read", "update", "delete", "list"] }' > /tmp/skipper-policy.hcl
      vault policy write skipper /tmp/skipper-policy.hcl
      
      echo "Vault setup complete!"
    else
      echo "Vault is already initialized."
      
      # Check if Vault is sealed
      SEALED_STATUS=$(vault status -format=json | jq -r '.sealed')
      
      if [ "$SEALED_STATUS" = "true" ]; then
        echo "Vault is sealed. Unsealing..."
        
        # Get unseal keys from AWS Secrets Manager
        AWS_REGION=$(curl -s http://169.254.169.254/latest/meta-data/placement/region)
        UNSEAL_KEYS=$(aws secretsmanager get-secret-value --secret-id "vault/unseal-keys" --region $AWS_REGION --query 'SecretString' --output text)
        
        # Unseal using the keys
        echo $UNSEAL_KEYS | jq -r '.[0]' | vault operator unseal
        echo $UNSEAL_KEYS | jq -r '.[1]' | vault operator unseal
        echo $UNSEAL_KEYS | jq -r '.[2]' | vault operator unseal
        
        echo "Vault unsealed successfully."
      else
        echo "Vault is already unsealed."
      fi
    fi
    EOT
  }
}

# Create Kubernetes job for initializing Vault
resource "kubernetes_job" "vault_init" {
  depends_on = [helm_release.vault]
  
  metadata {
    name      = "vault-init"
    namespace = kubernetes_namespace.vault.metadata[0].name
  }
  
  spec {
    template {
      metadata {
        labels = {
          app = "vault-init"
        }
      }
      
      spec {
        container {
          name    = "vault-init"
          image   = "hashicorp/vault:${var.vault_version}"
          command = ["/bin/sh", "/scripts/init.sh"]
          
          env {
            name  = "VAULT_ADDR"
            value = "http://vault-0.vault-internal:8200"
          }
          
          volume_mount {
            name       = "script-volume"
            mount_path = "/scripts"
          }
          
          volume_mount {
            name       = "data-volume"
            mount_path = "/vault/data"
          }
          
          resources {
            limits = {
              cpu    = "200m"
              memory = "256Mi"
            }
            requests = {
              cpu    = "100m"
              memory = "128Mi"
            }
          }
        }
        
        volume {
          name = "script-volume"
          config_map {
            name = kubernetes_config_map.vault_init.metadata[0].name
            default_mode = "0755"
          }
        }
        
        volume {
          name = "data-volume"
          empty_dir {}
        }
        
        restart_policy = "OnFailure"
        service_account_name = "vault"
      }
    }
    
    backoff_limit = 3
  }
}

# Outputs
output "vault_service" {
  value = "vault.${kubernetes_namespace.vault.metadata[0].name}.svc.cluster.local"
}

output "vault_url" {
  value = "http://vault.${kubernetes_namespace.vault.metadata[0].name}.svc.cluster.local:8200"
}