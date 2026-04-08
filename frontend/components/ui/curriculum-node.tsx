'use client'

import { motion } from 'framer-motion'
import { LEVEL_LABELS } from '@/lib/types'

interface CurriculumNodeProps {
  level: number
  active: number
  score?: number
}

export function CurriculumNode({ level, active, score }: CurriculumNodeProps) {
  const state = level < active ? 'done' : level === active ? 'active' : 'locked'
  const isActive = state === 'active'

  return (
    <motion.div
      className="flex flex-col items-center gap-2"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: level * 0.06, duration: 0.28 }}
    >
      <motion.div
        className="relative w-12 h-12 rounded-full flex items-center justify-center text-sm font-bold border-2 cursor-default"
        style={{
          backgroundColor: state === 'done' ? '#00E676' : isActive ? '#4A90D9' : '#1E2140',
          borderColor: state === 'done' ? '#00E676' : isActive ? '#00D4FF' : '#2A3050',
          color: state === 'locked' ? '#4A5568' : '#FFFFFF',
          boxShadow: isActive ? '0 0 18px #4A90D940' : 'none',
        }}
        animate={isActive ? { scale: [1, 1.04, 1] } : { scale: 1 }}
        transition={isActive ? { duration: 2.4, repeat: Infinity, ease: 'easeInOut' } : { duration: 0.2 }}
      >
        L{level}

        {isActive && (
          <motion.div
            className="absolute inset-0 rounded-full border-2 border-cyan-400"
            initial={{ scale: 1, opacity: 0.7 }}
            animate={{ scale: [1, 1.18], opacity: [0.7, 0] }}
            transition={{ duration: 1.8, repeat: Infinity, ease: 'easeOut' }}
          />
        )}
      </motion.div>

      <span className="text-xs" style={{ color: state === 'locked' ? '#4A5568' : '#8892A4' }}>
        {LEVEL_LABELS[level]}
      </span>

      {score !== undefined && (
        <span className="text-xs font-mono" style={{ color: score >= 0.7 ? '#00E676' : '#FFD740' }}>
          {(score * 100).toFixed(0)}%
        </span>
      )}
    </motion.div>
  )
}
