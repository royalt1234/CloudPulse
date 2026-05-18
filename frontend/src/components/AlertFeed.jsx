import { useState } from 'react'
import { acknowledgeAlert } from '../services/api.js'

const SEV_ORDER = { CRITICAL: 0, WARNING: 1, INFO: 2 }

export default function AlertFeed({ alerts, loading }) {
  const [acked, setAcked] = useState(new Set())

  const list = (alerts?.alerts ?? [])
    .slice()
    .sort((a, b) => SEV_ORDER[a.severity] - SEV_ORDER[b.severity])

  async function handleAck(id, e) {
    e.stopPropagation()
    await acknowledgeAlert(id)
    setAcked(prev => new Set([...prev, id]))
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">Alert Feed</span>
        <span style={{ display: 'flex', gap: 6 }}>
          {alerts && (
            <>
              <span style={{ fontSize: 11, color: 'var(--critical)', background: 'var(--critical-dim)', padding: '2px 7px', borderRadius: 4, fontWeight: 700 }}>
                {alerts.critical} CRIT
              </span>
              <span style={{ fontSize: 11, color: 'var(--warning)', background: 'var(--warning-dim)', padding: '2px 7px', borderRadius: 4, fontWeight: 700 }}>
                {alerts.warning} WARN
              </span>
            </>
          )}
        </span>
      </div>
      <div className="panel-body">
        {loading
          ? Array.from({ length: 6 }, (_, i) => (
              <div key={i} className="skeleton" style={{ height: 66, marginBottom: 8 }} />
            ))
          : (
            <div className="alert-list">
              {list.map(alert => {
                const isAcked = acked.has(alert.id) || alert.acknowledged
                return (
                  <div key={alert.id} className={`alert-item ${isAcked ? 'acknowledged' : ''}`}>
                    <div className="alert-item-top">
                      <span className={`severity-badge ${alert.severity}`}>{alert.severity}</span>
                      <span className={`alert-cloud-badge ${alert.cloud.toLowerCase()}`}
                        style={{ color: alert.cloud === 'AWS' ? 'var(--aws)' : 'var(--azure)', background: alert.cloud === 'AWS' ? 'var(--aws-dim)' : 'var(--azure-dim)' }}>
                        {alert.cloud}
                      </span>
                      <span className="alert-resource">{alert.resource_name}</span>
                      <span className="alert-age">{alert.age_minutes}m</span>
                      {!isAcked && (
                        <button
                          onClick={(e) => handleAck(alert.id, e)}
                          style={{ fontSize: 10, padding: '1px 6px', border: '1px solid var(--border)', borderRadius: 4, background: 'transparent', color: 'var(--text-muted)', cursor: 'pointer', fontFamily: 'inherit' }}
                        >
                          ACK
                        </button>
                      )}
                    </div>
                    <div className="alert-message">{alert.message}</div>
                  </div>
                )
              })}
            </div>
          )
        }
      </div>
    </div>
  )
}
