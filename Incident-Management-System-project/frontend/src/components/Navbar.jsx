import { Link } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { fetchHealth } from '../api/client'

export default function Navbar() {
  const [health, setHealth] = useState(null)

  useEffect(() => {
    const poll = async () => {
      try { setHealth((await fetchHealth()).data) } catch {}
    }
    poll()
    const t = setInterval(poll, 5000)
    return () => clearInterval(t)
  }, [])

  return (
    <nav style={{
      background: 'var(--surface)', borderBottom: '1px solid var(--border)',
      padding: '0 24px', display: 'flex', alignItems: 'center', gap: 24, height: 52
    }}>
      <Link to="/" style={{ fontWeight: 700, fontSize: 15, color: 'var(--accent)', letterSpacing: '-0.01em' }}>
        ⚡ IMS
      </Link>
      <Link to="/" style={{ color: 'var(--muted)', fontSize: 13 }}>Dashboard</Link>
      <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 12 }}>
        {health && (
          <>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              {health.signals_per_sec} sig/s
            </span>
            <span style={{ color: 'var(--muted)', fontSize: 12 }}>
              queue: {health.queue_depth}
            </span>
            <span style={{
              width: 8, height: 8, borderRadius: '50%',
              background: health.status === 'ok' ? 'var(--p3)' : 'var(--p0)',
              display: 'inline-block'
            }} title={health.status} />
          </>
        )}
      </div>
    </nav>
  )
}
