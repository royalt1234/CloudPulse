import { useState, useEffect, useCallback } from 'react'
import Header from './components/Header.jsx'
import Dashboard from './components/Dashboard.jsx'
import {
  fetchMetricsSummary, fetchAWSMetrics, fetchAzureMetrics,
  fetchAlerts, fetchTotalCost, fetchAWSCost, fetchAzureCost, fetchGCPCost
} from './services/api.js'
import { useIsAuthenticated } from "@azure/msal-react";
import Login from "./components/Login.jsx";

export default function App() {
  const isAuthenticated = useIsAuthenticated();
  const [data, setData]           = useState({})
  const [loading, setLoading]     = useState(true)
  const [lastUpdated, setLast]    = useState(null)
  const [cloudFilter, setCloud]   = useState('both')
  const [error, setError]         = useState(null)

  const refresh = useCallback(async () => {
    try {
      const [summary, awsMetrics, azureMetrics, alerts, totalCost, awsCost, azureCost, gcpCost] =
        await Promise.all([
          fetchMetricsSummary(),
          fetchAWSMetrics(),
          fetchAzureMetrics(),
          fetchAlerts(),
          fetchTotalCost(),
          fetchAWSCost(),
          fetchAzureCost(),
          fetchGCPCost()
        ])
      setData({ summary, awsMetrics, azureMetrics, alerts, totalCost, awsCost, azureCost, gcpCost })
      setLast(new Date())
      setLoading(false)
      setError(null)
    } catch (e) {
      setError(e.message)
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, 10_000)
    return () => clearInterval(id)
  }, [refresh])

  if (!isAuthenticated) {
    return <Login />
  }

  return (
    <div className="app">
      <Header
        lastUpdated={lastUpdated}
        cloudFilter={cloudFilter}
        onCloudChange={setCloud}
        error={error}
      />
      <Dashboard data={data} loading={loading} cloudFilter={cloudFilter} onRefresh={refresh} />
    </div>
  )
}
