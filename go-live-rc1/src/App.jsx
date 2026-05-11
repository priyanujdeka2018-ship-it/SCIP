import React from 'react'
import './liquidGlassTokens.css'

const cards = [
  {
    title: 'Live Pulse',
    subtitle: 'Current Signal · Month Movement · Risk & Action',
    body: 'Operational entry point for live collections signal, movement, risk, and action queues.'
  },
  {
    title: 'Narratives',
    subtitle: 'Story · Portfolio · Dues · Advance · Roadmap',
    body: 'Executive narrative path for board-safe, lineage-backed explanations and roadmap views.'
  }
]

export default function App() {
  return (
    <main style={{
      minHeight: '100vh',
      padding: '48px',
      fontFamily: 'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      background: 'linear-gradient(135deg, #0f172a, #111827)',
      color: '#f8fafc'
    }}>
      <section style={{ maxWidth: 1100, margin: '0 auto' }}>
        <p style={{ letterSpacing: '0.16em', textTransform: 'uppercase', color: '#93c5fd' }}>
          Sobha Collections Intelligence Platform
        </p>

        <h1 style={{ fontSize: 48, lineHeight: 1.05, margin: '16px 0' }}>
          SCIP Go-Live Release Candidate
        </h1>

        <p style={{ maxWidth: 760, color: '#cbd5e1', fontSize: 18 }}>
          Release candidate shell preserving the locked Liquid Glass two-door model:
          Live Pulse and Narratives only. Runtime overlays for Batches 13–18 are staged
          under the release branch.
        </p>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: 24,
          marginTop: 40
        }}>
          {cards.map((card) => (
            <article key={card.title} style={{
              border: '1px solid rgba(255,255,255,0.18)',
              borderRadius: 24,
              padding: 28,
              background: 'rgba(255,255,255,0.08)',
              backdropFilter: 'blur(18px)',
              boxShadow: '0 20px 60px rgba(0,0,0,0.28)'
            }}>
              <h2 style={{ fontSize: 28, margin: 0 }}>{card.title}</h2>
              <p style={{ color: '#93c5fd', marginTop: 10 }}>{card.subtitle}</p>
              <p style={{ color: '#d1d5db', lineHeight: 1.6 }}>{card.body}</p>
            </article>
          ))}
        </div>

        <section style={{
          marginTop: 40,
          padding: 24,
          borderRadius: 20,
          background: 'rgba(15,23,42,0.72)',
          border: '1px solid rgba(148,163,184,0.22)'
        }}>
          <h3 style={{ marginTop: 0 }}>Release status</h3>
          <ul style={{ color: '#d1d5db', lineHeight: 1.8 }}>
            <li>Batch 13 runtime baseline applied.</li>
            <li>Batch 14–17 governance overlays applied.</li>
            <li>Batch 18 analytics transformation overlay staged but not automatically exposed.</li>
            <li>Go-live consolidation pack uploaded under docs/go_live.</li>
          </ul>
        </section>
      </section>
    </main>
  )
}
