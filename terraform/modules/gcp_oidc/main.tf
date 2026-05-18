# In a real environment, GOOGLE_PROJECT is passed or you can define variable "gcp_project_id"
data "google_client_config" "current" {}

resource "google_iam_workload_identity_pool" "aks_pool" {
  workload_identity_pool_id = "${var.project_name}-pool"
  display_name              = "AKS OIDC Pool"
  description               = "Identity pool for AKS OIDC federation"
}

resource "google_iam_workload_identity_pool_provider" "aks_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.aks_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "${var.project_name}-provider"
  display_name                       = "AKS OIDC Provider"

  attribute_mapping = {
    "google.subject" = "assertion.sub"
  }

  oidc {
    issuer_uri = var.oidc_issuer_url
  }
}

resource "google_service_account" "cost_svc" {
  account_id   = "${var.project_name}-cost-svc"
  display_name = "CloudPulse Cost Service"
}

# Bind the service account to the specific Kubernetes Service Account subject
resource "google_service_account_iam_member" "workload_identity_binding" {
  service_account_id = google_service_account.cost_svc.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principal://iam.googleapis.com/${google_iam_workload_identity_pool.aks_pool.name}/subject/system:serviceaccount:cloudpulse:cloudpulse-sa"
}

# Grant the service account permissions to view billing
# In GCP, billing data is usually exported to BigQuery, so we grant BigQuery Data Viewer.
resource "google_project_iam_member" "bq_viewer" {
  project = data.google_client_config.current.project
  role    = "roles/bigquery.dataViewer"
  member  = "serviceAccount:${google_service_account.cost_svc.email}"
}
