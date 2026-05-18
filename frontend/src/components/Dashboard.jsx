import MetricsPanel from './MetricsPanel.jsx'
import AlertFeed    from './AlertFeed.jsx'
import CostPanel    from './CostPanel.jsx'
import ChartPanel   from './ChartPanel.jsx'

function StatCard({ label, value, sub, className = '' }) {
  return (
    <div className={`stat-card ${className}`}>
      <div className="label">{label}</div>
      <div className="value">{value ?? '—'}</div>
      {sub && <div className="sub">{sub}</div>}
    </div>
  )
}

export default function Dashboard({ data, loading, cloudFilter }) {
  const { summary, awsMetrics = [], azureMetrics = [], alerts, totalCost, awsCost, azureCost, gcpCost } = data

  const resources = [
    ...(cloudFilter !== 'azure' && cloudFilter !== 'gcp' ? awsMetrics   : []),
    ...(cloudFilter !== 'aws'   && cloudFilter !== 'gcp' ? azureMetrics : []),
  ]

  return (
    <main className="dashboard">
      {/* ── Summary Bar ── */}
      <div className="summary-bar" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
        <StatCard
          label="Total Resources"
          value={summary?.total_resources ?? (loading ? '…' : '—')}
          sub={`${summary?.aws_resources ?? 0} AWS · ${summary?.azure_resources ?? 0} Azure`}
        />
        <StatCard
          label="Avg CPU"
          value={summary ? `${summary.avg_cpu_percent}%` : '…'}
          sub="Across all nodes"
          className={summary?.avg_cpu_percent > 80 ? 'warning' : 'success'}
        />
        <StatCard
          label="Critical Alerts"
          value={alerts?.critical ?? '…'}
          sub={`${alerts?.warning ?? 0} warnings · ${alerts?.info ?? 0} info`}
          className={alerts?.critical > 0 ? 'critical' : 'success'}
        />
        <StatCard
          label="AWS Spend"
          value={awsCost ? `$${awsCost.total_monthly.toLocaleString()}` : '…'}
          sub={`Budget: $${awsCost?.total_budget?.toLocaleString() ?? '—'}/mo`}
          className="aws"
        />
        <StatCard
          label="Azure Spend"
          value={azureCost ? `$${azureCost.total_monthly.toLocaleString()}` : '…'}
          sub={`Budget: $${azureCost?.total_budget?.toLocaleString() ?? '—'}/mo`}
          className="azure"
        />
        <StatCard
          label="GCP Spend"
          value={gcpCost ? `$${gcpCost.total_monthly.toLocaleString()}` : '…'}
          sub={`Budget: $${gcpCost?.total_budget?.toLocaleString() ?? '—'}/mo`}
          className="gcp"
          style={{ '--accent': 'var(--gcp)' }}
        />
      </div>

      {/* ── Main Grid ── */}
      <div className="main-grid">
        <MetricsPanel resources={resources} loading={loading} />
        <ChartPanel   resources={resources} awsCost={awsCost} azureCost={azureCost} gcpCost={gcpCost} loading={loading} />
        <AlertFeed    alerts={alerts} loading={loading} />
      </div>

      {/* ── Cost Detail ── */}
      <div className="bottom-row" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
        <CostPanel cloud="AWS"   costData={awsCost}   loading={loading} color="var(--aws)"   />
        <CostPanel cloud="Azure" costData={azureCost} loading={loading} color="var(--azure)" />
        <CostPanel cloud="GCP"   costData={gcpCost}   loading={loading} color="var(--gcp)"   />
      </div>
    </main>
  )
}
