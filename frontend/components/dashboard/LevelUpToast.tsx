'use client'

import { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface LevelUpToastProps {
  fromLevel: number
  toLevel: number
  onDismiss: () => void
}

export function LevelUpToast({ fromLevel, toLevel, onDismiss }: LevelUpToastProps) {
  useEffect(() => {
    if (fromLevel >= toLevel) return

    const timer = setTimeout(() => {
      onDismiss()
    }, 4000)

    return () => clearTimeout(timer)
  }, [fromLevel, toLevel, onDismiss])

  return (
    <AnimatePresence>
      {fromLevel < toLevel && (
        <motion.div
          initial={{ opacity: 0, y: -50 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -50 }}
          className="fixed top-8 right-8 z-50 p-4 rounded-xl shadow-2xl flex items-center gap-3"
          style={{
            background: 'var(--bg-card)',
            border: '2px solid transparent',
            backgroundImage: 'linear-gradient(var(--bg-card), var(--bg-card)), linear-gradient(135deg, #4A90D9, #00D4FF)',
            backgroundOrigin: 'border-box',
            backgroundClip: 'padding-box, border-box',
          }}
        >
          <span className="text-2xl">🎉</span>
          <div>
            <div className="font-bold text-white">Level Up!</div>
            <div className="text-sm" style={{ color: 'var(--text-muted)' }}>
              Level {fromLevel} → Level {toLevel}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
