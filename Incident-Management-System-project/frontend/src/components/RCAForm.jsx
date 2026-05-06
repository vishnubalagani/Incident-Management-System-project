import { useState } from 'react'

const CATEGORIES = [
  'Infrastructure failure', 'Network issue', 'Software bug',
  'Configuration error', 'Capacity exceeded', 'Third-party dependency',
  'Human error', 'Security incident', 'Unknown',
]

export default function RCAForm({ onSubmit, onCancel, startTime }) {
  const now = new Date().toISOString().slice(0, 16)
  const start = startTime ? new Date(startTime).toISOString().slice(0, 16) : now

  const [form, setForm] = useState({
    incident_start: start,
    incident_end: now,
    root_cause_category: CATEGORIES[0],
    fix_applied: '',
    prevention_steps: '',
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = async () => {
    if (form.fix_applied.length < 10 || form.prevention_steps.length < 10) {
      setError('Fix applied and prevention steps must each be at least 10 characters.')
      return
    }
    setSubmitting(true)
    setError('')
    try {
      await onSubmit({
        ...form,
        incident_start: new Date(form.incident_start).toISOString(),
        incident_end: new Date(form.incident_end).toISOString(),
      })
    } catch (e) {
      setError(e.response?.data?.detail || 'Submission failed')
    } finally { setSubmitting(false) }
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100,
    }}>
      <div className="card" style={{ width: '100%', maxWidth: 520, maxHeight: '90vh', overflowY: 'auto' }}>
        <h2 style={{ fontSize: 15, fontWeight: 700, marginBottom: 18 }}>Submit Root Cause Analysis</h2>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <label>
            <div style={{ color: 'var(--muted)', fontSize: 12, marginBottom: 4 }}>Incident Start</div>
            <input type="datetime-local" value={form.incident_start} onChange={e => set('incident_start', e.target.value)} />
          </label>
          <label>
            <div style={{ color: 'var(--muted)', fontSize: 12, marginBottom: 4 }}>Incident End</div>
            <input type="datetime-local" value={form.incident_end} onChange={e => set('incident_end', e.target.value)} />
          </label>
          <label>
            <div style={{ color: 'var(--muted)', fontSize: 12, marginBottom: 4 }}>Root Cause Category</div>
            <select value={form.root_cause_category} onChange={e => set('root_cause_category', e.target.value)}>
              {CATEGORIES.map(c => <option key={c}>{c}</option>)}
            </select>
          </label>
          <label>
            <div style={{ color: 'var(--muted)', fontSize: 12, marginBottom: 4 }}>Fix Applied</div>
            <textarea
              placeholder="Describe the fix that was applied..."
              value={form.fix_applied}
              onChange={e => set('fix_applied', e.target.value)}
            />
          </label>
          <label>
            <div style={{ color: 'var(--muted)', fontSize: 12, marginBottom: 4 }}>Prevention Steps</div>
            <textarea
              placeholder="Steps to prevent recurrence..."
              value={form.prevention_steps}
              onChange={e => set('prevention_steps', e.target.value)}
            />
          </label>

          {error && <p className="error">{error}</p>}

          <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
            <button onClick={onCancel} style={{ background: 'var(--surface2)', color: 'var(--muted)' }}>
              Cancel
            </button>
            <button onClick={handleSubmit} disabled={submitting} style={{ background: 'var(--accent)', color: '#fff' }}>
              {submitting ? 'Submitting...' : 'Submit RCA'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
