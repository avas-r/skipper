#!/bin/bash

# Skipper Cloud Deployment Management Script
# This script manages cloud deployments using Terraform

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
CLOUD_PROVIDER="aws"
ENVIRONMENT="dev"
ACTION="plan"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print with timestamp
function log() {
  echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Print success message
function success() {
  log "${GREEN}SUCCESS: $1${NC}"
}

# Print info message
function info() {
  log "${YELLOW}INFO: $1${NC}"
}

# Print error message
function error() {
  log "${RED}ERROR: $1${NC}"
}

# Print heading
function heading() {
  echo
  echo -e "${BLUE}==== $1 ====${NC}"
  echo
}

# Check if terraform is installed
function check_terraform() {
  if ! command -v terraform &>/dev/null; then
    error "Terraform is not installed. Please install Terraform and try again."
    exit 1
  fi
  
  local tf_version
  tf_version=$(terraform version -json | jq -r '.terraform_version')
  info "Terraform version: $tf_version"
}

# Check if AWS CLI is installed
function check_aws_cli() {
  if ! command -v aws &>/dev/null; then
    error "AWS CLI is not installed. Please install AWS CLI and try again."
    exit 1
  fi
  
  local aws_version
  aws_version=$(aws --version | cut -d ' ' -f 1 | cut -d '/' -f 2)
  info "AWS CLI version: $aws_version"
  
  # Check if AWS credentials are configured
  if ! aws sts get-caller-identity >/dev/null 2>&1; then
    error "AWS credentials are not configured or invalid. Please run 'aws configure' and try again."
    exit 1
  fi
}

# Check if GCP CLI is installed
function check_gcp_cli() {
  if ! command -v gcloud &>/dev/null; then
    error "GCP CLI is not installed. Please install GCP CLI and try again."
    exit 1
  fi
  
  local gcp_version
  gcp_version=$(gcloud version | head -n 1 | cut -d ' ' -f 4)
  info "GCP CLI version: $gcp_version"
  
  # Check if GCP credentials are configured
  if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" >/dev/null 2>&1; then
    error "GCP credentials are not configured or invalid. Please run 'gcloud auth login' and try again."
    exit 1
  fi
}

# Initialize Terraform
function terraform_init() {
  heading "Initializing Terraform"
  
  local tfvars_file="${PROJECT_ROOT}/infra/terraform/${CLOUD_PROVIDER}/environments/${ENVIRONMENT}.tfvars"
  
  # Create environment directory if it doesn't exist
  mkdir -p "${PROJECT_ROOT}/infra/terraform/${CLOUD_PROVIDER}/environments"
  
  # Create tfvars file if it doesn't exist
  if [ ! -f "$tfvars_file" ]; then
    info "Creating default tfvars file for ${ENVIRONMENT} environment"
    
    if [ "$CLOUD_PROVIDER" = "aws" ]; then
      cat > "$tfvars_file" << EOF
# Terraform variables for ${ENVIRONMENT} environment - AWS

project_name = "skipper"
environment  = "${ENVIRONMENT}"
aws_region   = "us-west-2"

availability_zones = ["us-west-2a", "us-west-2b", "us-west-2c"]
vpc_cidr           = "10.0.0.0/16"
private_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
public_subnet_cidrs  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

kubernetes_version = "1.27"

db_instance_class     = "db.t3.${ENVIRONMENT == "prod" ? "medium" : "small"}"
db_allocated_storage  = ${ENVIRONMENT == "prod" ? "50" : "20"}
db_password           = "CHANGE_ME_BEFORE_APPLYING"

rabbitmq_instance_type = "mq.t3.${ENVIRONMENT == "prod" ? "small" : "micro"}"
rabbitmq_password      = "CHANGE_ME_BEFORE_APPLYING"

redis_node_type = "cache.t3.${ENVIRONMENT == "prod" ? "small" : "micro"}"
EOF
    elif [ "$CLOUD_PROVIDER" = "gcp" ]; then
      cat > "$tfvars_file" << EOF
# Terraform variables for ${ENVIRONMENT} environment - GCP

project_id   = "CHANGE_ME"
project_name = "skipper"
environment  = "${ENVIRONMENT}"
region       = "us-central1"
zone         = "us-central1-a"

private_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
public_subnet_cidrs  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

cluster_ipv4_cidr_block  = "10.1.0.0/16"
services_ipv4_cidr_block = "10.2.0.0/16"
master_ipv4_cidr_block   = "172.16.0.0/28"

control_plane_machine_type = "${ENVIRONMENT == "prod" ? "e2-standard-2" : "e2-medium"}"
agents_machine_type        = "${ENVIRONMENT == "prod" ? "e2-medium" : "e2-small"}"

db_tier      = "${ENVIRONMENT == "prod" ? "db-custom-2-4096" : "db-g1-small"}"
db_password  = "CHANGE_ME_BEFORE_APPLYING"

redis_memory_size_gb = ${ENVIRONMENT == "prod" ? "2" : "1"}

alert_email  = "alerts@example.com"
EOF
    fi
    
    info "Created default tfvars file: ${tfvars_file}"
    info "Please update the values in the file before applying"
  fi
  
  # Change to Terraform directory
  cd "${PROJECT_ROOT}/infra/terraform/${CLOUD_PROVIDER}"
  
  # Initialize Terraform
  terraform init
  
  success "Terraform initialized successfully"
}

# Run Terraform plan
function terraform_plan() {
  heading "Running Terraform Plan"
  
  local tfvars_file="${PROJECT_ROOT}/infra/terraform/${CLOUD_PROVIDER}/environments/${ENVIRONMENT}.tfvars"
  
  # Check if tfvars file exists
  if [ ! -f "$tfvars_file" ]; then
    error "Terraform variables file not found: ${tfvars_file}"
    exit 1
  fi
  
  # Change to Terraform directory
  cd "${PROJECT_ROOT}/infra/terraform/${CLOUD_PROVIDER}"
  
  # Run Terraform plan
  terraform plan -var-file="$tfvars_file" -out="terraform.tfplan"
  
  success "Terraform plan completed"
}

# Run Terraform apply
function terraform_apply() {
  heading "Applying Terraform Configuration"
  
  local tfvars_file="${PROJECT_ROOT}/infra/terraform/${CLOUD_PROVIDER}/environments/${ENVIRONMENT}.tfvars"
  
  # Check if tfvars file exists
  if [ ! -f "$tfvars_file" ]; then
    error "Terraform variables file not found: ${tfvars_file}"
    exit 1
  fi
  
  # Change to Terraform directory
  cd "${PROJECT_ROOT}/infra/terraform/${CLOUD_PROVIDER}"
  
  # Run Terraform apply
  if [ -f "terraform.tfplan" ]; then
    terraform apply "terraform.tfplan"
  else
    info "No plan file found, creating and applying plan..."
    terraform apply -var-file="$tfvars_file" -auto-approve
  fi
  
  success "Terraform apply completed"
  
  # Output important information
  heading "Deployment Information"
  
  if [ "$CLOUD_PROVIDER" = "aws" ]; then
    echo "Kubernetes cluster name: $(terraform output -raw gke_cluster_name 2>/dev/null || echo "N/A")"
    echo "Database endpoint: $(terraform output -raw postgres_endpoint 2>/dev/null || echo "N/A")"
    echo "Redis endpoint: $(terraform output -raw redis_endpoint 2>/dev/null || echo "N/A")"
    echo "RabbitMQ endpoint: $(terraform output -raw primary_amqp_endpoint 2>/dev/null || echo "N/A")"
    echo "Vault URL: $(terraform output -raw vault_url 2>/dev/null || echo "N/A")"
    echo "Event store bucket: $(terraform output -raw event_store_bucket_name 2>/dev/null || echo "N/A")"
  elif [ "$CLOUD_PROVIDER" = "gcp" ]; then
    echo "Kubernetes cluster name: $(terraform output -raw gke_cluster_name 2>/dev/null || echo "N/A")"
    echo "Database connection name: $(terraform output -raw postgres_instance_connection_name 2>/dev/null || echo "N/A")"
    echo "Redis host: $(terraform output -raw redis_host 2>/dev/null || echo "N/A")"
    echo "Redis port: $(terraform output -raw redis_port 2>/dev/null || echo "N/A")"
    echo "Event store bucket: $(terraform output -raw event_store_bucket 2>/dev/null || echo "N/A")"
  fi
}

# Run Terraform destroy
function terraform_destroy() {
  heading "Destroying Terraform Infrastructure"
  
  local tfvars_file="${PROJECT_ROOT}/infra/terraform/${CLOUD_PROVIDER}/environments/${ENVIRONMENT}.tfvars"
  
  # Check if tfvars file exists
  if [ ! -f "$tfvars_file" ]; then
    error "Terraform variables file not found: ${tfvars_file}"
    exit 1
  fi
  
  # Confirm destruction
  read -p "Are you sure you want to destroy the infrastructure for ${ENVIRONMENT} environment? (y/N): " -r CONFIRM
  if [[ ! $CONFIRM =~ ^[Yy]$ ]]; then
    info "Destruction cancelled"
    exit 0
  fi
  
  # Change to Terraform directory
  cd "${PROJECT_ROOT}/infra/terraform/${CLOUD_PROVIDER}"
  
  # Run Terraform destroy
  terraform destroy -var-file="$tfvars_file"
  
  success "Terraform destroy completed"
}

# Parse command line arguments
function parse_args() {
  while [[ $# -gt 0 ]]; do
    case $1 in
      --provider|-p)
        CLOUD_PROVIDER="$2"
        shift 2
        ;;
      --environment|-e)
        ENVIRONMENT="$2"
        shift 2
        ;;
      --init|-i)
        ACTION="init"
        shift
        ;;
      --plan)
        ACTION="plan"
        shift
        ;;
      --apply|-a)
        ACTION="apply"
        shift
        ;;
      --destroy|-d)
        ACTION="destroy"
        shift
        ;;
      --help|-h)
        show_help
        exit 0
        ;;
      *)
        error "Unknown option: $1"
        show_help
        exit 1
        ;;
    esac
  done
  
  # Validate cloud provider
  if [[ ! "$CLOUD_PROVIDER" =~ ^(aws|gcp)$ ]]; then
    error "Invalid cloud provider: ${CLOUD_PROVIDER}. Must be 'aws' or 'gcp'"
    exit 1
  fi
  
  # Validate environment
  if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    error "Invalid environment: ${ENVIRONMENT}. Must be 'dev', 'staging', or 'prod'"
    exit 1
  fi
}

# Show help
function show_help() {
  cat << EOF
Usage: $(basename "$0") [OPTIONS]

Manage Skipper cloud deployments using Terraform.

Options:
  -p, --provider PROVIDER    Cloud provider (aws, gcp) [default: aws]
  -e, --environment ENV      Deployment environment (dev, staging, prod) [default: dev]
  -i, --init                 Initialize Terraform
  --plan                     Generate Terraform plan
  -a, --apply                Apply Terraform changes
  -d, --destroy              Destroy infrastructure
  -h, --help                 Show this help message

Examples:
  $(basename "$0") --provider aws --environment dev --init
  $(basename "$0") --provider gcp --environment staging --plan
  $(basename "$0") -p aws -e prod -a
  $(basename "$0") -p gcp -e dev -d
EOF
}

# Main function
function main() {
  heading "Skipper Cloud Deployment Management"
  
  parse_args "$@"
  
  info "Cloud Provider: ${CLOUD_PROVIDER}"
  info "Environment: ${ENVIRONMENT}"
  info "Action: ${ACTION}"
  
  # Check required tools
  check_terraform
  
  if [ "$CLOUD_PROVIDER" = "aws" ]; then
    check_aws_cli
  elif [ "$CLOUD_PROVIDER" = "gcp" ]; then
    check_gcp_cli
  fi
  
  # Perform action
  case $ACTION in
    init)
      terraform_init
      ;;
    plan)
      terraform_init
      terraform_plan
      ;;
    apply)
      terraform_init
      terraform_plan
      terraform_apply
      ;;
    destroy)
      terraform_init
      terraform_destroy
      ;;
    *)
      error "Unknown action: ${ACTION}"
      show_help
      exit 1
      ;;
  esac
}

# Run main function
main "$@"