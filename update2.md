
### 1. Azure Entra ID Authentication (SSO)
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

## Deployment (GitHub Actions)

If you do not have access to Azure DevOps for your Microsoft account, we have implemented a fallback **GitHub Actions** CI/CD pipeline!

The pipeline is located at `.github/workflows/deploy.yml`.

### Setup Instructions
Before pushing to GitHub, you must configure the following **Repository Secrets** in your GitHub repository (`Settings -> Secrets and variables -> Actions`):

| Secret Name | Description |
|---|---|
| `AZURE_SUBSCRIPTION_ID` | Your Azure Subscription ID |
| `AZURE_TENANT_ID` | Your Azure Active Directory Tenant ID |
| `AZURE_CLIENT_ID` | Service Principal Client ID for Terraform |
| `AZURE_CLIENT_SECRET` | Service Principal Secret for Terraform |
| `AWS_ACCESS_KEY_ID` | (Optional) Used by Terraform to configure IAM trust |
| `AWS_SECRET_ACCESS_KEY` | (Optional) Used by Terraform to configure IAM trust |
| `GOOGLE_CREDENTIALS` | (Optional) Raw JSON content of your GCP Service Account for IAM trust |
| `GOOGLE_PROJECT` | (Optional) GCP Project ID |

Once these secrets are configured, pushing to the `main` branch will automatically trigger the GitHub Actions workflow to build, deploy, and verify the CloudPulse application.
