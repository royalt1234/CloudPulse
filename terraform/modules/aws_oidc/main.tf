# The audience for Azure Workload Identity is typically "api://AzureADTokenExchange"
resource "aws_iam_openid_connect_provider" "aks" {
  url = var.oidc_issuer_url

  client_id_list = [
    "api://AzureADTokenExchange",
    "sts.amazonaws.com"
  ]

  # AWS requires the thumbprint of the top-level CA that signed the OIDC issuer certificate.
  # The thumbprint for Azure AD OIDC is known/stable, but can be retrieved via TLS if needed.
  # Using a common known thumbprint for Azure OIDC (subject to change, but generally stable).
  # Actually, as of 2023, AWS allows OIDC providers to auto-fetch thumbprints if you leave it empty or provide dummy,
  # but terraform requires it. We'll provide the standard DigiCert root thumbprint that signs *.blob.core.windows.net
  thumbprint_list = ["9e99a48a9960b14926bb7f3b02e22da2b0ab7280"]
}

data "aws_iam_policy_document" "assume_role_policy" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.aks.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(var.oidc_issuer_url, "https://", "")}:aud"
      values   = ["api://AzureADTokenExchange", "sts.amazonaws.com"]
    }

    # Restrict to the specific Kubernetes ServiceAccount namespace/name
    condition {
      test     = "StringEquals"
      variable = "${replace(var.oidc_issuer_url, "https://", "")}:sub"
      values   = ["system:serviceaccount:cloudpulse:cost-svc-sa"]
    }
  }
}

resource "aws_iam_role" "cost_svc" {
  name               = "${var.project_name}-cost-svc-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role_policy.json
}

resource "aws_iam_role_policy_attachment" "cost_explorer" {
  role       = aws_iam_role.cost_svc.name
  policy_arn = "arn:aws:iam::aws:policy/AWSCostAndUsageReportRead"
}

resource "aws_iam_role_policy" "ce_inline" {
  name = "cost-explorer-access"
  role = aws_iam_role.cost_svc.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "ce:GetCostAndUsage"
        ]
        Effect   = "Allow"
        Resource = "*"
      },
    ]
  })
}
