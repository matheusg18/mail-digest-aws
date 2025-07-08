variable "gcp_project_id" {
  type        = string
  description = "The GCP project ID."
}

variable "gcp_region" {
  type        = string
  description = "The GCP region for all resources."
  default     = "southamerica-east1"
}

variable "dispatcher_schedule" {
  type        = string
  description = "Cron schedule for the daily dispatcher."
  default     = "0 * * * *"
}
