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
    # Return mock AWS data for the demo
    return [
        {
            "id": "i-09876fedcba543210",
            "name": "aws-db-node-1",
            "type": "EC2 Instance",
            "cloud": "AWS",
            "metrics": {
                "cpu_percent": 82.5,
                "memory_percent": 68.4,
                "disk_percent": 45.2,
                "network_in_kbps": 1204.5,
                "network_out_kbps": 3402.1
            },
            "status": "Running"
        },
        {
            "id": "i-1234567890abcdef0",
            "name": "aws-web-prod-1",
            "type": "EC2 Instance",
            "cloud": "AWS",
            "metrics": {
                "cpu_percent": 45.1,
                "memory_percent": 55.0,
                "disk_percent": 60.1,
                "network_in_kbps": 5400.0,
                "network_out_kbps": 8900.0
            },
            "status": "Running"
        }
    ]

@app.get("/metrics/azure")
def azure_metrics():
    resources = []
    sub_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
    if sub_id:
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
                    "cloud": "Azure",
                    "metrics": {
                        "cpu_percent": round(cpu_metric, 1),
                        "memory_percent": round(0.0, 1), # Memory requires guest OS agent in Azure, omitted for simplicity
                        "disk_percent": round(0.0, 1), 
                        "network_in_kbps": 0.0,
                        "network_out_kbps": 0.0
                    },
                    "status": "Running"
                })
        except Exception as e:
            logger.error(f"Azure Monitor API Error: {e}")

    # Fallback to simulated Azure metrics if we found 0 real resources or query failed
    if not resources:
        resources = [
            {
                "id": "vm-azure-app-01",
                "name": "azure-app-node-1",
                "type": "Virtual Machine",
                "cloud": "Azure",
                "metrics": {
                    "cpu_percent": 65.4,
                    "memory_percent": 72.1,
                    "disk_percent": 38.9,
                    "network_in_kbps": 2048.0,
                    "network_out_kbps": 1024.0
                },
                "status": "Running"
            },
            {
                "id": "vm-azure-app-02",
                "name": "azure-app-node-2",
                "type": "Virtual Machine",
                "cloud": "Azure",
                "metrics": {
                    "cpu_percent": 88.0,
                    "memory_percent": 91.5,
                    "disk_percent": 78.2,
                    "network_in_kbps": 4096.0,
                    "network_out_kbps": 2048.0
                },
                "status": "Running"
            }
        ]
        
    return resources

@app.get("/metrics/gcp")
def gcp_metrics():
    return [
        {
            "id": "gcp-web-prod-1",
            "name": "gcp-web-prod-1",
            "type": "Compute Engine",
            "cloud": "GCP",
            "metrics": {
                "cpu_percent": 54.8,
                "memory_percent": 61.2,
                "disk_percent": 42.0,
                "network_in_kbps": 1500.0,
                "network_out_kbps": 800.0
            },
            "status": "Running"
        },
        {
            "id": "gcp-db-replica-1",
            "name": "gcp-db-replica-1",
            "type": "Compute Engine",
            "cloud": "GCP",
            "metrics": {
                "cpu_percent": 76.5,
                "memory_percent": 82.0,
                "disk_percent": 68.3,
                "network_in_kbps": 3200.0,
                "network_out_kbps": 4100.0
            },
            "status": "Running"
        }
    ]

@app.get("/metrics/summary")
def summary():
    azure_data = azure_metrics()
    aws_data = aws_metrics()
    gcp_data = gcp_metrics()
    
    combined = azure_data + aws_data + gcp_data
    total_resources = len(combined)
    aws_resources = len(aws_data)
    azure_resources = len(azure_data)
    gcp_resources = len(gcp_data)
    
    if total_resources == 0:
        return {
            "total_resources": 0,
            "aws_resources": 0,
            "azure_resources": 0,
            "gcp_resources": 0,
            "avg_cpu_percent": 0.0,
            "avg_memory_percent": 0.0,
            "healthy_count": 0,
            "warning_count": 0,
            "critical_count": 0,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status": "unknown"
        }

    cpus = [r["metrics"].get("cpu_percent", 0) for r in combined]
    mems = [r["metrics"].get("memory_percent", 0) for r in combined]

    return {
        "total_resources": total_resources,
        "aws_resources": aws_resources,
        "azure_resources": azure_resources,
        "gcp_resources": gcp_resources,
        "avg_cpu_percent": round(sum(cpus) / total_resources, 1),
        "avg_memory_percent": round(sum(mems) / total_resources, 1),
        "healthy_count": sum(1 for c in cpus if c < 75),
        "warning_count": sum(1 for c in cpus if 75 <= c < 90),
        "critical_count": sum(1 for c in cpus if c >= 90),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": "healthy" if (sum(cpus) / total_resources) < 80 else "warning"
    }

from fastapi import Query
import random
@app.get("/metrics/history/{resource_id}")
def history(resource_id: str, points: int = Query(default=30, le=60)):
    now = datetime.utcnow()
    return [
        {
            "timestamp": (now - timedelta(minutes=points - i)).isoformat() + "Z",
            "cpu_percent": round(random.uniform(40.0, 90.0), 1),
            "memory_percent": round(random.uniform(50.0, 85.0), 1),
            "disk_percent": round(random.uniform(30.0, 60.0), 1),
            "network_in_mbps": round(random.uniform(1.0, 50.0), 2),
            "network_out_mbps": round(random.uniform(1.0, 30.0), 2),
        }
        for i in range(points)
    ]
