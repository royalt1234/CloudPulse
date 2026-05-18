function cpuColor(v) {
  if (v >= 90) return 'var(--critical)'
  if (v >= 75) return 'var(--warning)'
  return 'var(--success)'
}

function ResourceCard({ resource }) {
  const { name, type, cloud, metrics } = resource
  const { cpu_percent, memory_percent, disk_percent } = metrics

  return (
    <div className="resource-card">
      <div className="resource-card-top">
        <div>
          <div className="resource-name">{name}</div>
          <div className="resource-type">{type}</div>
        </div>
        <span className={`resource-cloud-badge ${cloud.toLowerCase()}`}>{cloud}</span>
      </div>
      <div className="metric-bars">
        {[
          { label: 'CPU', value: cpu_percent,    color: cpuColor(cpu_percent) },
          { label: 'MEM', value: memory_percent, color: memory_percent > 85 ? 'var(--warning)' : '#60a5fa' },
          { label: 'DSK', value: disk_percent,   color: disk_percent > 80   ? 'var(--warning)' : '#a78bfa' },
        ].map(({ label, value, color }) => (
          <div className="metric-row" key={label}>
            <span className="metric-label">{label}</span>
            <div className="metric-bar-track">
              <div className="metric-bar-fill" style={{ width: `${value}%`, background: color }} />
            </div>
            <span className="metric-value" style={{ color }}>{value}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function MetricsPanel({ resources, loading }) {
  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">Resource Health</span>
        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{resources.length} nodes</span>
      </div>
      <div className="panel-body">
        {loading
          ? Array.from({ length: 5 }, (_, i) => (
              <div key={i} className="skeleton" style={{ height: 88, marginBottom: 10 }} />
            ))
          : (
            <div className="resource-list">
              {resources.map(r => <ResourceCard key={r.id} resource={r} />)}
            </div>
          )
        }
      </div>
    </div>
  )
}
