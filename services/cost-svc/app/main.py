import os
import random
import logging
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Cloud SDKs
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from azure.identity import DefaultAzureCredential
from azure.mgmt.costmanagement import CostManagementClient
from google.cloud import billing_v1
from google.api_core.exceptions import GoogleAPICallError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CloudPulse Cost Service", version="1.0.0", docs_url="/docs")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Helper for 30-day trend chart
def _generate_trend(total: float, days: int = 30) -> list:
    daily_base = total / days if total > 0 else 0
    return [
        {
            "date": (datetime.utcnow() - timedelta(days=days - i)).strftime("%Y-%m-%d"),
            "cost": round(daily_base + (random.uniform(-daily_base * 0.1, daily_base * 0.1) if daily_base > 0 else 0), 2),
        }
        for i in range(days)
    ]

@app.get("/health")
def health():
    return {"status": "healthy", "service": "cost-svc", "version": "1.0.0"}

@app.get("/cost/aws")
def aws_cost():
    services = []
    total_monthly = 0.0
    budget = 1500.0  # Simulated budget
    
    aws_access = os.environ.get("AWS_ACCESS_KEY_ID")
    if aws_access:
        try:
            ce_client = boto3.client('ce', region_name='us-east-1')
            start_date = datetime.utcnow().replace(day=1).strftime('%Y-%m-%d')
            end_date = datetime.utcnow().strftime('%Y-%m-%d')
            
            # If today is the 1st, fetch for today and tomorrow to satisfy Cost Explorer requirements
            if start_date == end_date:
                end_date = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d')
    
            response = ce_client.get_cost_and_usage(
                TimePeriod={'Start': start_date, 'End': end_date},
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
            )
            
            results = response['ResultsByTime'][0]['Groups']
            for group in results:
                service_name = group['Keys'][0]
                amount = float(group['Metrics']['UnblendedCost']['Amount'])
                if amount > 0:
                    services.append({"service": service_name, "monthly_cost": round(amount, 2), "budget": 0})
                    total_monthly += amount
    
            services.sort(key=lambda x: x["monthly_cost"], reverse=True)
            services = services[:6]
        except (BotoCoreError, ClientError) as e:
            logger.error(f"AWS Cost Explorer API Error: {e}")

    # Fallback to simulated AWS cost data if no real credentials/data
    if not services or total_monthly == 0.0:
        services = [
            {"service": "Amazon EC2", "monthly_cost": 450.20, "budget": 0},
            {"service": "Amazon RDS", "monthly_cost": 280.50, "budget": 0},
            {"service": "Amazon S3", "monthly_cost": 95.10, "budget": 0},
            {"service": "Amazon Route 53", "monthly_cost": 15.00, "budget": 0},
            {"service": "Amazon CloudFront", "monthly_cost": 62.40, "budget": 0},
        ]
        total_monthly = sum(s["monthly_cost"] for s in services)

    return {
        "cloud": "AWS", "region": "global", "currency": "USD",
        "total_monthly": round(total_monthly, 2),
        "total_budget": round(budget, 2),
        "budget_used_pct": round((total_monthly / budget * 100) if budget > 0 else 0, 1),
        "services": services,
        "daily_trend": _generate_trend(total_monthly)
    }

@app.get("/cost/azure")
def azure_cost():
    services = []
    total_monthly = 0.0
    budget = 1500.0
    
    sub_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
    if sub_id:
        try:
            credential = DefaultAzureCredential()
            client = CostManagementClient(credential)
            
            start_date = datetime.utcnow().replace(day=1)
            end_date = datetime.utcnow()
            
            # Note: Azure Cost API requires a specific query payload
            query_payload = {
                "type": "Usage",
                "timeframe": "Custom",
                "timePeriod": {
                    "from": start_date.strftime("%Y-%m-%dT00:00:00Z"),
                    "to": end_date.strftime("%Y-%m-%dT23:59:59Z")
                },
                "dataset": {
                    "granularity": "None",
                    "aggregation": {
                        "totalCost": {"name": "PreTaxCost", "function": "Sum"}
                    },
                    "grouping": [
                        {"type": "Dimension", "name": "ServiceName"}
                    ]
                }
            }
            
            scope = f"/subscriptions/{sub_id}"
            response = client.query.usage(scope, query_payload)
            
            if response.rows:
                for row in response.rows:
                    amount = float(row[0])
                    service_name = row[1]
                    if amount > 0:
                        services.append({"service": service_name, "monthly_cost": round(amount, 2), "budget": 0})
                        total_monthly += amount
    
            services.sort(key=lambda x: x["monthly_cost"], reverse=True)
            services = services[:6]
        except Exception as e:
            logger.error(f"Azure Cost Management API Error: {e}")

    # Fallback to simulated Azure cost data if no real credentials/data
    if not services or total_monthly == 0.0:
        services = [
            {"service": "Virtual Machines", "monthly_cost": 520.00, "budget": 0},
            {"service": "SQL Database", "monthly_cost": 310.50, "budget": 0},
            {"service": "App Service", "monthly_cost": 145.20, "budget": 0},
            {"service": "Azure Storage", "monthly_cost": 88.00, "budget": 0},
            {"service": "Azure Monitor", "monthly_cost": 40.50, "budget": 0},
        ]
        total_monthly = sum(s["monthly_cost"] for s in services)

    return {
        "cloud": "Azure", "region": "global", "currency": "USD",
        "total_monthly": round(total_monthly, 2),
        "total_budget": round(budget, 2),
        "budget_used_pct": round((total_monthly / budget * 100) if budget > 0 else 0, 1),
        "services": services,
        "daily_trend": _generate_trend(total_monthly)
    }

@app.get("/cost/gcp")
def gcp_cost():
    services = []
    total_monthly = 0.0
    budget = 1500.0
    
    gcp_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if gcp_creds:
        try:
            logger.info("GCP Credentials found, but real-time billing requires BigQuery export. Simulating...")
            services = [
                {"service": "Compute Engine", "monthly_cost": 450.20, "budget": 0},
                {"service": "Cloud SQL", "monthly_cost": 210.10, "budget": 0},
                {"service": "Cloud Storage", "monthly_cost": 85.50, "budget": 0},
            ]
            total_monthly = sum(s["monthly_cost"] for s in services)
        except Exception as e:
            logger.error(f"GCP Cost API Error: {e}")

    # Fallback to simulated GCP cost data if no real credentials/data
    if not services or total_monthly == 0.0:
        services = [
            {"service": "Compute Engine", "monthly_cost": 380.40, "budget": 0},
            {"service": "Cloud SQL", "monthly_cost": 190.20, "budget": 0},
            {"service": "Cloud Storage", "monthly_cost": 72.50, "budget": 0},
            {"service": "BigQuery", "monthly_cost": 120.10, "budget": 0},
            {"service": "Google Kubernetes Engine", "monthly_cost": 210.30, "budget": 0},
        ]
        total_monthly = sum(s["monthly_cost"] for s in services)

    return {
        "cloud": "GCP", "region": "global", "currency": "USD",
        "total_monthly": round(total_monthly, 2),
        "total_budget": round(budget, 2),
        "budget_used_pct": round((total_monthly / budget * 100) if budget > 0 else 0, 1),
        "services": services,
        "daily_trend": _generate_trend(total_monthly)
    }

@app.get("/cost/total")
def total_cost():
    aws_data = aws_cost()
    azure_data = azure_cost()
    gcp_data = gcp_cost()
    
    aws_total = aws_data["total_monthly"]
    azure_total = azure_data["total_monthly"]
    gcp_total = gcp_data["total_monthly"]
    
    combined = aws_total + azure_total + gcp_total
    last_month = combined * 0.95  # Simulated 5% growth
    
    return {
        "combined_monthly_usd": round(combined, 2),
        "aws_monthly_usd":      round(aws_total, 2),
        "azure_monthly_usd":    round(azure_total, 2),
        "gcp_monthly_usd":      round(gcp_total, 2),
        "aws_percentage":       round(aws_total / combined * 100, 1) if combined > 0 else 0,
        "azure_percentage":     round(azure_total / combined * 100, 1) if combined > 0 else 0,
        "gcp_percentage":       round(gcp_total / combined * 100, 1) if combined > 0 else 0,
        "last_month_usd":       round(last_month, 2),
        "forecast_monthly_usd": round(combined * 1.04, 2),
        "trend":                "up" if combined > last_month else "down",
        "currency":             "USD",
    }
