resource "google_app_engine_application" "app" {
  project     = "stunt-tokens"
  location_id = "europe-central2"
}

resource "google_app_engine_standard_app_version" "myapp_v1" {
  version_id = "v1"
  service    = "stunt-tokens"
  runtime    = "python311"  # например, "nodejs10", "python37" и т.д.
  entrypoint {
    shell = "python main.py"
  }

  deployment {
    zip {
      source_url = "url-to-your-app-zip-file"
    }
  }

  env_variables = {
    # "ENV_VAR_NAME" = "value"
    # Добавьте сюда любые другие переменные окружения, которые нужны вашему приложению
  }

  service_account = google_service_account.app_engine_account.email
}
