import os
import logging
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Azure SDKs
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.monitor import MonitorManagementClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CloudPulse Metrics Service", version="1.0.0", docs_url="/docs")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"status": "healthy", "service": "metrics-svc", "version": "1.0.0"}

@app.get("/metrics/aws")
def aws_metrics():
    # AWS infrastructure was removed from this deployment; returning empty.
    return []

@app.get("/metrics/azure")
def azure_metrics():
    sub_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
    if not sub_id:
        logger.warning("AZURE_SUBSCRIPTION_ID not found. Returning empty metrics.")
        return []

    resources = []
    try:
        credential = DefaultAzureCredential()
        compute_client = ComputeManagementClient(credential, sub_id)
        monitor_client = MonitorManagementClient(credential, sub_id)
        
        # Get all VMs in the subscription
        vms = list(compute_client.virtual_machines.list_all())
        
        # We'll take up to 5 VMs to avoid long API times in demo
        for vm in vms[:5]:
            vm_id = vm.id
            vm_name = vm.name
            
            # Timespan: Last 15 minutes
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=15)
            timespan = f"{start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}/{end_time.strftime('%Y-%m-%dT%H:%M:%SZ')}"
            
            # Fetch CPU metric
            cpu_metric = 0.0
            try:
                metrics_data = monitor_client.metrics.list(
                    vm_id,
                    timespan=timespan,
                    interval='PT1M',
                    metricnames='Percentage CPU',
                    aggregation='Average'
                )
                for item in metrics_data.value:
                    for timeseries in item.timeseries:
                        for data in timeseries.data:
                            if data.average is not None:
                                cpu_metric = data.average
            except Exception as me:
                logger.warning(f"Failed to fetch CPU for {vm_name}: {me}")
            
            resources.append({
                "id": vm_id.split('/')[-1],
                "name": vm_name,
                "type": "Virtual Machine",
                "cpu_percent": round(cpu_metric, 1),
                "memory_percent": round(0.0, 1), # Memory requires guest OS agent in Azure, omitted for simplicity
                "disk_usage_percent": round(0.0, 1), 
                "network_in_kbps": 0.0,
                "network_out_kbps": 0.0,
                "status": "Running"
            })
            
    except Exception as e:
        logger.error(f"Azure Monitor API Error: {e}")
        resources = [{"id": "api-err", "name": "API Error", "type": "Error", "cpu_percent": 0, "status": "Error"}]

    return resources

@app.get("/metrics/summary")
def summary():
    azure_data = azure_metrics()
    
    total_resources = len(azure_data)
    if total_resources == 0:
        return {
            "total_resources": 0,
            "aws_resources": 0,
            "azure_resources": 0,
            "avg_cpu_percent": 0.0,
            "avg_memory_percent": 0.0,
            "healthy_count": 0,
            "warning_count": 0,
            "critical_count": 0,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status": "unknown"
        }

    cpus = [r.get("cpu_percent", 0) for r in azure_data]
    mems = [r.get("memory_percent", 0) for r in azure_data]

    return {
        "total_resources": total_resources,
        "aws_resources": 0,
        "azure_resources": total_resources,
        "avg_cpu_percent": round(sum(cpus) / total_resources, 1),
        "avg_memory_percent": round(sum(mems) / total_resources, 1),
        "healthy_count": sum(1 for c in cpus if c < 75),
        "warning_count": sum(1 for c in cpus if 75 <= c < 90),
        "critical_count": sum(1 for c in cpus if c >= 90),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": "healthy" if (sum(cpus) / total_resources) < 80 else "warning"
    }

from fastapi import Query
@app.get("/metrics/history/{resource_id}")
def history(resource_id: str, points: int = Query(default=30, le=60)):
    # With real Azure Monitor, history is fetched per-resource dynamically, 
    # but for simplicity in this endpoint we return an empty list or simulated flat line
    # since we already fetch the real current metric in /metrics/azure.
    now = datetime.utcnow()
    return [
        {
            "timestamp": (now - timedelta(minutes=points - i)).isoformat() + "Z",
            "cpu_percent": 0.0,
            "memory_percent": 0.0,
            "disk_percent": 0.0,
            "network_in_mbps": 0.0,
            "network_out_mbps": 0.0,
        }
        for i in range(points)
    ]
