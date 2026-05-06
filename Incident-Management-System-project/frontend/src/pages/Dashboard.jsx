import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchDashboard } from '../api/client'
import { formatDistanceToNow } from 'date-fns'

const PRIORITY_ORDER = { P0: 0, P1: 1, P2: 2, P3: 3 }

export default function Dashboard() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('ALL')
  const navigate = useNavigate()

  const load = async () => {
    try {
      const { data } = await fetchDashboard()
      setItems(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    const t = setInterval(load, 5000) // live refresh every 5s
    return () => clearInterval(t)
  }, [])

  const filtered = items
    .filter(i => filter === 'ALL' || i.status === filter)
    .sort((a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority])

  const statuses = ['ALL', 'OPEN', 'INVESTIGATING', 'RESOLVED', 'CLOSED']

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <h1 style={{ fontSize: 20, fontWeight: 700 }}>Incident Feed</h1>
          <p style={{ color: 'var(--muted)', fontSize: 13, marginTop: 2 }}>
            {filtered.length} incident{filtered.length !== 1 ? 's' : ''} — auto-refreshes every 5s
          </p>
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          {statuses.map(s => (
            <button key={s}
              onClick={() => setFilter(s)}
              style={{
                background: filter === s ? 'var(--accent)' : 'var(--surface2)',
                color: filter === s ? '#fff' : 'var(--muted)',
                padding: '5px 12px', fontSize: 12,
              }}>
              {s}
            </button>
          ))}
        </div>
      </div>

      {loading && <p style={{ color: 'var(--muted)' }}>Loading...</p>}

      {!loading && filtered.length === 0 && (
        <div className="card" style={{ textAlign: 'center', padding: 40, color: 'var(--muted)' }}>
          No incidents found.
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {filtered.map(item => (
          <div key={item.id} className="card"
            onClick={() => navigate(`/incident/${item.id}`)}
            style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 14, transition: 'border-color 0.15s' }}
            onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--accent)'}
            onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
          >
            <span className={`badge badge-${item.priority}`}>{item.priority}</span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontWeight: 600, fontSize: 14, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {item.title}
              </div>
              <div style={{ color: 'var(--muted)', fontSize: 12, marginTop: 2 }}>
                {item.component_id} · {item.signal_count} signals · {formatDistanceToNow(new Date(item.start_time), { addSuffix: true })}
              </div>
            </div>
            <span className={`badge badge-${item.status}`}>{item.status}</span>
            {item.mttr_seconds && (
              <span style={{ color: 'var(--muted)', fontSize: 12, whiteSpace: 'nowrap' }}>
                MTTR {Math.round(item.mttr_seconds / 60)}m
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
