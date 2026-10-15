output "namespace" {
  value = kubernetes_namespace.student.metadata[0].name
}

output "artifact_registry_repo" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.stedi.repository_id}"
}

output "etl_bucket" {
  value = google_storage_bucket.etl_source.name
}
