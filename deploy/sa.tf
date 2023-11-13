resource "google_service_account" "app_engine_account" {
  account_id   = "stunt-tokens-sa"
  display_name = "Stunt Tokens App Engine Service Account"
}
