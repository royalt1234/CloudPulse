

### 1. Azure Entra ID Authentication (SSO) - NEW
We have secured the CloudPulse dashboard with Enterprise Single Sign-On!
*   **Automated App Registration**: Terraform now uses the `azuread` provider to automatically register a Single Page Application (SPA) in your Azure AD tenant. You no longer need to create this manually!
*   **MSAL Integration**: The React frontend uses Microsoft's official `@azure/msal-react` library.
*   **Dynamic UI**: Unauthenticated users are presented with a premium "Sign in with Microsoft" landing page. Once authenticated, the full multi-cloud dashboard is revealed.

### 2. Cross-Cloud Identity Federation (OIDC)
We have successfully eliminated the need for long-lived AWS and GCP keys inside the Kubernetes cluster! 
*   **AKS OIDC Issuer**: We enabled the OIDC issuer on your AKS cluster.
*   **AWS IAM Federation**: Terraform now provisions an `aws_iam_openid_connect_provider` that trusts your AKS cluster, along with an `aws_iam_role`. The `cost-svc` pod automatically mounts a projected token which `boto3` exchanges for temporary credentials.
*   **GCP Workload Identity**: Terraform provisions a Google `workload_identity_pool` and `provider` linked to the AKS OIDC URL. It binds a GCP service account to your Kubernetes `cloudpulse-sa`. A custom ConfigMap injects the GCP credentials JSON file into the pod, which seamlessly points the `google-cloud-billing` SDK to the Kubernetes token.
*   **Azure Workload Identity**: We configured User Assigned Managed Identities for the cluster to seamlessly hit Azure APIs without passwords.

### 3. Multi-Cloud Cost Integration (`cost-svc`)
The Cost Service fetches **real** billing data dynamically using 100% passwordless authentication:
*   **AWS**: Uses `boto3` via Web Identity Token Federation to hit the Cost Explorer API.
*   **Azure**: Uses `CostManagementClient` via AKS Workload Identity to fetch real Resource Group usage.
*   **GCP**: Uses `google-cloud-billing` via Workload Identity Pools.

### 4. Native Azure Metrics & Alerts (`metrics-svc` & `alerts-svc`)
*   **`metrics-svc`**: Now uses the Azure Monitor SDK to dynamically discover Virtual Machines in your subscription and fetch their real `Percentage CPU` metric.
*   **`alerts-svc`**: Connects to the Azure Alerts Management API to fetch live alerts from the last 7 days.

---

## How to Run Locally

If you are running the frontend locally (`npm run dev`), you must supply the Entra ID environment variables. 
After running `terraform apply`, grab the output variables and create a `.env.local` file in the `frontend/` directory:
```bash
VITE_AZURE_CLIENT_ID="<your-entra_client_id>"
VITE_AZURE_TENANT_ID="<your-entra_tenant_id>"
```
Then run:
```bash
npm install
npm run dev
```
#######################################################

Layer 1: Automation (The "Control Plane")
GitHub Actions: The brain of the operation.
deploy.yml: Handles the terraform apply and initial setup.
cluster-schedule.yml: Manages the Monday morning cron schedule.
GitHub Secrets: Stores the bootstrap credentials for Azure, AWS, and GCP.
Layer 2: Infrastructure (Azure Foundation)
Terraform Remote State: An Azure Storage Account (rg-cloudpulse-tfstate) where the architecture state is stored.
Azure Resource Group (rg-cloudpulse-prod): Contains:
AKS Cluster: The 1-node Standard_B2s cluster.
ACR (Container Registry): Stores your 4 microservice images.
Managed Identity: The "Identity Bridge" that allows AKS to talk to Azure APIs.
Layer 3: Security & Identity (The "Secret Sauce")
This is the most important part to visualize for your presentation:

Entra ID (Azure AD):
App Registration: Secures the Frontend UI (SSO).
OIDC Federation Hub (AKS):
The AKS OIDC Issuer URL, which is trusted by:
AWS IAM: OIDC Provider + IAM Role (Cross-Cloud Trust).
GCP IAM: Workload Identity Pool + Service Account (Cross-Cloud Trust).
Layer 4: Runtime (The AKS Cluster)
Inside the cloudpulse namespace:

Ingress (nginx): The public entry point via Load Balancer.
The Pods:
frontend: Nginx + React.
metrics-svc: Hits Azure Monitor API.
alerts-svc: Hits Azure Alerts API.
cost-svc: The "Aggregator" that uses the OIDC tokens to hit AWS, Azure, and GCP simultaneously.