# CloudPulse 🌐

> Real-time multi-cloud cost & infrastructure monitoring dashboard. Deployed on **Azure (AKS)** with unified visibility across **AWS, Azure, and GCP** accounts.

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    CloudPulse Infrastructure                      │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Azure (Deployment)                                     │   │
│  │  ┌─────────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │   Frontend  │  │ Metrics  │  │ Alerts   │          │   │
│  │  │  (React)    │  │  Service │  │ Service  │          │   │
│  │  │   nginx     │  │ FastAPI  │  │ FastAPI  │          │   │
│  │  └─────────────┘  └──────────┘  └──────────┘          │   │
│  │         │              │              │                │   │
│  │         └──────────────┼──────────────┘                │   │
│  │                  ┌─────▼─────┐                         │   │
│  │                  │ Cost Svc   │                         │   │
│  │                  │ (FastAPI)  │                         │   │
│  │                  └─────┬─────┘                         │   │
│  │  AKS Cluster           │                               │   │
│  │  ACR Registry          │                               │   │
│  └───────────────────────┼───────────────────────────────┘   │
│                          │                                    │
│   ┌──────────────────────┼──────────────────────┐            │
│   │                      │                      │            │
│   ▼                      ▼                      ▼            │
│┌────────┐          ┌────────┐          ┌────────┐          │
││  AWS   │          │ Azure  │          │  GCP   │          │
││ Cost   │          │ Cost   │          │ Cost   │          │
││ APIs   │          │ APIs   │          │ APIs   │          │
│└────────┘          └────────┘          └────────┘          │
│  (Multi-Cloud Cost Aggregation)                            │
└──────────────────────────────────────────────────────────────────┘
```

### How It Works

1. **Application** runs on Azure AKS with ACR for image storage
2. **Cost Service** aggregates billing data from AWS, Azure, and GCP APIs using **Workload Identity Federation (OIDC)**—no long-lived secrets in the cluster.
3. **Dashboard** displays unified metrics, alerts, and cost breakdown across all three clouds, secured with **Azure Entra ID (SSO)**.
4. **Zero-Trust Infrastructure**: All cloud interactions use temporary, short-lived tokens via federated trust relationships.

| Service | Port | Role |
|---|---|---|
| `metrics-svc` | 8001 | CPU/memory/network metrics for Azure resources |
| `alerts-svc` | 8002 | Threshold alerts with severity classification |
| `cost-svc` | 8003 | Multi-cloud cost aggregation (AWS + Azure + GCP) |
| `frontend` | 80 | React dashboard (nginx + API proxy) |

## Prerequisites

| Tool | Version |
|---|---|
| Terraform | ≥ 1.5 |
| Azure CLI | latest (authenticated) |
| Docker Desktop | running |
| kubectl | latest |
| helm | ≥ 3.14 |

## Quick Start

### 1. Bootstrap remote state (once)

```bash
bash scripts/bootstrap-state.sh <your-azure-subscription-id>
```

### 2. Configure variables

Edit `terraform/terraform.tfvars`:

```hcl
azure_subscription_id = "your-subscription-id"
azure_location        = "uksouth"   # e.g., eastus, westeurope, etc.
project_name          = "cloudpulse"
image_tag             = "latest"
```

### 3. Configure cloud credentials (for cost monitoring)

Set environment variables or create a `.env` file for cost-svc to monitor AWS/GCP:

```bash
# AWS
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...

# GCP (optional)
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcp-key.json
```

> Azure credentials are automatically available via AKS managed identity.

### 4. Deploy

```bash
cd terraform
terraform init
terraform apply
```

Outputs:

```
Outputs:
  azure_dashboard_url = "http://1.2.3.4"
  aks_cluster_name    = "cloudpulse-aks"
  acr_server          = "cloudpulse.azurecr.io"
```

## Cost Optimization (Auto-Shutdown)

To minimize costs, this project includes a scheduled GitHub Action (`.github/workflows/cluster-schedule.yml`) that:
*   **Starts** the AKS cluster every Monday at 08:55 UTC.
*   **Stops** the AKS cluster every Monday at 11:05 UTC.

This reduces the compute cost from ~$30/month to **~$0.40/month**, as you only pay for the VM while it is actually running during your analysis meeting.

### Monthly Cost Breakdown (Estimated)

| Component | Resource Type | Always-On | Scheduled (2h/wk) |
|---|---|---|---|
| **AKS Worker Node** | 1 x `Standard_B2s` | ~$30.37 | ~$0.40 |
| **Load Balancer** | Azure Standard LB | ~$18.00 | ~$18.00 |
| **ACR Registry** | Azure ACR (Basic) | ~$5.00 | ~$5.00 |
| **TOTAL** | | **~$53.37** | **~$23.40** |

> [!NOTE]
> Fixed costs for the Load Balancer and ACR (~$23/month) still apply to keep your IP address and images persistent.

## Local Development

```bash
docker compose up --build
```

Dashboard: http://localhost:3000
- Metrics API: http://localhost:8001/docs
- Alerts API:  http://localhost:8002/docs
- Cost API:    http://localhost:8003/docs

## CI/CD Options

### 1. GitHub Actions (Recommended)
Workflow located at `.github/workflows/deploy.yml`.

**Required Repository Secrets:**

| Secret Name | Description |
|---|---|
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID |
| `AZURE_TENANT_ID` | Azure AD tenant ID |
| `AZURE_CLIENT_ID` | Service principal client ID |
| `AZURE_CLIENT_SECRET` | Service principal secret |
| `AWS_ACCESS_KEY_ID` | (Optional) AWS credentials for IAM OIDC provisioning |
| `AWS_SECRET_ACCESS_KEY` | (Optional) AWS credentials for IAM OIDC provisioning |
| `GOOGLE_CREDENTIALS` | (Optional) GCP Service Account JSON for Workload Identity provisioning |
| `GOOGLE_PROJECT` | (Optional) GCP Project ID |

### 2. Azure DevOps
Import `.azdo/azure-pipelines.yml` into your Azure DevOps project.

**Required variable group** `cloudpulse-secrets`:

| Variable | Description |
|---|---|
| `AZURE_SUBSCRIPTION_ID` | Azure subscription |
| `AZURE_TENANT_ID` | Azure AD tenant |
| `AZURE_CLIENT_ID` | Service principal client ID |
| `AZURE_CLIENT_SECRET` | Service principal secret |
| `AWS_ACCESS_KEY_ID` | (Optional) AWS credentials for IAM OIDC provisioning |
| `AWS_SECRET_ACCESS_KEY` | (Optional) AWS credentials for IAM OIDC provisioning |
| `GOOGLE_CREDENTIALS` | (Optional) GCP Service Account JSON |
| `GOOGLE_PROJECT` | (Optional) GCP Project ID |

**Pipeline stages:**
1. **Build** — Docker images → ACR
2. **Deploy** — `terraform apply` (Provisions Infra + OIDC + Helm)
3. **Verify** — Health check all endpoints

## Project Structure

```
cloudpulse/
├── services/
│   ├── metrics-svc/   FastAPI — Azure resource metrics
│   ├── alerts-svc/    FastAPI — threshold alerts
│   └── cost-svc/      FastAPI — multi-cloud cost aggregation
├── frontend/          React + Vite dashboard
├── helm/cloudpulse/   Helm chart (all 4 workloads)
├── terraform/
│   ├── main.tf        Single entry point
│   ├── modules/aks/   AKS cluster + VNet
│   ├── modules/acr/   Azure Container Registry
│   ├── modules/aws_oidc/ AWS OIDC Trust Relationship
│   ├── modules/gcp_oidc/ GCP Workload Identity Federation
│   ├── backend.tf     Remote state configuration
│   ├── variables.tf   Input variables
│   └── outputs.tf     Output values
├── scripts/
│   ├── deploy.sh          Build + push to ACR + Helm deploy
│   └── bootstrap-state.sh Create Terraform remote state
├── .azdo/
│   └── azure-pipelines.yml
└── .github/
    └── workflows/
        └── deploy.yml
```

## Tear Down

```bash
cd terraform
terraform destroy
```
