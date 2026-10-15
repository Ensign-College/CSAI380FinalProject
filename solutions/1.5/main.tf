# Completed version of starter/terraform/main.tf (solution for the TODO(student) stub).
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

provider "kubernetes" {
  config_path = "~/.kube/config"
}

resource "kubernetes_namespace" "student" {
  metadata {
    name = var.student_namespace
    labels = {
      course = "csai380"
    }
  }
}

resource "google_artifact_registry_repository" "stedi" {
  location      = var.region
  repository_id = "${var.student_namespace}-images"
  description   = "CSAI 380 student images"
  format        = "DOCKER"
}

resource "google_storage_bucket" "etl_source" {
  name                        = "${var.project_id}-${var.student_namespace}-etl"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = true
}

# Solution to TODO(student): the service account the STEDI deployment references
resource "kubernetes_service_account" "stedi_dev_sa" {
  metadata {
    name      = "stedi-dev-sa"
    namespace = kubernetes_namespace.student.metadata[0].name
  }
}
