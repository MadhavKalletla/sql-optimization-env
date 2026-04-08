'use client'

import { AnimatePresence, motion } from 'framer-motion'
import { StepResult } from '@/lib/types'

interface EpisodeHistoryProps {
  history: StepResult[]
  currentLevel: number
}

export function EpisodeHistory({ history, currentLevel }: EpisodeHistoryProps) {
  return (
    <div
      className="p-4 rounded-xl overflow-y-auto"
      style={{
        background: '#0f172a',
        border: '1px solid #1e2140',
        maxHeight: '400px',
        color: '#cbd5e1',
      }}
    >
      <div className="text-xs font-bold mb-4" style={{ color: 'var(--text-muted)' }}>
        EPISODE HISTORY
      </div>

      <div className="space-y-3">
        <AnimatePresence>
          {history.map((step, idx) => {
            const reward = step.reward_detail
            const score = reward.total
            
            const badgeColor = score >= 0.70 ? '#00E676' : score >= 0.40 ? '#FFD740' : '#FF5252'

            return (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-3 rounded-lg text-sm flex items-center justify-between"
                style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)' }}
              >
                <div className="flex items-center gap-3">
                  <span className="font-mono" style={{ color: 'var(--text-muted)' }}>
                    #{idx + 1}
                  </span>
                  
                  <span 
                    className="px-2 py-0.5 rounded text-xs font-bold"
                    style={{ background: `${badgeColor}20`, color: badgeColor }}
                  >
                    {(score * 100).toFixed(0)}%
                  </span>
                </div>

                <div className="flex items-center gap-4 text-xs text-right">
                  <div className="flex flex-col">
                    <span style={{ color: 'var(--text-muted)' }}>Speedup</span>
                    <span className="font-mono font-bold" style={{ color: '#4A90D9' }}>{reward.speedup_ratio.toFixed(1)}x</span>
                  </div>

                  <div className="flex flex-col">
                    <span style={{ color: 'var(--text-muted)' }}>Pattern</span>
                    <span className="font-bold text-[10px]" style={{ color: reward.hack_detected ? '#FF5252' : '#E040FB' }}>
                      {reward.hack_detected ? 'HACK DETECTED' : (step.info?.identified_pattern as string || 'N/A')}
                    </span>
                  </div>
                  
                  {step.done && (
                    <div className="flex items-center justify-center">
                      <span className="w-2 h-2 rounded-full" style={{ background: '#00E676' }} />
                    </div>
                  )}
                </div>
              </motion.div>
            )
          })}
        </AnimatePresence>
        
        {history.length === 0 && (
          <div className="text-center py-6 text-xs" style={{ color: 'var(--text-muted)' }}>
            No steps recorded yet.
          </div>
        )}
      </div>
    </div>
  )
}
