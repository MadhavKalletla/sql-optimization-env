'use client'

import { useMemo } from 'react'

interface QueryDiffProps {
  original: string
  optimized: string
}

function normLines(sql: string): string[] {
  return sql
    .split('\n')
    .map(l => l.trimEnd())
    .filter(l => l.trim() !== '')
}

export function QueryDiff({ original, optimized }: QueryDiffProps) {
  const origLines = useMemo(() => normLines(original), [original])
  const optLines = useMemo(() => normLines(optimized), [optimized])

  const origSet = new Set(origLines.map(l => l.trim().toUpperCase()))
  const optSet = new Set(optLines.map(l => l.trim().toUpperCase()))

  return (
    <div
      className="rounded-xl overflow-hidden"
      style={{ border: '1px solid #1E2140', background: '#0B0F20' }}
    >
      <div
        className="px-4 py-2 text-xs font-bold flex items-center gap-2"
        style={{ background: '#0F1229', color: '#8892A4', borderBottom: '1px solid #1E2140' }}
      >
        <span style={{ color: '#4A90D9' }}>⟷</span>
        QUERY DIFF — Changes from Slow to Optimized
      </div>
      <div className="p-3 font-mono text-xs space-y-0.5 overflow-x-auto"
        style={{ background: '#0B0F20' }}>

        {origLines.filter(l => !optSet.has(l.trim().toUpperCase())).map((line, i) => (
          <div key={'rem' + i} style={{
            background: '#FF52521A',
            color: '#FF7070',
            padding: '2px 10px',
            borderLeft: '3px solid #FF5252',
            borderRadius: '2px',
          }}>
            − {line}
          </div>
        ))}

        {optLines.map((line, i) => {
          const isNew = !origSet.has(line.trim().toUpperCase())
          return (
            <div key={'opt' + i} style={{
              background: isNew ? '#00E6761A' : 'transparent',
              color: isNew ? '#00E676' : '#6B7A99',
              padding: '2px 10px',
              borderLeft: isNew ? '3px solid #00E676' : '3px solid transparent',
              borderRadius: '2px',
            }}>
              {isNew ? '+ ' : '  '}{line}
            </div>
          )
        })}

        {origLines.filter(l => !optSet.has(l.trim().toUpperCase())).length === 0 &&
         optLines.filter(l => !origSet.has(l.trim().toUpperCase())).length === 0 && (
          <div style={{ color: '#FFD740', padding: '8px 10px', textAlign: 'center' }}>
            ⚠ Query is identical to the original — no changes detected
          </div>
        )}
      </div>
    </div>
  )
}
