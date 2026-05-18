export default function CostPanel({ cloud, costData, loading, color }) {
  const maxCost = costData ? Math.max(...(costData.services ?? []).map(s => s.monthly_cost)) : 1

  return (
    <div className="cost-cloud-card" style={{ borderTop: `2px solid ${color}` }}>
      <div className="cost-cloud-header">
        <span className="cost-cloud-label" style={{ color }}>{cloud}</span>
        <span style={{ fontSize: 10, color: 'var(--text-muted)', background: 'rgba(255,255,255,0.04)', padding: '2px 8px', borderRadius: 4 }}>
          {costData?.region ?? '—'}
        </span>
      </div>

      {loading ? (
        <div className="skeleton" style={{ height: 180 }} />
      ) : costData ? (
        <>
          <div className="cost-total" style={{ color }}>
            ${costData.total_monthly.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="cost-budget">
            Budget: ${costData.total_budget.toLocaleString()} / mo &nbsp;·&nbsp;
            <span style={{ color: costData.budget_used_pct > 95 ? 'var(--warning)' : 'var(--success)' }}>
              {costData.budget_used_pct}% used
            </span>
          </div>
          <div className="cost-service-list">
            {(costData.services ?? []).slice(0, 6).map(s => (
              <div key={s.service} className="cost-service-row">
                <div className="cost-service-name">
                  <span>{s.service}</span>
                  <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
                    ${s.monthly_cost.toFixed(0)}
                  </span>
                </div>
                <div className="cost-service-bar-track">
                  <div
                    className="cost-service-bar-fill"
                    style={{ width: `${(s.monthly_cost / maxCost) * 100}%`, background: color }}
                  />
                </div>
              </div>
            ))}
          </div>
        </>
      ) : (
        <p style={{ color: 'var(--text-muted)', fontSize: 12 }}>No data</p>
      )}
    </div>
  )
}
