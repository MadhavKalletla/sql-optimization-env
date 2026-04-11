'use client'

import { MetricsPanel } from '@/components/dashboard/MetricsPanel'
import { motion, AnimatePresence } from 'framer-motion'
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'
import { SQLOptReward } from '@/lib/types'

interface RewardRadarProps {
  reward: SQLOptReward | null
  previous?: SQLOptReward | null
}

const DIMS = [
  { key: 'speedup_score', label: 'Speedup', max: 0.35 },
  { key: 'equivalence_score', label: 'Equivalence', max: 0.25 },
  { key: 'pattern_score', label: 'Pattern', max: 0.2 },
  { key: 'index_score', label: 'Index', max: 0.1 },
  { key: 'simplicity_score', label: 'Simplicity', max: 0.1 },
] as const

export function RewardRadar({ reward, previous }: RewardRadarProps) {
  const data = DIMS.map(d => ({
    dimension: d.label,
    current: reward ? Math.round((reward[d.key] / d.max) * 100) : 0,
    previous: previous ? Math.round((previous[d.key] / d.max) * 100) : 0,
    fullMark: 100,
  }))

  const totalScoreRounded = reward ? Math.round(reward.total * 100) : 0
  const displayScore = reward ? reward.total.toFixed(3) : "-"

  const scoreColor =
    totalScoreRounded >= 70 ? '#00E676'
    : totalScoreRounded >= 40 ? '#FFD740'
    : '#FF5252'

  return (
    <>
      {/* RADAR CARD */}
      <div
        className="rounded-xl p-5"
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          boxShadow: '0 0 20px #00000030',
        }}
      >
        {/* HEADER */}
        <div className="flex justify-between items-center mb-4">
          <h3
            className="text-xs font-semibold tracking-wide"
            style={{ color: 'var(--text-muted)' }}
          >
            REWARD BREAKDOWN
          </h3>

          <AnimatePresence mode="wait">
            <motion.div
              key={displayScore}
              initial={{ scale: 0.6, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.6, opacity: 0 }}
              className="text-2xl font-bold font-mono"
              style={{ color: scoreColor }}
            >
              {displayScore}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* CHART */}
        <div className="h-[240px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={data}>
              <PolarGrid stroke="#1E2140" />

              <PolarAngleAxis
                dataKey="dimension"
                tick={{ fill: '#8892A4', fontSize: 11 }}
              />

              {previous && (
                <Radar
                  name="Previous"
                  dataKey="previous"
                  stroke="#2A3050"
                  fill="#2A3050"
                  fillOpacity={0.25}
                />
              )}

              <Radar
                name="Current"
                dataKey="current"
                stroke="#4A90D9"
                fill="#4A90D9"
                fillOpacity={0.45}
                strokeWidth={2}
              />

              <Tooltip
                contentStyle={{
                  background: '#0F1229',
                  border: '1px solid #1E2140',
                  borderRadius: '8px',
                  fontSize: '12px',
                  color: '#E8EAF6',
                }}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 🔥 METRICS PANEL BELOW */}
      <MetricsPanel reward={reward} />
    </>
  )
}