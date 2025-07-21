# ==============================================================================
# GCP PROVIDER CONFIGURATION
#
# Configures the Google Cloud provider with the project and region.
# ==============================================================================
provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# ==============================================================================
# NETWORKING & EVENTING RESOURCES (PUB/SUB)
#
# Defines the messaging backbone of the application. The main topic receives
# job requests, and the DLQ topic holds messages that fail processing.
# ==============================================================================
resource "google_pubsub_topic" "summary_jobs" {
  name    = "mail-digest-summary-jobs"
  project = var.gcp_project_id
}

resource "google_pubsub_topic" "summary_jobs_dlq" {
  name    = "mail-digest-summary-jobs-dlq"
  project = var.gcp_project_id
}

resource "google_pubsub_subscription" "summary_jobs_subscription" {
  name    = "mail-digest-summary-jobs-subscription"
  topic   = google_pubsub_topic.summary_jobs.name
  project = var.gcp_project_id

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.summary_jobs_dlq.id
    max_delivery_attempts = 5
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  ack_deadline_seconds = 600
}

# Subscription for the Dead Letter Queue topic
resource "google_pubsub_subscription" "summary_jobs_dlq_subscription" {
  name    = "mail-digest-summary-jobs-dlq-subscription"
  topic   = google_pubsub_topic.summary_jobs_dlq.name
  project = var.gcp_project_id

  # Retain messages for 7 days
  message_retention_duration = "604800s"
  ack_deadline_seconds       = 600
}

# ==============================================================================
# IAM & SERVICE ACCOUNTS
#
# Defines dedicated "robot" users for our services, following the principle of
# least privilege. Each service account will only have the permissions it needs.
# ==============================================================================
resource "google_service_account" "dispatcher_sa" {
  project      = var.gcp_project_id
  account_id   = "dispatcher-sa"
  display_name = "Sumio - Summary Dispatcher SA"
}

resource "google_service_account" "worker_sa" {
  project      = var.gcp_project_id
  account_id   = "worker-sa"
  display_name = "Sumio - Summary Worker SA"
}

# Service account for Telegram Webhook
resource "google_service_account" "telegram_webhook_sa" {
  project      = var.gcp_project_id
  account_id   = "telegram-webhook-sa"
  display_name = "Sumio - Telegram Webhook SA"
}

# ==============================================================================
# SECRETS MANAGEMENT (SECRET MANAGER)
#
# These blocks create the secure containers for your application secrets.
# The actual secret values must be added manually via the GCP console or gcloud CLI.
# ==============================================================================
resource "google_secret_manager_secret" "secrets" {
  for_each = toset([
    "SUPABASE_URL",
    "SUPABASE_SERVICE_KEY",
    "OPENAI_API_KEY",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_WEBHOOK_SECRET_TOKEN",
    "TOKEN_ENCRYPTION_KEY"
  ])

  project   = var.gcp_project_id
  secret_id = each.key

  replication {
    auto {}
  }
}

# ==============================================================================
# IAM FOR SECRETS & SERVICES
#
# Grants the service accounts the specific permissions they need to access
# secrets and other GCP services.
# ==============================================================================

# Grant the Dispatcher SA rights to publish to the Pub/Sub topic.
resource "google_project_iam_member" "dispatcher_pubsub_publisher" {
  project = var.gcp_project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.dispatcher_sa.email}"
}

# Grant the Worker SA rights to publish to the DLQ topic (for failed messages)
resource "google_project_iam_member" "worker_pubsub_publisher" {
  project = var.gcp_project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.worker_sa.email}"
}

# Get project number for Pub/Sub service account
data "google_project" "project" {
  project_id = var.gcp_project_id
}

# Grant Pub/Sub service account Editor role on DLQ topic
resource "google_pubsub_topic_iam_member" "dlq_topic_editor" {
  project = var.gcp_project_id
  topic   = google_pubsub_topic.summary_jobs_dlq.name
  role    = "roles/editor"
  member  = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

# Grant Pub/Sub service account Subscriber role on DLQ subscription
resource "google_pubsub_subscription_iam_member" "dlq_subscription_subscriber" {
  project      = var.gcp_project_id
  subscription = google_pubsub_subscription.summary_jobs_dlq_subscription.name
  role         = "roles/pubsub.subscriber"
  member       = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

# Grant Pub/Sub service account Subscriber role on main subscription (required for DLQ forwarding)
resource "google_pubsub_subscription_iam_member" "main_subscription_subscriber" {
  project      = var.gcp_project_id
  subscription = google_pubsub_subscription.summary_jobs_subscription.name
  role         = "roles/pubsub.subscriber"
  member       = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

# Grant the Dispatcher SA access to the secrets it needs.
resource "google_secret_manager_secret_iam_member" "dispatcher_secret_access" {
  for_each = toset([
    "SUPABASE_URL",
    "SUPABASE_SERVICE_KEY",
  ])

  project   = var.gcp_project_id
  secret_id = google_secret_manager_secret.secrets[each.key].secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.dispatcher_sa.email}"
}

# Grant the Worker SA access to all application secrets.
resource "google_secret_manager_secret_iam_member" "worker_secret_access" {
  for_each = google_secret_manager_secret.secrets

  project   = var.gcp_project_id
  secret_id = each.value.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.worker_sa.email}"
}

# Grant the Telegram Webhook SA access to all application secrets.
resource "google_secret_manager_secret_iam_member" "telegram_webhook_secret_access" {
  for_each = toset([
    "SUPABASE_URL",
    "SUPABASE_SERVICE_KEY",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_WEBHOOK_SECRET_TOKEN",
  ])

  project   = var.gcp_project_id
  secret_id = google_secret_manager_secret.secrets[each.key].secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.telegram_webhook_sa.email}"
}

# ==============================================================================
# FUNCTION SOURCE CODE PREPARATION
#
# Packages the application source code from the `src` directory into a zip
# file and uploads it to a GCS bucket for deployment to Cloud Functions.
# ==============================================================================
resource "google_storage_bucket" "functions_source_bucket" {
  project                     = var.gcp_project_id
  name                        = "${var.gcp_project_id}-functions-source-code"
  location                    = var.gcp_region
  uniform_bucket_level_access = true
}

data "archive_file" "dispatcher_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../../../build/dispatcher"
  output_path = "${path.module}/dispatcher.zip"
  excludes    = ["**/__pycache__", "**/*.pyc"]
}

data "archive_file" "worker_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../../../build/worker"
  output_path = "${path.module}/worker.zip"
  excludes    = ["**/__pycache__", "**/*.pyc"]
}

data "archive_file" "telegram_webhook_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../../../build/telegram_webhook"
  output_path = "${path.module}/telegram_webhook.zip"
  excludes    = ["**/__pycache__", "**/*.pyc"]
}

resource "google_storage_bucket_object" "dispatcher_archive" {
  name   = "dispatcher-${data.archive_file.dispatcher_zip.output_md5}.zip"
  bucket = google_storage_bucket.functions_source_bucket.name
  source = data.archive_file.dispatcher_zip.output_path
}

resource "google_storage_bucket_object" "worker_archive" {
  name   = "worker-${data.archive_file.worker_zip.output_md5}.zip"
  bucket = google_storage_bucket.functions_source_bucket.name
  source = data.archive_file.worker_zip.output_path
}

resource "google_storage_bucket_object" "telegram_webhook_archive" {
  name   = "telegram_webhook-${data.archive_file.telegram_webhook_zip.output_md5}.zip"
  bucket = google_storage_bucket.functions_source_bucket.name
  source = data.archive_file.telegram_webhook_zip.output_path
}

# ==============================================================================
# CLOUD FUNCTIONS (SERVERLESS COMPUTE)
# ==============================================================================

# 1. Summary Dispatcher Function (Triggered by Scheduler)
# ------------------------------------------------------------------------------
resource "google_cloudfunctions2_function" "summary_dispatcher_function" {
  project  = var.gcp_project_id
  name     = "summary-dispatcher"
  location = var.gcp_region

  build_config {
    runtime     = "python313"
    entry_point = "handler"
    source {
      storage_source {
        bucket = google_storage_bucket.functions_source_bucket.name
        object = google_storage_bucket_object.dispatcher_archive.name
      }
    }
  }

  service_config {
    max_instance_count    = 2
    min_instance_count    = 0
    available_memory      = "256Mi"
    timeout_seconds       = 300
    service_account_email = google_service_account.dispatcher_sa.email

    # Regular environment variables
    environment_variables = {
      GCP_PROJECT     = var.gcp_project_id
      PUBSUB_TOPIC_ID = google_pubsub_topic.summary_jobs.name
      LOG_FORMAT      = "json"
    }

    # Secret Manager secrets as environment variables
    secret_environment_variables {
      key        = "SUPABASE_URL"
      project_id = var.gcp_project_id
      secret     = google_secret_manager_secret.secrets["SUPABASE_URL"].secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "SUPABASE_SERVICE_KEY"
      project_id = var.gcp_project_id
      secret     = google_secret_manager_secret.secrets["SUPABASE_SERVICE_KEY"].secret_id
      version    = "latest"
    }
  }
}

# 2. Summary Worker Function (Triggered by Pub/Sub)
# ------------------------------------------------------------------------------
resource "google_cloudfunctions2_function" "summary_worker_function" {
  project  = var.gcp_project_id
  name     = "summary-worker"
  location = var.gcp_region

  build_config {
    runtime     = "python313"
    entry_point = "handler"
    source {
      storage_source {
        bucket = google_storage_bucket.functions_source_bucket.name
        object = google_storage_bucket_object.worker_archive.name
      }
    }
  }

  service_config {
    max_instance_count    = 10
    min_instance_count    = 0
    available_memory      = "512Mi"
    timeout_seconds       = 540
    service_account_email = google_service_account.worker_sa.email

    # Regular environment variables
    environment_variables = {
      GCP_PROJECT = var.gcp_project_id
      LOG_FORMAT  = "json"
    }

    # All Secret Manager secrets as environment variables
    secret_environment_variables {
      key        = "SUPABASE_URL"
      project_id = var.gcp_project_id
      secret     = google_secret_manager_secret.secrets["SUPABASE_URL"].secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "SUPABASE_SERVICE_KEY"
      project_id = var.gcp_project_id
      secret     = google_secret_manager_secret.secrets["SUPABASE_SERVICE_KEY"].secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "OPENAI_API_KEY"
      project_id = var.gcp_project_id
      secret     = google_secret_manager_secret.secrets["OPENAI_API_KEY"].secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "GOOGLE_CLIENT_ID"
      project_id = var.gcp_project_id
      secret     = google_secret_manager_secret.secrets["GOOGLE_CLIENT_ID"].secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "GOOGLE_CLIENT_SECRET"
      project_id = var.gcp_project_id
      secret     = google_secret_manager_secret.secrets["GOOGLE_CLIENT_SECRET"].secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "TELEGRAM_BOT_TOKEN"
      project_id = var.gcp_project_id
      secret     = google_secret_manager_secret.secrets["TELEGRAM_BOT_TOKEN"].secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "TOKEN_ENCRYPTION_KEY"
      project_id = var.gcp_project_id
      secret     = google_secret_manager_secret.secrets["TOKEN_ENCRYPTION_KEY"].secret_id
      version    = "latest"
    }
  }

  event_trigger {
    trigger_region = var.gcp_region
    event_type     = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic   = google_pubsub_topic.summary_jobs.id
    retry_policy   = "RETRY_POLICY_RETRY"
  }
}

# 3. Telegram Webhook Function (Triggered by HTTP)
# ------------------------------------------------------------------------------
resource "google_cloudfunctions2_function" "telegram_webhook_function" {
  project  = var.gcp_project_id
  name     = "telegram-webhook"
  location = var.gcp_region

  build_config {
    runtime     = "python313"
    entry_point = "handler"
    source {
      storage_source {
        bucket = google_storage_bucket.functions_source_bucket.name
        object = google_storage_bucket_object.telegram_webhook_archive.name
      }
    }
  }

  service_config {
    max_instance_count             = 5
    min_instance_count             = 0
    available_memory               = "256Mi"
    timeout_seconds                = 60
    all_traffic_on_latest_revision = true
    service_account_email          = google_service_account.telegram_webhook_sa.email

    # Regular environment variables
    environment_variables = {
      GCP_PROJECT = var.gcp_project_id
      LOG_FORMAT  = "json"
    }

    # Secrets needed for Telegram webhook
    secret_environment_variables {
      key        = "TELEGRAM_BOT_TOKEN"
      project_id = var.gcp_project_id
      secret     = google_secret_manager_secret.secrets["TELEGRAM_BOT_TOKEN"].secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "TELEGRAM_WEBHOOK_SECRET_TOKEN"
      project_id = var.gcp_project_id
      secret     = google_secret_manager_secret.secrets["TELEGRAM_WEBHOOK_SECRET_TOKEN"].secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "SUPABASE_URL"
      project_id = var.gcp_project_id
      secret     = google_secret_manager_secret.secrets["SUPABASE_URL"].secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "SUPABASE_SERVICE_KEY"
      project_id = var.gcp_project_id
      secret     = google_secret_manager_secret.secrets["SUPABASE_SERVICE_KEY"].secret_id
      version    = "latest"
    }
  }
}

# Make the telegram_webhook function publicly accessible
resource "google_cloud_run_service_iam_member" "telegram_webhook_invoker" {
  project  = google_cloudfunctions2_function.telegram_webhook_function.project
  location = google_cloudfunctions2_function.telegram_webhook_function.location
  service  = google_cloudfunctions2_function.telegram_webhook_function.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Allow the Cloud Scheduler to invoke the summary_dispatcher function
resource "google_cloud_run_service_iam_member" "dispatcher_invoker" {
  project  = google_cloudfunctions2_function.summary_dispatcher_function.project
  location = google_cloudfunctions2_function.summary_dispatcher_function.location
  service  = google_cloudfunctions2_function.summary_dispatcher_function.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.dispatcher_sa.email}"
}

# ==============================================================================
# SCHEDULER (CRON JOB)
#
# Triggers the entire process on a schedule.
# ==============================================================================
resource "google_cloud_scheduler_job" "dispatcher_job" {
  project     = var.gcp_project_id
  name        = "trigger-summary-dispatcher"
  description = "Triggers the summary dispatcher function"
  schedule    = "0 * * * *"
  time_zone   = "UTC"

  http_target {
    uri         = google_cloudfunctions2_function.summary_dispatcher_function.service_config[0].uri
    http_method = "POST"

    # Authenticates the scheduler's request to the function using the dispatcher's SA
    oidc_token {
      service_account_email = google_service_account.dispatcher_sa.email
    }
  }
}
