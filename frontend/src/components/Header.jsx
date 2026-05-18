import { RefreshCw, LogOut } from 'lucide-react'
import { useMsal } from '@azure/msal-react'

export default function Header({ lastUpdated, cloudFilter, onCloudChange, error }) {
  const { instance } = useMsal();
  const fmt = (d) => d ? d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '—'

  return (
    <header className="header">
      <div className="header-brand">
        {/* Logo SVG */}
        <svg className="header-logo" viewBox="0 0 34 34" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="17" cy="17" r="17" fill="url(#grad)"/>
          <path d="M10 20l4-8 3 5 2-3 5 6" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          <defs>
            <linearGradient id="grad" x1="0" y1="0" x2="34" y2="34" gradientUnits="userSpaceOnUse">
              <stop stopColor="#60a5fa"/>
              <stop offset="1" stopColor="#a78bfa"/>
            </linearGradient>
          </defs>
        </svg>
        <span className="header-title">Cloud<span>Pulse</span></span>
      </div>

      <div className="header-controls">
        {error && (
          <span style={{ fontSize: 11, color: 'var(--critical)', background: 'var(--critical-dim)', padding: '3px 8px', borderRadius: 5 }}>
            ⚠ API Error — using cached data
          </span>
        )}

        <div className="cloud-tabs">
          {[['both','All Clouds'],['aws','AWS'],['azure','Azure']].map(([v, label]) => (
            <button
              key={v}
              className={`cloud-tab ${cloudFilter === v ? 'active ' + v : ''}`}
              onClick={() => onCloudChange(v)}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="live-badge">
          <span className="live-dot" />
          LIVE
        </div>

        <span className="last-updated">
          <RefreshCw size={11} style={{ marginRight: 4, verticalAlign: 'middle' }} />
          {fmt(lastUpdated)}
        </span>

        <button 
          onClick={() => instance.logoutRedirect()}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            marginLeft: '16px'
          }}
          title="Sign Out"
        >
          <LogOut size={16} />
        </button>
      </div>
    </header>
  )
}
