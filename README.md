# CloudPulse 🌐

> Real-time multi-cloud cost & infrastructure monitoring dashboard. Deployed on **Azure Kubernetes Service (AKS)** with unified visibility across **AWS, Azure, and GCP** — secured with **HTTPS**, **Entra ID SSO**, and **zero-trust cross-cloud identity federation**.

**Live**: [https://cloudpulse.itclabs.live](https://cloudpulse.itclabs.live)

---

## Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│                      CloudPulse Infrastructure                        │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Azure AKS Cluster (cloudpulse namespace)                    │    │
│  │                                                              │    │
│  │  nginx-ingress (LoadBalancer)                                │    │
│  │  cert-manager + Let's Encrypt (TLS)                          │    │
│  │  ┌───────────┐  ┌───────────┐  ┌──────────┐  ┌──────────┐ │    │
│  │  │ Frontend  │  │ Metrics   │  │ Alerts   │  │  Cost    │ │    │
│  │  │ React+    │  │  Service  │  │ Service  │  │ Service  │ │    │
│  │  │ Nginx     │  │ FastAPI   │  │ FastAPI  │  │ FastAPI  │ │    │
│  │  └───────────┘  └───────────┘  └──────────┘  └──────────┘ │    │
│  │       │              │              │              │        │    │
│  │       └──────────────┴──────────────┴──────────────┘        │    │
│  │                           │                                  │    │
│  │  Workload Identity (OIDC Federation)                        │    │
│  └──────────────────────────┼───────────────────────────────────┘    │
│                              │                                        │
│     ┌────────────────────────┼────────────────────────┐              │
│     │                        │                        │              │
│     ▼                        ▼                        ▼              │
│ ┌────────┐            ┌────────┐            ┌────────┐              │
│ │  AWS   │            │ Azure  │            │  GCP   │              │
│ │ Cost   │            │ Cost + │            │ Cost   │              │
│ │Explorer│            │Monitor │            │Billing │              │
│ └────────┘            └────────┘            └────────┘              │
└───────────────────────────────────────────────────────────────────────┘
```

### How It Works

1. **Application** runs on AKS with images stored in Azure Container Registry (ACR).
2. **Authentication** is handled by Microsoft Entra ID (Azure AD) SSO — unauthenticated users see a sign-in page; authenticated users get the full dashboard.
3. **Cost Service** aggregates billing data from AWS, Azure, and GCP using **Workload Identity Federation (OIDC)** — no long-lived secrets in the cluster.
4. **Metrics & Alerts** are fetched from Azure Monitor and Azure Alerts Management APIs via Managed Identity.
5. **TLS/HTTPS** is automated via cert-manager with Let's Encrypt certificates.
6. **Theme Switching** — the UI supports both dark and light themes, togglable from the login page and the dashboard header.

### Services

| Service | Port | Role |
|---|---|---|
| `frontend` | 80 | React SPA dashboard (nginx reverse proxy + Entra ID auth) |
| `metrics-svc` | 8001 | CPU/memory/disk metrics for AWS, Azure, and GCP resources |
| `alerts-svc` | 8002 | Threshold alerts with severity classification (Critical/Warning/Info) |
| `cost-svc` | 8003 | Multi-cloud cost aggregation (AWS + Azure + GCP via OIDC) |

---

## Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Terraform | ≥ 1.5 | Infrastructure provisioning |
| Azure CLI | latest | Azure authentication |
| Docker Desktop | running | Image building |
| kubectl | latest | Kubernetes management |
| Helm | ≥ 3.14 | Chart deployments |
| A DNS domain | — | Required for HTTPS (e.g. `cloudpulse.itclabs.live`) |

---

## Quick Start

### 1. Bootstrap remote state (once)

```bash
bash scripts/bootstrap-state.sh <your-azure-subscription-id>
```

This creates an Azure Storage Account for Terraform state.

### 2. Configure variables

Edit `terraform/terraform.tfvars`:

```hcl
project_name          = "cloudpulse"
azure_location        = "westeurope"
azure_subscription_id = "your-subscription-id"
azure_tenant_id       = "your-tenant-id"
kubernetes_version    = "1.34.5"
azure_node_vm_size    = "standard_b4ls_v2"
node_count            = 1
image_tag             = "latest"
```

### 3. Deploy

```bash
cd terraform
terraform init
terraform apply
```

The `deploy.sh` script (called by Terraform) automatically:
1. Builds and pushes all 4 Docker images to ACR
2. Installs **nginx-ingress** controller on AKS
3. Installs **cert-manager** for automated TLS
4. Deploys the **CloudPulse Helm chart** with TLS, ClusterIssuer, and Entra ID configuration
5. Waits for the LoadBalancer IP

Terraform outputs:

```
azure_dashboard_url      = "https://cloudpulse.itclabs.live"
aks_cluster_name         = "cloudpulse-aks"
acr_server               = "cloudpulseacr<hash>.azurecr.io"
entra_client_id          = "<app-client-id>"
azure_workload_client_id = "<workload-identity-client-id>"
```

### 4. DNS Setup (required for HTTPS)

Point your domain's DNS A record to the Load Balancer IP:

```
cloudpulse.itclabs.live  →  A  →  <load-balancer-ip>
```

cert-manager will automatically issue a Let's Encrypt certificate once DNS propagates.

> [!NOTE]
> If the cert-manager HTTP-01 challenge fails, ensure the Azure LB health probe is configured correctly:
> ```bash
> kubectl annotate service ingress-nginx-controller -n ingress-nginx \
>   service.beta.kubernetes.io/azure-load-balancer-health-probe-request-path=/healthz
> ```

---

## Security Architecture

### Entra ID Authentication (SSO)

- Terraform automatically registers a **Single Page Application** in Azure AD via the `azuread` provider.
- The React frontend uses `@azure/msal-react` for Microsoft SSO.
- Unauthenticated users see a premium sign-in page; authenticated users get the full dashboard.

### Cross-Cloud Identity Federation (OIDC)

All cloud access uses **temporary, short-lived tokens** — zero stored secrets.

| Cloud | Federation Method | What It Accesses |
|---|---|---|
| **Azure** | AKS Managed Identity | Monitor API, Alerts API, Cost Management |
| **AWS** | IAM OIDC Provider → IAM Role | Cost Explorer API |
| **GCP** | Workload Identity Pool → Service Account | Cloud Billing API |

### TLS / HTTPS

- **cert-manager** v1.20+ is installed on the cluster.
- A `ClusterIssuer` (`letsencrypt-prod`) handles automatic certificate issuance via HTTP-01 challenges.
- The ingress enforces `ssl-redirect: "true"` — all HTTP traffic is redirected to HTTPS.
- Certificate renewal is fully automated.

---

## Cost Optimization (Auto-Shutdown)

A GitHub Action (`.github/workflows/cluster-schedule.yml`) manages AKS scheduling:

- **Starts** the cluster every Monday at 08:55 UTC
- **Stops** the cluster every Monday at 11:05 UTC
- Can be triggered manually via `workflow_dispatch`

### Monthly Cost Breakdown (Estimated)

| Component | Resource Type | Always-On | Scheduled (2h/wk) |
|---|---|---|---|
| **AKS Worker Node** | 1 × `standard_b4ls_v2` | ~$30.37 | ~$0.40 |
| **Load Balancer** | Azure Standard LB | ~$18.00 | ~$18.00 |
| **ACR Registry** | Azure ACR (Basic) | ~$5.00 | ~$5.00 |
| **TOTAL** | | **~$53.37** | **~$23.40** |

> [!NOTE]
> Fixed costs for the Load Balancer and ACR (~$23/month) still apply to keep your public IP and container images persistent.

---

## Local Development

### Docker Compose

```bash
docker compose up --build
```

| Endpoint | URL |
|---|---|
| Dashboard | http://localhost:3000 |
| Metrics API (Swagger) | http://localhost:8001/docs |
| Alerts API (Swagger) | http://localhost:8002/docs |
| Cost API (Swagger) | http://localhost:8003/docs |

### Frontend Only (Vite dev server)

After `terraform apply`, grab the Entra ID outputs and create `frontend/.env.local`:

```bash
VITE_AZURE_CLIENT_ID="<entra_client_id output>"
VITE_AZURE_TENANT_ID="<entra_tenant_id output>"
```

```bash
cd frontend
npm install
npm run dev
```

---

## UI Features

- **Multi-Cloud Dashboard**: Unified view of AWS, Azure, and GCP resources, costs, and alerts
- **Cloud Filter Tabs**: Toggle between All Clouds, AWS, Azure, and GCP
- **Theme Switcher**: Dark/Light mode toggle (persisted in localStorage)
- **Real-Time Refresh**: Auto-refreshes every 10 seconds with live indicator
- **Resource Health Cards**: CPU, memory, and disk utilization with color-coded bars
- **Cost Breakdown**: Per-cloud spend with service-level detail and budget tracking
- **Alert Feed**: Severity-classified alerts (Critical/Warning/Info) with one-click acknowledgment
- **Entra ID SSO**: Secure login via Microsoft with a modern glassmorphism sign-in page

---

## CI/CD

### GitHub Actions

| Workflow | File | Purpose |
|---|---|---|
| **Deploy** | `.github/workflows/deploy.yml` | Full `terraform apply` pipeline |
| **Cluster Schedule** | `.github/workflows/cluster-schedule.yml` | Auto start/stop AKS on schedule |

**Required Repository Secrets:**

| Secret Name | Description |
|---|---|
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID |
| `AZURE_TENANT_ID` | Azure AD tenant ID |
| `AZURE_CLIENT_ID` | Service principal client ID |
| `AZURE_CLIENT_SECRET` | Service principal secret |
| `AWS_ACCESS_KEY_ID` | *(Optional)* AWS credentials for OIDC provisioning |
| `AWS_SECRET_ACCESS_KEY` | *(Optional)* AWS credentials for OIDC provisioning |
| `GOOGLE_CREDENTIALS` | *(Optional)* GCP Service Account JSON |
| `GOOGLE_PROJECT` | *(Optional)* GCP Project ID |

### Azure DevOps

Import `.azdo/azure-pipelines.yml` into your Azure DevOps project with a `cloudpulse-secrets` variable group containing the same secrets above.

---

## Project Structure

```
cloudpulse/
├── frontend/                React + Vite dashboard (Entra ID SSO)
│   ├── src/
│   │   ├── App.jsx          Root component (theme + data fetching)
│   │   ├── components/
│   │   │   ├── Login.jsx    SSO login page (glassmorphism + theme toggle)
│   │   │   ├── Header.jsx   Nav bar (cloud tabs, theme, live badge)
│   │   │   ├── Dashboard.jsx Main layout (stats, charts, costs)
│   │   │   ├── MetricsPanel.jsx  Resource health cards
│   │   │   ├── ChartPanel.jsx    CPU/cost charts (Recharts)
│   │   │   ├── AlertFeed.jsx     Alert list with acknowledge
│   │   │   └── CostPanel.jsx     Per-cloud cost breakdown
│   │   ├── services/api.js  API client (metrics, alerts, cost)
│   │   ├── authConfig.js    MSAL configuration
│   │   └── index.css        Design system (dark/light themes)
│   └── Dockerfile
├── services/
│   ├── metrics-svc/         FastAPI — AWS/Azure/GCP resource metrics
│   ├── alerts-svc/          FastAPI — threshold alerts
│   └── cost-svc/            FastAPI — multi-cloud cost aggregation
├── helm/cloudpulse/
│   ├── Chart.yaml
│   ├── values.yaml          Default values (TLS, replicas, resources)
│   ├── values-azure.yaml    Azure-specific overrides
│   └── templates/
│       ├── deployments_new.yaml   All 4 workloads
│       ├── services.yaml          ClusterIP services
│       ├── ingress.yaml           TLS-enabled ingress
│       ├── clusterissuer.yaml     Let's Encrypt ClusterIssuer
│       ├── serviceaccount.yaml    Workload Identity SA
│       └── gcp-configmap.yaml     GCP credential config
├── terraform/
│   ├── main.tf              Entry point (AKS, ACR, Entra ID, OIDC, build+deploy)
│   ├── modules/
│   │   ├── aks/             AKS cluster + VNet + OIDC issuer
│   │   └── acr/             Azure Container Registry
│   ├── backend.tf           Remote state (Azure Storage)
│   ├── variables.tf         Input variables
│   ├── outputs.tf           Dashboard URL, cluster name, client IDs
│   └── terraform.tfvars     Your configuration
├── scripts/
│   ├── deploy.sh            Build → ACR → cert-manager → Helm deploy
│   └── bootstrap-state.sh   Create Terraform remote state
├── .github/workflows/
│   ├── deploy.yml           CI/CD deployment pipeline
│   └── cluster-schedule.yml AKS auto start/stop schedule
├── .azdo/
│   └── azure-pipelines.yml  Azure DevOps pipeline
├── docker-compose.yml       Local development
└── .env.example             Environment variable template
```

---

## Troubleshooting

### Certificate not issuing

```bash
# Check certificate status
kubectl get certificate -n cloudpulse
kubectl describe certificate cloudpulse-tls -n cloudpulse

# Check cert-manager logs
kubectl logs -n cert-manager deploy/cert-manager

# Check ACME challenge solver
kubectl get ingress -n cloudpulse
```

### Azure LB health probe marking pods as unhealthy

By default, Azure's HTTP health probe expects a `200 OK`. If the nginx ingress default backend returns `404`, the LB stops routing traffic. Fix:

```bash
kubectl annotate service ingress-nginx-controller -n ingress-nginx \
  service.beta.kubernetes.io/azure-load-balancer-health-probe-request-path=/healthz
```

### Blank page after login

Ensure the metrics API returns resources with the correct nested structure:

```json
{
  "id": "vm-01",
  "name": "node-1",
  "type": "Virtual Machine",
  "cloud": "Azure",
  "metrics": {
    "cpu_percent": 65.4,
    "memory_percent": 72.1,
    "disk_percent": 38.9
  },
  "status": "Running"
}
```

The frontend destructures `resource.metrics.cpu_percent` — flat structures will crash React.

### Force rolling restart (new images, same tag)

The Helm chart includes a `rollout-trigger: {{ randAlphaNum 8 }}` annotation that forces a rolling restart on every `helm upgrade`, even when the image tag hasn't changed.

---

## Tear Down

```bash
cd terraform
terraform destroy
```

This removes all Azure resources (AKS, ACR, Entra ID app, managed identities, role assignments).
