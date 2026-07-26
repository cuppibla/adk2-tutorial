locals {
  services = [
    "aiplatform.googleapis.com",
    "cloudresourcemanager.googleapis.com"
  ]
}

resource "google_project_service" "enabled_services" {
  for_each           = toset(local.services)
  project            = var.gcp_project_id
  service            = each.value
  disable_on_destroy = false
}
