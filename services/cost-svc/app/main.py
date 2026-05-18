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
    if not aws_access:
        logger.warning("AWS credentials not found. Returning empty cost data.")
        return {
            "cloud": "AWS", "region": "global", "currency": "USD",
            "total_monthly": 0.0, "total_budget": budget, "budget_used_pct": 0.0,
            "services": [], "daily_trend": _generate_trend(0.0)
        }

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
        # Take top 6
        services = services[:6]

    except (BotoCoreError, ClientError) as e:
        logger.error(f"AWS Cost Explorer API Error: {e}")
        # Fallback to simulated error data so UI doesn't crash
        services = [{"service": "API Error", "monthly_cost": 0.0, "budget": 0}]

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
    if not sub_id:
        logger.warning("AZURE_SUBSCRIPTION_ID not found. Returning empty cost data.")
        return {
            "cloud": "Azure", "region": "global", "currency": "USD",
            "total_monthly": 0.0, "total_budget": budget, "budget_used_pct": 0.0,
            "services": [], "daily_trend": _generate_trend(0.0)
        }

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
        services = [{"service": "API Error", "monthly_cost": 0.0, "budget": 0}]

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
    
    # GCP Billing relies on GOOGLE_APPLICATION_CREDENTIALS env var implicitly
    # and requires the Billing Account ID to query the API. 
    # Usually this is done via BigQuery export, but we will mock GCP or try basic API.
    gcp_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    
    if not gcp_creds:
        logger.warning("GOOGLE_APPLICATION_CREDENTIALS not found. Returning empty cost data.")
        return {
            "cloud": "GCP", "region": "global", "currency": "USD",
            "total_monthly": 0.0, "total_budget": budget, "budget_used_pct": 0.0,
            "services": [], "daily_trend": _generate_trend(0.0)
        }

    # GCP Cloud Billing API does not have an easy "get current cost by service" endpoint like AWS/Azure.
    # It requires a BigQuery dataset linked to billing export.
    # We will simulate the GCP breakdown here for demo purposes if credentials ARE provided, 
    # or you could plug in BigQuery API here.
    logger.info("GCP Credentials found, but real-time billing requires BigQuery export. Simulating...")
    services = [
        {"service": "Compute Engine", "monthly_cost": 450.20, "budget": 0},
        {"service": "Cloud SQL", "monthly_cost": 210.10, "budget": 0},
        {"service": "Cloud Storage", "monthly_cost": 85.50, "budget": 0},
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
