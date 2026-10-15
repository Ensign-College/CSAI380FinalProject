terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.23"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Assumes you have run: gcloud container clusters get-credentials <cluster-name> --region <region>
provider "kubernetes" {
  config_path = "~/.kube/config"
}

# Your personal namespace — all of your weekly work lives here
resource "kubernetes_namespace" "student" {
  metadata {
    name = var.student_namespace
    labels = {
      course = "csai380"
    }
  }
}

# Artifact Registry repository for your Docker images
resource "google_artifact_registry_repository" "stedi" {
  location      = var.region
  repository_id = "${var.student_namespace}-images"
  description   = "CSAI 380 student images"
  format        = "DOCKER"
}

# GCS bucket used as the ETL data source in week 3
resource "google_storage_bucket" "etl_source" {
  name                        = "${var.project_id}-${var.student_namespace}-etl"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = true
}

# TODO(student): week 1 — add a kubernetes_service_account resource named
# "stedi-dev-sa" in your namespace. The STEDI deployment references it.
