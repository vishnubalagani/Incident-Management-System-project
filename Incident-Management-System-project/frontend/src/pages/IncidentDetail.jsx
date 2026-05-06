import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { fetchWorkItem, fetchSignals, updateStatus, submitRCA } from '../api/client'
import { formatDistanceToNow, format } from 'date-fns'
import RCAForm from '../components/RCAForm'

const STATUS_FLOW = ['OPEN', 'INVESTIGATING', 'RESOLVED', 'CLOSED']

export default function IncidentDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [item, setItem] = useState(null)
  const [signals, setSignals] = useState([])
  const [loading, setLoading] = useState(true)
  const [transitioning, setTransitioning] = useState(false)
  const [error, setError] = useState('')
  const [showRCA, setShowRCA] = useState(false)

  const load = async () => {
    try {
      const [wiRes, sigRes] = await Promise.all([fetchWorkItem(id), fetchSignals(id)])
      setItem(wiRes.data)
      setSignals(sigRes.data.signals)
    } catch { navigate('/') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [id])

  const currentIdx = STATUS_FLOW.indexOf(item?.status)
  const nextStatus = STATUS_FLOW[currentIdx + 1]

  const handleTransition = async () => {
    if (!nextStatus) return
    if (nextStatus === 'CLOSED' && !item?.rca) {
      setShowRCA(true)
      return
    }
    setTransitioning(true)
    setError('')
    try {
      await updateStatus(id, nextStatus)
      await load()
    } catch (e) {
      setError(e.response?.data?.detail || 'Transition failed')
    } finally { setTransitioning(false) }
  }

  const handleRCASubmit = async (data) => {
    await submitRCA(id, data)
    await load()
    setShowRCA(false)
  }

  if (loading) return <p style={{ color: 'var(--muted)', padding: 24 }}>Loading...</p>
  if (!item) return null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
        <button onClick={() => navigate('/')} style={{ background: 'var(--surface2)', color: 'var(--muted)' }}>← Back</button>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <span className={`badge badge-${item.priority}`}>{item.priority}</span>
            <span className={`badge badge-${item.status}`}>{item.status}</span>
            <h1 style={{ fontSize: 17, fontWeight: 700 }}>{item.title}</h1>
          </div>
          <p style={{ color: 'var(--muted)', fontSize: 12, marginTop: 6 }}>
            {item.component_id} · {item.signal_count} signals · started {formatDistanceToNow(new Date(item.start_time), { addSuffix: true })}
            {item.mttr_seconds && ` · MTTR ${Math.round(item.mttr_seconds / 60)}m`}
          </p>
        </div>
        {nextStatus && item.status !== 'CLOSED' && (
          <button
            onClick={handleTransition}
            disabled={transitioning}
            style={{ background: 'var(--accent)', color: '#fff', whiteSpace: 'nowrap' }}
          >
            {transitioning ? '...' : `→ ${nextStatus}`}
          </button>
        )}
      </div>
      {error && <p className="error">{error}</p>}

      {/* Status progress bar */}
      <div style={{ display: 'flex', gap: 4 }}>
        {STATUS_FLOW.map((s, i) => (
          <div key={s} style={{
            flex: 1, height: 4, borderRadius: 2,
            background: i <= currentIdx ? 'var(--accent)' : 'var(--surface2)'
          }} />
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {/* Signals */}
        <div className="card" style={{ gridColumn: '1 / 2' }}>
          <h2 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>
            Raw Signals ({signals.length})
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 400, overflowY: 'auto' }}>
            {signals.length === 0 && <p style={{ color: 'var(--muted)' }}>No signals yet.</p>}
            {signals.map((s, i) => (
              <div key={i} style={{
                background: 'var(--surface2)', borderRadius: 6, padding: '8px 12px',
                borderLeft: '3px solid var(--p0)'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontWeight: 600, fontSize: 12 }}>{s.error_code}</span>
                  <span style={{ color: 'var(--muted)', fontSize: 11 }}>
                    {format(new Date(s.timestamp), 'HH:mm:ss')}
                  </span>
                </div>
                <p style={{ color: 'var(--muted)', fontSize: 12, marginTop: 2 }}>{s.message}</p>
                {s.latency_ms && <span style={{ color: 'var(--p2)', fontSize: 11 }}>{s.latency_ms}ms</span>}
              </div>
            ))}
          </div>
        </div>

        {/* RCA */}
        <div className="card">
          <h2 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>Root Cause Analysis</h2>
          {item.rca ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: 13 }}>
              <Field label="Category" value={item.rca.root_cause_category} />
              <Field label="Start" value={format(new Date(item.rca.incident_start), 'PPpp')} />
              <Field label="End" value={format(new Date(item.rca.incident_end), 'PPpp')} />
              <Field label="Fix applied" value={item.rca.fix_applied} />
              <Field label="Prevention" value={item.rca.prevention_steps} />
            </div>
          ) : (
            <div>
              <p style={{ color: 'var(--muted)', fontSize: 13, marginBottom: 12 }}>
                RCA required before closing this incident.
              </p>
              <button onClick={() => setShowRCA(true)} style={{ background: 'var(--accent)', color: '#fff' }}>
                + Submit RCA
              </button>
            </div>
          )}
        </div>
      </div>

      {showRCA && (
        <RCAForm
          workItemId={id}
          onSubmit={handleRCASubmit}
          onCancel={() => setShowRCA(false)}
          startTime={item.start_time}
        />
      )}
    </div>
  )
}

function Field({ label, value }) {
  return (
    <div>
      <div style={{ color: 'var(--muted)', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</div>
      <div style={{ marginTop: 2 }}>{value}</div>
    </div>
  )
}
