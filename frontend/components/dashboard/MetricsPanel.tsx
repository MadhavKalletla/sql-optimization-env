'use client'

import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { SQLOptReward } from '@/lib/types'

function AnimatedNumber({
  value,
  decimals = 1,
  suffix = '',
}: {
  value: number
  decimals?: number
  suffix?: string
}) {
  const [display, setDisplay] = useState(value)
  const displayRef = useRef(value)
  const frameRef = useRef<number | null>(null)

  useEffect(() => {
    displayRef.current = display
  }, [display])

  useEffect(() => {
    const start = displayRef.current
    const end = value

    if (start === end) {
      setDisplay(end)
      return
    }

    const duration = 600
    const startTime = performance.now()

    if (frameRef.current !== null) {
      cancelAnimationFrame(frameRef.current)
    }

    const animate = (now: number) => {
      const progress = Math.min((now - startTime) / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      const nextValue = start + (end - start) * eased

      displayRef.current = nextValue
      setDisplay(nextValue)

      if (progress < 1) {
        frameRef.current = requestAnimationFrame(animate)
      } else {
        frameRef.current = null
      }
    }

    frameRef.current = requestAnimationFrame(animate)

    return () => {
      if (frameRef.current !== null) {
        cancelAnimationFrame(frameRef.current)
        frameRef.current = null
      }
    }
  }, [value])

  return (
    <span>
      {display.toFixed(decimals)}
      {suffix}
    </span>
  )
}

interface MetricsPanelProps {
  reward: SQLOptReward | null
}

export function MetricsPanel({ reward }: MetricsPanelProps) {
  const metrics = reward
    ? [
      {
        label: 'Speedup Ratio',
        value: reward.speedup_ratio,
        suffix: 'x',
        color:
          reward.speedup_ratio >= 10
            ? '#00E676'
            : reward.speedup_ratio >= 2
              ? '#FFD740'
              : '#FF5252',
        decimals: 1,
      },
      {
        label: 'Equivalence',
        value: (reward.equivalence_score / 0.25) * 100,
        suffix: '%',
        color: '#4A90D9',
        decimals: 0,
      },
      {
        label: 'Pattern Score',
        value: (reward.pattern_score / 0.2) * 100,
        suffix: '%',
        color: '#E040FB',
        decimals: 0,
      },
      {
        label: 'Index Quality',
        value: (reward.index_score / 0.1) * 100,
        suffix: '%',
        color: '#00D4FF',
        decimals: 0,
      },
    ]
    : []

  return (
    <div
      className="rounded-xl p-4 mt-4"
      style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-subtle)',
      }}
    >
      <div className="text-xs font-bold mb-3" style={{ color: 'var(--text-muted)' }}>
        LIVE METRICS
      </div>

      {reward ? (
        <div className="space-y-4">
          {metrics.map(({ label, value, suffix, color, decimals }) => (
            <div key={label}>
              <div className="flex justify-between mb-1">
                <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                  {label}
                </span>

                <motion.span
                  key={`${label}-${value}`}
                  className="text-sm font-bold font-mono"
                  style={{ color }}
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                >
                  <AnimatedNumber value={value} decimals={decimals} suffix={suffix} />
                </motion.span>
              </div>

              <div className="h-2 rounded-full overflow-hidden" style={{ background: '#1E2140' }}>
                <motion.div
                  className="h-full rounded-full"
                  initial={{ width: 0 }}
                  animate={{
                    width: `${value <= 100 ? value : Math.min(100, value * 10)}%`,
                  }}
                  transition={{ duration: 0.6 }}
                  style={{ background: `linear-gradient(90deg, ${color}80, ${color})` }}
                />
              </div>
            </div>
          ))}

          {reward.penalties < 0 && (
            <div
              className="mt-2 px-3 py-2 rounded-lg text-xs"
              style={{
                background: '#FF525215',
                color: '#FF5252',
                border: '1px solid #FF525230',
              }}
            >
              Penalties: {(reward.penalties * 100).toFixed(1)}%
            </div>
          )}
        </div>
      ) : (
        <div className="text-xs text-center py-4" style={{ color: 'var(--text-muted)' }}>
          Submit an optimization to see metrics
        </div>
      )}
    </div>
  )
}
