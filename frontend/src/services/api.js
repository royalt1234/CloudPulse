const BASE = {
  metrics: import.meta.env.VITE_METRICS_URL || '/api/metrics',
  alerts:  import.meta.env.VITE_ALERTS_URL  || '/api/alerts',
  cost:    import.meta.env.VITE_COST_URL    || '/api/cost',
}

async function get(url) {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${url}`)
  return res.json()
}

export const fetchMetricsSummary  = () => get(`${BASE.metrics}/metrics/summary`)
export const fetchAWSMetrics      = () => get(`${BASE.metrics}/metrics/aws`)
export const fetchAzureMetrics    = () => get(`${BASE.metrics}/metrics/azure`)
export const fetchMetricHistory   = (id) => get(`${BASE.metrics}/metrics/history/${id}`)

export const fetchAlerts          = (params = {}) => {
  const q = new URLSearchParams(params).toString()
  return get(`${BASE.alerts}/alerts${q ? '?' + q : ''}`)
}
export const acknowledgeAlert     = (id) =>
  fetch(`${BASE.alerts}/alerts/${id}/acknowledge`, { method: 'POST' }).then(r => r.json())

export const fetchTotalCost       = () => get(`${BASE.cost}/cost/total`)
export const fetchAWSCost         = () => get(`${BASE.cost}/cost/aws`)
export const fetchAzureCost       = () => get(`${BASE.cost}/cost/azure`)
export const fetchGCPCost         = () => get(`${BASE.cost}/cost/gcp`)
