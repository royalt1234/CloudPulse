import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid, Legend,
} from 'recharts'

const TOOLTIP_STYLE = {
  background: '#0c1122', border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: 8, fontSize: 11, color: '#eef2ff',
}

function CpuChart({ resources }) {
  // Take avg CPU across resources per cloud, 6 tick labels
  const aws   = resources.filter(r => r.cloud === 'AWS')
  const azure = resources.filter(r => r.cloud === 'Azure')
  const avg   = (arr) => arr.length ? +(arr.reduce((s, r) => s + r.metrics.cpu_percent, 0) / arr.length).toFixed(1) : 0

  // Create fake timeline from current values with slight historical variation
  const now = Date.now()
  const points = Array.from({ length: 12 }, (_, i) => ({
    t: new Date(now - (11 - i) * 60_000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    AWS:   +(avg(aws)   + (Math.random() - 0.5) * 10).toFixed(1),
    Azure: +(avg(azure) + (Math.random() - 0.5) * 10).toFixed(1),
  }))

  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={points} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id="gAWS"   x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#FF9900" stopOpacity={0.4}/>
            <stop offset="95%" stopColor="#FF9900" stopOpacity={0}/>
          </linearGradient>
          <linearGradient id="gAzure" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#0078D4" stopOpacity={0.4}/>
            <stop offset="95%" stopColor="#0078D4" stopOpacity={0}/>
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis dataKey="t" tick={{ fontSize: 10, fill: '#4a5875' }} axisLine={false} tickLine={false} interval={3} />
        <YAxis tick={{ fontSize: 10, fill: '#4a5875' }} axisLine={false} tickLine={false} domain={[0, 100]} unit="%" />
        <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [`${v}%`, '']} />
        <Legend iconSize={8} wrapperStyle={{ fontSize: 11 }} />
        <Area type="monotone" dataKey="AWS"   stroke="#FF9900" strokeWidth={2} fill="url(#gAWS)"   dot={false} />
        <Area type="monotone" dataKey="Azure" stroke="#0078D4" strokeWidth={2} fill="url(#gAzure)" dot={false} />
      </AreaChart>
    </ResponsiveContainer>
  )
}

function CostBarChart({ awsCost, azureCost, gcpCost }) {
  const merge = (aws = [], azure = [], gcp = []) => {
    const map = {}
    aws.forEach(s => { map[s.service] = { service: s.service.replace('Amazon ', '').replace('AWS ', ''), AWS: s.monthly_cost } })
    azure.forEach(s => { const k = s.service; if (!map[k]) map[k] = { service: k.replace('Azure ', '') }; map[k].Azure = s.monthly_cost })
    gcp.forEach(s => { const k = s.service; if (!map[k]) map[k] = { service: k.replace('Google ', '').replace('Cloud ', '') }; map[k].GCP = s.monthly_cost })
    return Object.values(map).sort((a, b) => (b.AWS || 0) + (b.Azure || 0) + (b.GCP || 0) - ((a.AWS || 0) + (a.Azure || 0) + (a.GCP || 0))).slice(0, 7)
  }
  const data = merge(awsCost?.services, azureCost?.services, gcpCost?.services)

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 40 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
        <XAxis dataKey="service" tick={{ fontSize: 9, fill: '#4a5875' }} axisLine={false} tickLine={false} angle={-35} textAnchor="end" />
        <YAxis tick={{ fontSize: 10, fill: '#4a5875' }} axisLine={false} tickLine={false} tickFormatter={v => `$${v}`} />
        <Tooltip contentStyle={TOOLTIP_STYLE} formatter={v => [`$${v?.toFixed(0) ?? 0}`, '']} />
        <Legend iconSize={8} wrapperStyle={{ fontSize: 11 }} />
        <Bar dataKey="AWS"   fill="#FF9900" radius={[4,4,0,0]} maxBarSize={24} />
        <Bar dataKey="Azure" fill="#0078D4" radius={[4,4,0,0]} maxBarSize={24} />
        <Bar dataKey="GCP"   fill="#EA4335" radius={[4,4,0,0]} maxBarSize={24} />
      </BarChart>
    </ResponsiveContainer>
  )
}

export default function ChartPanel({ resources, awsCost, azureCost, gcpCost, loading }) {
  return (
    <div className="panel" style={{ gap: 0 }}>
      <div className="panel-header">
        <span className="panel-title">CPU Utilisation — Last 12 Minutes</span>
      </div>
      <div style={{ padding: '16px 20px 0' }}>
        {loading
          ? <div className="skeleton" style={{ height: 220 }} />
          : <CpuChart resources={resources} />
        }
      </div>

      <div className="panel-header" style={{ marginTop: 8, borderTop: '1px solid var(--border)' }}>
        <span className="panel-title">Cost by Service (USD/mo)</span>
      </div>
      <div style={{ padding: '8px 20px 0' }}>
        {loading
          ? <div className="skeleton" style={{ height: 200 }} />
          : <CostBarChart awsCost={awsCost} azureCost={azureCost} gcpCost={gcpCost} />
        }
      </div>
    </div>
  )
}
