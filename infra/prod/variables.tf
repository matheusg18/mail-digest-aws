variable "gcp_project_id" {
  type        = string
  description = "The GCP project ID."
}

variable "gcp_region" {
  type        = string
  default     = "southamerica-east1"
  description = "The GCP region for all resources."
}