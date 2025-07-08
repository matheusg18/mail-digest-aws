terraform {
  backend "gcs" {
    bucket = "sumio-terraform-state-bucket"
    prefix = "prod/core"
  }
}

provider "google" {
  project = var.gcp_project_id
}

module "app" {
  source = "../modules/app"

  gcp_project_id = var.gcp_project_id
  gcp_region     = var.gcp_region
}
