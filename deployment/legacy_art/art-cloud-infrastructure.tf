# ART系統雲端基礎設施 Terraform配置
# DevOps Engineer 墨子 - 混合部署雲端架構

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.24"
    }
  }
}

# 變數定義
variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "twstock-466914"
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "asia-east1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

# Provider 配置
provider "google" {
  project = var.project_id
  region  = var.region
}

# 啟用必要的 API
resource "google_project_service" "art_apis" {
  for_each = toset([
    "run.googleapis.com",
    "container.googleapis.com",
    "compute.googleapis.com",
    "storage.googleapis.com",
    "cloudsql.googleapis.com",
    "redis.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "aiplatform.googleapis.com",
    "ml.googleapis.com"
  ])
  
  service            = each.key
  disable_on_destroy = false
}

# VPC 網路（擴展TradingAgents現有網路）
resource "google_compute_network" "art_vpc" {
  name                    = "art-hybrid-vpc"
  auto_create_subnetworks = false
  
  depends_on = [google_project_service.art_apis]
}

resource "google_compute_subnetwork" "art_training_subnet" {
  name          = "art-training-subnet"
  ip_cidr_range = "10.1.0.0/24"
  region        = var.region
  network       = google_compute_network.art_vpc.id
  
  private_ip_google_access = true
  
  secondary_ip_range {
    range_name    = "gke-pods"
    ip_cidr_range = "10.2.0.0/16"
  }
  
  secondary_ip_range {
    range_name    = "gke-services"
    ip_cidr_range = "10.3.0.0/16"
  }
}

# GKE 集群（用於GPU訓練工作負載）
resource "google_container_cluster" "art_gke" {
  name     = "art-gpu-cluster"
  location = var.region
  
  network    = google_compute_network.art_vpc.name
  subnetwork = google_compute_subnetwork.art_training_subnet.name
  
  # 移除默認節點池
  remove_default_node_pool = true
  initial_node_count       = 1
  
  # 啟用必要的功能
  enable_shielded_nodes = true
  
  # 網路配置
  ip_allocation_policy {
    cluster_secondary_range_name  = "gke-pods"
    services_secondary_range_name = "gke-services"
  }
  
  # 主節點授權網路
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = "0.0.0.0/0"
      display_name = "all"
    }
  }
  
  # 日誌和監控
  logging_service    = "logging.googleapis.com/kubernetes"
  monitoring_service = "monitoring.googleapis.com/kubernetes"
  
  depends_on = [
    google_project_service.art_apis,
    google_compute_network.art_vpc,
    google_compute_subnetwork.art_training_subnet
  ]
}

# GPU節點池（T4 GPU用於訓練）
resource "google_container_node_pool" "art_gpu_pool" {
  name       = "art-gpu-nodes"
  location   = var.region
  cluster    = google_container_cluster.art_gke.name
  node_count = 0  # 使用自動擴縮容
  
  # 自動擴縮容配置
  autoscaling {
    min_node_count = 0
    max_node_count = 3
  }
  
  # 節點配置
  node_config {
    preemptible  = true  # 使用搶佔式實例節省成本
    machine_type = "n1-standard-4"
    
    # GPU配置
    guest_accelerator {
      type  = "nvidia-tesla-t4"
      count = 1
    }
    
    # OAuth範圍
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
    
    # 標籤
    labels = {
      environment = var.environment
      workload    = "gpu-training"
    }
    
    # 污點配置（確保只有GPU工作負載調度到這些節點）
    taint {
      key    = "nvidia.com/gpu"
      value  = "true"
      effect = "NO_SCHEDULE"
    }
    
    # 元數據
    metadata = {
      disable-legacy-endpoints = "true"
    }
  }
  
  # 管理配置
  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

# CPU節點池（一般工作負載）
resource "google_container_node_pool" "art_cpu_pool" {
  name       = "art-cpu-nodes"
  location   = var.region
  cluster    = google_container_cluster.art_gke.name
  node_count = 1
  
  # 自動擴縮容配置
  autoscaling {
    min_node_count = 1
    max_node_count = 5
  }
  
  # 節點配置
  node_config {
    preemptible  = true
    machine_type = "e2-standard-2"
    
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
    
    labels = {
      environment = var.environment
      workload    = "general"
    }
    
    metadata = {
      disable-legacy-endpoints = "true"
    }
  }
  
  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

# Cloud Storage (模型存儲)
resource "google_storage_bucket" "art_models" {
  name     = "${var.project_id}-art-models"
  location = var.region
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
  
  depends_on = [google_project_service.art_apis]
}

resource "google_storage_bucket" "art_datasets" {
  name     = "${var.project_id}-art-datasets"
  location = var.region
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 180
    }
    action {
      type = "Delete"
    }
  }
}

# Artifact Registry (容器映像存儲)
resource "google_artifact_registry_repository" "art_docker" {
  location      = var.region
  repository_id = "art-docker-repo"
  description   = "ART系統Docker映像存儲庫"
  format        = "DOCKER"
  
  depends_on = [google_project_service.art_apis]
}

# Cloud SQL (元數據存儲)
resource "google_sql_database_instance" "art_metadata_db" {
  name             = "art-metadata-postgres"
  database_version = "POSTGRES_15"
  region           = var.region
  
  settings {
    tier              = "db-g1-small"
    availability_type = "ZONAL"
    disk_type         = "PD_SSD"
    disk_size         = 50
    disk_autoresize   = true
    
    backup_configuration {
      enabled                        = true
      start_time                     = "04:00"
      location                       = var.region
      point_in_time_recovery_enabled = true
      backup_retention_settings {
        retained_backups = 14
      }
    }
    
    ip_configuration {
      ipv4_enabled    = true
      private_network = google_compute_network.art_vpc.id
      require_ssl     = true
    }
    
    database_flags {
      name  = "max_connections"
      value = "200"
    }
  }
  
  deletion_protection = false
  
  depends_on = [
    google_project_service.art_apis,
    google_compute_network.art_vpc
  ]
}

# Redis (模型緩存和工作佇列)
resource "google_redis_instance" "art_redis" {
  name           = "art-model-cache"
  tier           = "STANDARD_HA"  # 高可用性
  memory_size_gb = 4
  region         = var.region
  
  authorized_network = google_compute_network.art_vpc.id
  redis_version      = "REDIS_7_0"
  display_name       = "ART Model Cache and Queue"
  
  # 持久化配置
  persistence_config {
    persistence_mode    = "RDB"
    rdb_snapshot_period = "ONE_HOUR"
  }
  
  depends_on = [
    google_project_service.art_apis,
    google_compute_network.art_vpc
  ]
}

# Cloud Run (推理服務)
resource "google_cloud_run_service" "art_inference" {
  name     = "art-inference-service"
  location = var.region
  
  template {
    spec {
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/art-docker-repo/art-inference:latest"
        
        ports {
          container_port = 8080
        }
        
        resources {
          limits = {
            cpu    = "4000m"
            memory = "8Gi"
          }
        }
        
        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }
        
        env {
          name  = "MODEL_BUCKET"
          value = google_storage_bucket.art_models.name
        }
        
        env {
          name = "REDIS_URL"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.art_redis_url.secret_id
              key  = "latest"
            }
          }
        }
      }
      
      container_concurrency = 100
      timeout_seconds       = 300
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale"      = "1"
        "autoscaling.knative.dev/maxScale"      = "10"
        "run.googleapis.com/cpu-throttling"     = "false"
        "run.googleapis.com/execution-environment" = "gen2"
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  depends_on = [
    google_project_service.art_apis,
    google_artifact_registry_repository.art_docker
  ]
}

# Secret Manager 密鑰
resource "google_secret_manager_secret" "art_secrets" {
  for_each = toset([
    "art-training-config",
    "art-model-registry-key",
    "art-redis-url",
    "art-db-connection",
    "wandb-api-key",
    "huggingface-token"
  ])
  
  secret_id = each.value
  
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
  
  depends_on = [google_project_service.art_apis]
}

resource "google_secret_manager_secret" "art_redis_url" {
  secret_id = "art-redis-url"
  
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}

# 監控和告警
resource "google_monitoring_notification_channel" "art_email" {
  display_name = "ART System Email"
  type         = "email"
  labels = {
    email_address = "art-alerts@tradingagents.com"
  }
}

resource "google_monitoring_alert_policy" "art_gpu_utilization" {
  display_name = "ART GPU High Utilization"
  combiner     = "OR"
  
  conditions {
    display_name = "GPU Utilization > 90%"
    condition_threshold {
      filter          = "resource.type=\"gce_instance\" AND metric.type=\"compute.googleapis.com/instance/accelerator/utilization\""
      comparison      = "COMPARISON_GREATER_THAN"
      threshold_value = 0.9
      duration        = "300s"
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.art_email.id]
  
  depends_on = [google_project_service.art_apis]
}

# 輸出值
output "gke_cluster_name" {
  value = google_container_cluster.art_gke.name
}

output "gke_cluster_endpoint" {
  value = google_container_cluster.art_gke.endpoint
}

output "model_bucket_name" {
  value = google_storage_bucket.art_models.name
}

output "artifact_registry_url" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/art-docker-repo"
}

output "inference_service_url" {
  value = google_cloud_run_service.art_inference.status[0].url
}

output "redis_host" {
  value = google_redis_instance.art_redis.host
}