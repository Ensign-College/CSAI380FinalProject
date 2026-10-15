variable "project_id" {
  description = "Your GCP project ID (from Vocareum)"
  type        = string
}

variable "region" {
  description = "GCP region for Artifact Registry and GCS"
  type        = string
  default     = "us-central1"
}

variable "student_namespace" {
  description = "Your personal Kubernetes namespace, e.g. jdoe-stedi"
  type        = string
}
