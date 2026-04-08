'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { AntiPatternType, ANTI_PATTERN_LABELS } from '@/lib/types'

interface QueryEditorProps {
  initialQuery: string
  onSubmit: (
    query: string,
    pattern: AntiPatternType,
    explanation: string,
    indexes: string[]
  ) => Promise<void>
  isLoading: boolean
}

interface EditorModules {
  CodeMirror: typeof import('@uiw/react-codemirror').default
  sql: typeof import('@codemirror/lang-sql').sql
  oneDark: typeof import('@codemirror/theme-one-dark').oneDark
}

const PATTERNS: AntiPatternType[] = [
  'MISSING_INDEX',
  'N_PLUS_ONE',
  'CARTESIAN_PRODUCT',
  'SELECT_STAR',
  'LEADING_WILDCARD',
  'IMPLICIT_CAST',
  'UNBOUNDED_AGGREGATION',
  'NONE',
]

export function QueryEditor({ initialQuery, onSubmit, isLoading }: QueryEditorProps) {
  const [query, setQuery] = useState(initialQuery)
  const [pattern, setPattern] = useState<AntiPatternType>('NONE')
  const [explanation, setExplanation] = useState('')
  const [indexes, setIndexes] = useState('')
  const [editorModules, setEditorModules] = useState<EditorModules | null>(null)

  useEffect(() => {
    setQuery(initialQuery)
    setPattern('NONE')
    setExplanation('')
    setIndexes('')
  }, [initialQuery])

  useEffect(() => {
    let cancelled = false

    const loadEditor = async () => {
      const [{ default: CodeMirror }, sqlModule, oneDarkModule] = await Promise.all([
        import('@uiw/react-codemirror'),
        import('@codemirror/lang-sql'),
        import('@codemirror/theme-one-dark'),
      ])

      if (!cancelled) {
        setEditorModules({
          CodeMirror,
          sql: sqlModule.sql,
          oneDark: oneDarkModule.oneDark,
        })
      }
    }

    void loadEditor()

    return () => {
      cancelled = true
    }
  }, [])

  const handleSubmit = useCallback(async () => {
    const indexList = indexes
      .split(';')
      .map(statement => statement.trim())
      .filter(Boolean)

    await onSubmit(query, pattern, explanation, indexList)
  }, [query, pattern, explanation, indexes, onSubmit])

  const editorExtensions = useMemo(
    () => (editorModules ? [editorModules.sql()] : []),
    [editorModules]
  )

  return (
    <div
      className="rounded-xl overflow-hidden"
      style={{
        border: '1px solid var(--border-subtle)',
        background: 'var(--bg-card)',
      }}
    >
      <div
        className="px-4 py-2 text-xs font-semibold"
        style={{
          background: '#0F1229',
          color: 'var(--text-muted)',
          borderBottom: '1px solid var(--border-subtle)',
        }}
      >
        Optimized Query Editor
      </div>

      {editorModules ? (
        <editorModules.CodeMirror
          value={query}
          height="200px"
          extensions={editorExtensions}
          theme={editorModules.oneDark}
          onChange={setQuery}
        />
      ) : (
        <div className="p-4" style={{ background: '#0B1020' }}>
          <div className="mb-3 text-xs" style={{ color: 'var(--text-muted)' }}>
            Loading editor… You can already edit in the lightweight fallback below.
          </div>
          <textarea
            value={query}
            onChange={e => setQuery(e.target.value)}
            className="w-full rounded-lg p-3 text-sm outline-none resize-y min-h-[200px]"
            style={{
              background: '#0F1229',
              border: '1px solid #1E2140',
              color: '#E8EAF6',
            }}
          />
        </div>
      )}

      <div className="p-5 space-y-4">
        <div className="space-y-1">
          <label className="text-xs font-semibold" style={{ color: 'var(--text-muted)' }}>
            Detected Anti-pattern
          </label>

          <select
            value={pattern}
            onChange={e => setPattern(e.target.value as AntiPatternType)}
            className="w-full px-3 py-2 rounded-lg text-sm outline-none"
            style={{
              background: '#0F1229',
              border: '1px solid #1E2140',
              color: '#E8EAF6',
            }}
          >
            {PATTERNS.map(patternOption => (
              <option key={patternOption} value={patternOption}>
                {ANTI_PATTERN_LABELS[patternOption]}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-1">
          <label className="text-xs font-semibold" style={{ color: 'var(--text-muted)' }}>
            Explanation
          </label>

          <textarea
            value={explanation}
            onChange={e => setExplanation(e.target.value)}
            placeholder="Explain your optimization..."
            className="w-full px-3 py-2 rounded-lg text-sm outline-none resize-none"
            rows={3}
            style={{
              background: '#0F1229',
              border: '1px solid #1E2140',
              color: '#E8EAF6',
            }}
          />
        </div>

        <div className="space-y-1">
          <label className="text-xs font-semibold" style={{ color: 'var(--text-muted)' }}>
            Index Statements (optional)
          </label>

          <input
            value={indexes}
            onChange={e => setIndexes(e.target.value)}
            placeholder="CREATE INDEX ...; CREATE INDEX ..."
            className="w-full px-3 py-2 rounded-lg text-sm outline-none"
            style={{
              background: '#0F1229',
              border: '1px solid #1E2140',
              color: '#E8EAF6',
            }}
          />
        </div>

        <motion.button
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          onClick={() => void handleSubmit()}
          disabled={isLoading}
          className="w-full py-3 rounded-lg text-sm font-bold transition-all"
          style={{
            background: isLoading ? '#1E2140' : 'linear-gradient(135deg, #4A90D9, #00D4FF)',
            color: isLoading ? 'var(--text-muted)' : '#fff',
            cursor: isLoading ? 'not-allowed' : 'pointer',
          }}
        >
          {isLoading ? '💡 Submitting...' : '⚡ Submit Optimization'}
        </motion.button>
      </div>
    </div>
  )
}
