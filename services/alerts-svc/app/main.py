import os
import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

# Azure SDKs
from azure.identity import DefaultAzureCredential
from azure.mgmt.alertsmanagement import AlertsManagementClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CloudPulse Alerts Service", version="1.0.0", docs_url="/docs")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_SEV_ORDER = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
_acknowledged: set[str] = set()

def _get_azure_alerts() -> list[dict]:
    alerts_list = []
    sub_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
    if sub_id:
        try:
            credential = DefaultAzureCredential()
            client = AlertsManagementClient(credential, sub_id)
            
            # Fetch alerts created in the last 7 days
            alerts = client.alerts.get_all(time_range="7d")
            
            for alert in alerts:
                # Map Azure Monitor severity (Sev0, Sev1, Sev2, Sev3, Sev4) to our format
                azure_sev = getattr(alert, 'severity', 'Sev3')
                if azure_sev in ['Sev0', 'Sev1']:
                    sev = "CRITICAL"
                elif azure_sev == 'Sev2':
                    sev = "WARNING"
                else:
                    sev = "INFO"
                    
                alert_id = alert.id.split('/')[-1] if alert.id else "unknown"
                
                # Extract target resource name
                resource_name = "Azure Subscription"
                if getattr(alert, 'essentials', None) and getattr(alert.essentials, 'target_resource_name', None):
                    resource_name = alert.essentials.target_resource_name
    
                age_minutes = 0
                start_date = getattr(alert, 'start_date_time', None)
                if start_date:
                    # Calculate age in minutes
                    now = datetime.utcnow()
                    start_date = start_date.replace(tzinfo=None) # remove tzinfo for subtraction if needed
                    age_minutes = int((now - start_date).total_seconds() / 60)
    
                alerts_list.append({
                    "id": alert_id,
                    "type": getattr(alert, 'essentials', None).monitor_condition if getattr(alert, 'essentials', None) else "Alert",
                    "severity": sev,
                    "cloud": "Azure",
                    "resource_id": alert_id,
                    "resource_name": resource_name,
                    "message": alert.name or "Azure Monitor Alert",
                    "acknowledged": alert_id in _acknowledged,
                    "timestamp": start_date.isoformat() + "Z" if start_date else datetime.utcnow().isoformat() + "Z",
                    "age_minutes": age_minutes,
                })
        except Exception as e:
            logger.error(f"Azure Alerts API Error: {e}")

    # Fallback to simulated Azure alerts if no real ones
    if not alerts_list:
        alerts_list = [
            {
                "id": "az-err-01",
                "type": "HighCPU",
                "severity": "WARNING",
                "cloud": "Azure",
                "resource_id": "vm-azure-app-02",
                "resource_name": "azure-app-node-2",
                "message": "CPU utilization exceeded 80%",
                "acknowledged": "az-err-01" in _acknowledged,
                "timestamp": (datetime.utcnow() - timedelta(minutes=12)).isoformat() + "Z",
                "age_minutes": 12,
            },
            {
                "id": "az-err-02",
                "type": "MemoryLeak",
                "severity": "CRITICAL",
                "cloud": "Azure",
                "resource_id": "vm-azure-db-01",
                "resource_name": "azure-db-node-1",
                "message": "Out of memory error imminent",
                "acknowledged": "az-err-02" in _acknowledged,
                "timestamp": (datetime.utcnow() - timedelta(minutes=3)).isoformat() + "Z",
                "age_minutes": 3,
            }
        ]
        
    return sorted(alerts_list, key=lambda a: (_SEV_ORDER.get(a["severity"], 3), a["age_minutes"]))


@app.get("/health")
def health():
    return {"status": "healthy", "service": "alerts-svc", "version": "1.0.0"}


def _get_aws_alerts() -> list[dict]:
    return [
        {
            "id": "aws-err-01",
            "type": "StorageFull",
            "severity": "CRITICAL",
            "cloud": "AWS",
            "resource_id": "i-09876fedcba543210",
            "resource_name": "aws-db-node-1",
            "message": "Storage capacity reached 95%",
            "acknowledged": "aws-err-01" in _acknowledged,
            "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat() + "Z",
            "age_minutes": 5,
        }
    ]


@app.get("/health")
def health():
    return {"status": "healthy", "service": "alerts-svc", "version": "1.0.0"}


@app.get("/alerts")
def get_alerts(cloud: Optional[str] = None):
    aws_alerts = _get_aws_alerts()
    azure_alerts = _get_azure_alerts()
    
    if cloud and cloud.upper() == "AWS":
        alerts = aws_alerts
    elif cloud and cloud.upper() == "AZURE":
        alerts = azure_alerts
    else:
        alerts = azure_alerts + aws_alerts
        
    return {
        "alerts": alerts,
        "summary": {
            "total":    len(alerts),
            "critical": sum(1 for a in alerts if a["severity"] == "CRITICAL" and not a["acknowledged"]),
            "warning":  sum(1 for a in alerts if a["severity"] == "WARNING"  and not a["acknowledged"]),
            "info":     sum(1 for a in alerts if a["severity"] == "INFO"     and not a["acknowledged"]),
        }
    }


@app.post("/alerts/{alert_id}/ack")
def acknowledge_alert(alert_id: str):
    _acknowledged.add(alert_id)
    return {"acknowledged": True, "alert_id": alert_id}


@app.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert_alt(alert_id: str):
    _acknowledged.add(alert_id)
    return {"acknowledged": True, "alert_id": alert_id}


@app.get("/alerts/stats")
def stats():
    alerts = _get_azure_alerts() + _get_aws_alerts()
    return {
        "by_cloud":    {"aws": sum(1 for a in alerts if a["cloud"] == "AWS"), "azure": sum(1 for a in alerts if a["cloud"] == "Azure")},
        "by_severity": {"critical": sum(1 for a in alerts if a["severity"] == "CRITICAL"), "warning": sum(1 for a in alerts if a["severity"] == "WARNING"), "info": sum(1 for a in alerts if a["severity"] == "INFO")},
        "by_type":     {t: sum(1 for a in alerts if a["type"] == t) for t in {a["type"] for a in alerts}},
        "total_unacknowledged": sum(1 for a in alerts if not a["acknowledged"]),
    }
