'use client'

import { motion } from 'framer-motion'
import { ANTI_PATTERN_COLORS, ANTI_PATTERN_LABELS, AntiPatternType } from '@/lib/types'

export function AntiPatternBadge({ pattern }: { pattern: AntiPatternType }) {
  const color = ANTI_PATTERN_COLORS[pattern]

  return (
    <motion.span
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold"
      style={{
        backgroundColor: color + '20',
        color,
        border: `1px solid ${color}40`,
      }}
    >
      <span
        className="w-1.5 h-1.5 rounded-full animate-pulse"
        style={{ backgroundColor: color }}
      />
      {ANTI_PATTERN_LABELS[pattern]}
    </motion.span>
  )
}
