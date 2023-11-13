resource "google_project_iam_binding" "secret_manager_reader" {
  project = "stunt-tokens"
  role    = "roles/secretmanager.secretAccessor"

  members = [
    "serviceAccount:${google_service_account.app_engine_account.email}",
  ]
}

resource "google_project_iam_binding" "firestore_reader_writer" {
  project = "stunt-tokens"
  role    = "roles/datastore.user"

  members = [
    "serviceAccount:${google_service_account.app_engine_account.email}",
  ]
}
