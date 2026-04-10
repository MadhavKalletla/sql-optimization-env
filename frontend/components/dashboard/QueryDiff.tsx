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
    <div className="rounded-xl border bg-white p-4 space-y-2">
      <h3 className="text-sm font-semibold text-gray-700">
        QUERY DIFF — Changes from Slow to Optimized
      </h3>

      {/* Removed lines from original */}
      {origLines
        .filter(l => !optSet.has(l.trim().toUpperCase()))
        .map((line, i) => (
          <div
            key={`removed-${i}`}
            className="text-sm font-mono bg-red-100 text-red-700 px-2 py-1 rounded"
          >
            - {line}
          </div>
        ))}

      {/* Added / unchanged lines in optimized */}
      {optLines.map((line, i) => {
        const isNew = !origSet.has(line.trim().toUpperCase())
        return (
          <div
            key={`opt-${i}`}
            className={`text-sm font-mono px-2 py-1 rounded ${
              isNew ? 'bg-green-100 text-green-700' : ''
            }`}
          >
            {isNew ? '+ ' : '  '}
            {line}
          </div>
        )
      })}
    </div>
  )
}
