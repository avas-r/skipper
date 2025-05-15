# Event Store Module for Skipper infrastructure using S3

# Create S3 bucket for event store
resource "aws_s3_bucket" "event_store" {
  bucket = var.bucket_name
  
  tags = var.tags
}

# Configure bucket versioning
resource "aws_s3_bucket_versioning" "event_store" {
  bucket = aws_s3_bucket.event_store.id
  
  versioning_configuration {
    status = var.versioning ? "Enabled" : "Suspended"
  }
}

# Configure server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "event_store" {
  bucket = aws_s3_bucket.event_store.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Configure lifecycle rules
resource "aws_s3_bucket_lifecycle_configuration" "event_store" {
  count  = length(var.lifecycle_rules) > 0 ? 1 : 0
  bucket = aws_s3_bucket.event_store.id
  
  dynamic "rule" {
    for_each = var.lifecycle_rules
    
    content {
      id     = rule.value.id
      status = rule.value.enabled ? "Enabled" : "Disabled"
      
      dynamic "transition" {
        for_each = rule.value.transition != null ? rule.value.transition : []
        
        content {
          days          = transition.value.days
          storage_class = transition.value.storage_class
        }
      }
      
      dynamic "expiration" {
        for_each = rule.value.expiration != null ? [rule.value.expiration] : []
        
        content {
          days = expiration.value.days
        }
      }
    }
  }
}

# Configure bucket policy for restricted access
resource "aws_s3_bucket_policy" "event_store" {
  bucket = aws_s3_bucket.event_store.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyUnencryptedObjectUploads"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:PutObject"
        Resource  = "${aws_s3_bucket.event_store.arn}/*"
        Condition = {
          StringNotEquals = {
            "s3:x-amz-server-side-encryption" = "AES256"
          }
        }
      },
      {
        Sid       = "DenyInsecureConnections"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource  = "${aws_s3_bucket.event_store.arn}/*"
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}

# Create IAM policy for accessing the event store
resource "aws_iam_policy" "event_store_access" {
  name        = "${var.bucket_name}-access"
  description = "Policy for accessing the ${var.bucket_name} event store"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "ListBucket"
        Effect   = "Allow"
        Action   = [
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = aws_s3_bucket.event_store.arn
      },
      {
        Sid      = "ReadWriteObjects"
        Effect   = "Allow"
        Action   = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.event_store.arn}/*"
      }
    ]
  })
  
  tags = var.tags
}

# Outputs
output "bucket_name" {
  value = aws_s3_bucket.event_store.id
}

output "bucket_arn" {
  value = aws_s3_bucket.event_store.arn
}

output "bucket_domain_name" {
  value = aws_s3_bucket.event_store.bucket_domain_name
}

output "access_policy_arn" {
  value = aws_iam_policy.event_store_access.arn
}