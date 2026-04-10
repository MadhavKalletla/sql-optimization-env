'use client'
import { motion, AnimatePresence } from 'framer-motion'
import Link from 'next/link'

interface EpisodeResultModalProps {
  isOpen: boolean
  passed: boolean
  score: number
  speedupRatio: number
  episodeNumber: number
  onNextEpisode: () => void
  onRetry: () => void
}

const PASS_MESSAGES = [
  'Outstanding optimization! The database thanks you.',
  'Index master! That query flies now.',
  'Excellent work — 50,000 beneficiaries will thank you.',
  'Production-grade optimization achieved!',
]

const FAIL_MESSAGES = [
  'Close! Check the anti-pattern hint and try again.',
  'The query still has room for improvement.',
  'Think about WHY the query is slow, not just what to change.',
  'Hint: Look at the EXPLAIN plan — what operation type is it?',
]

export function EpisodeResultModal({
  isOpen, passed, score, speedupRatio, episodeNumber, onNextEpisode, onRetry,
}: EpisodeResultModalProps) {
  const msg = passed
    ? PASS_MESSAGES[episodeNumber % PASS_MESSAGES.length]
    : FAIL_MESSAGES[episodeNumber % FAIL_MESSAGES.length]

  const scoreColor = passed ? '#00E676' : score >= 0.40 ? '#FFD740' : '#FF5252'
  const borderColor = passed ? '#00E676' : '#FF5252'
  const emoji = passed ? '🎉' : '💡'

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              position: 'fixed', inset: 0, zIndex: 100,
              background: 'rgba(0,0,0,0.75)',
              backdropFilter: 'blur(6px)',
            }}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.85, y: 40 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.85, y: 40 }}
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
            style={{
              position: 'fixed', inset: 0, zIndex: 101,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              padding: '1rem',
            }}
          >
            <div style={{
              background: '#0F1229',
              border: `2px solid ${borderColor}`,
              borderRadius: '20px',
              padding: '2.5rem',
              maxWidth: '420px',
              width: '100%',
              boxShadow: `0 0 60px ${borderColor}30, 0 0 120px ${borderColor}10`,
              textAlign: 'center',
            }}>
              {/* Emoji */}
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 0.6, repeat: passed ? 2 : 0 }}
                style={{ fontSize: '3rem', marginBottom: '1rem' }}
              >
                {emoji}
              </motion.div>

              {/* Title */}
              <div style={{
                fontSize: '1.4rem', fontWeight: 800,
                color: passed ? '#00E676' : '#FF5252',
                marginBottom: '0.5rem',
                letterSpacing: '0.05em',
              }}>
                {passed ? 'EPISODE PASSED!' : 'NOT QUITE YET'}
              </div>

              {/* Score */}
              <div style={{
                fontSize: '3rem', fontWeight: 900,
                color: scoreColor, fontFamily: 'monospace',
                lineHeight: 1, marginBottom: '0.25rem',
              }}>
                {Math.round(score * 100)}%
              </div>
              <div style={{ fontSize: '0.75rem', color: '#8892A4', marginBottom: '1.5rem' }}>
                {passed ? 'Need ≥70% to pass · ' : 'Score · '}
                Speedup: <strong style={{ color: '#4A90D9' }}>{speedupRatio.toFixed(1)}x</strong>
              </div>

              {/* Message */}
              <div style={{
                background: passed ? '#00E67610' : '#FF525210',
                border: `1px solid ${borderColor}30`,
                borderRadius: '10px',
                padding: '0.75rem 1rem',
                fontSize: '0.85rem',
                color: '#CBD5E1',
                marginBottom: '2rem',
                lineHeight: 1.5,
              }}>
                {msg}
              </div>

              {/* Buttons */}
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <Link href="/" style={{ flex: 1 }}>
                  <button style={{
                    width: '100%', padding: '0.75rem',
                    borderRadius: '10px', border: '1px solid #1E2140',
                    background: '#131528', color: '#8892A4',
                    fontSize: '0.875rem', fontWeight: 600, cursor: 'pointer',
                  }}>
                    ← Exit to Home
                  </button>
                </Link>

                <button
                  onClick={passed ? onNextEpisode : onRetry}
                  style={{
                    flex: 1, padding: '0.75rem',
                    borderRadius: '10px', border: 'none',
                    background: passed
                      ? 'linear-gradient(135deg, #00E676, #4A90D9)'
                      : 'linear-gradient(135deg, #FFD740, #FF9100)',
                    color: '#000',
                    fontSize: '0.875rem', fontWeight: 800, cursor: 'pointer',
                  }}
                >
                  {passed ? 'Next Episode →' : 'Try Again ↺'}
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
