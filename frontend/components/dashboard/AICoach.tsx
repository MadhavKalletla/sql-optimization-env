'use client'

import { motion } from 'framer-motion'
import { StepResult } from '@/lib/types'
import { ANTI_PATTERN_LABELS, ANTI_PATTERN_COLORS } from '@/lib/types'

interface AICoachProps {
  stepResult: StepResult
  onNextChallenge: () => void
}

export function AICoach({ stepResult, onNextChallenge }: AICoachProps) {
  const { reward_detail, observation } = stepResult
  
  // Generate plain English explanation
  const generateExplanation = () => {
    const pattern = observation.anti_pattern_hint || ''
    const table = extractTableName(observation.current_query)
    const speedupRatio = reward_detail.speedup_ratio || 1
    const rowCount = observation.row_count || 0
    const executionPlan = observation.execution_plan
    
    let explanation = `Your query optimization attempt has been analyzed. `
    
    // Pattern-specific explanations based on common anti-patterns
    if (pattern.toLowerCase().includes('full table scan') || pattern.toLowerCase().includes('missing index')) {
      explanation += `The original query was performing a FULL TABLE SCAN on ${table}, examining ${rowCount.toLocaleString()} rows. `
      if (executionPlan?.using_index) {
        explanation += `Your optimization successfully added an index (${executionPlan.using_index}), allowing the database to scan fewer rows efficiently. `
      } else {
        explanation += `Consider adding an index to improve scan performance. `
      }
    } else if (pattern.toLowerCase().includes('select *') || pattern.toLowerCase().includes('select star')) {
      explanation += `The original query used SELECT *, transferring all columns and consuming unnecessary bandwidth. `
      explanation += `Your optimization selected only the needed columns, reducing data transfer and improving performance. `
    } else if (pattern.toLowerCase().includes('n+1') || pattern.toLowerCase().includes('correlated')) {
      explanation += `The original query had a correlated subquery pattern, causing multiple database round trips. `
      explanation += `Your optimization replaced this with a more efficient JOIN operation, reducing query complexity. `
    } else if (pattern.toLowerCase().includes('cartesian') || pattern.toLowerCase().includes('cross product')) {
      explanation += `The original query was creating a Cartesian product due to missing JOIN conditions. `
      explanation += `Your optimization added proper JOIN conditions, eliminating unnecessary row combinations. `
    } else if (pattern.toLowerCase().includes('wildcard') || pattern.toLowerCase().includes('like')) {
      explanation += `The original query used a leading wildcard in LIKE, preventing index usage. `
      explanation += `Your optimization restructured the query to enable better index utilization. `
    } else {
      explanation += `The optimization focused on improving query structure and execution efficiency. `
    }
    
    // Add performance impact
    if (speedupRatio > 1.5) {
      explanation += `This resulted in a significant ${speedupRatio.toFixed(1)}x performance improvement! 🚀`
    } else if (speedupRatio > 1.1) {
      explanation += `This made your query ${speedupRatio.toFixed(1)}x faster. ✅`
    } else if (speedupRatio < 0.9) {
      explanation += `However, the query appears to be slower now - double-check your optimization approach. ⚠️`
    } else {
      explanation += `Performance remained similar, but code quality and maintainability improved. 📈`
    }
    
    return explanation
  }
  
  const extractTableName = (query: string): string => {
    const match = query.match(/FROM\s+(\w+)/i)
    return match ? match[1] : 'table'
  }
  
  const getPatternBadgeColor = (score: number) => {
    return score >= 0.7 ? '#00E676' : '#FF4C4C'
  }
  
  const getScoreColor = (score: number) => {
    return score >= 0.7 ? '#1E90FF' : '#FF4C4C'
  }
  
  // Normalize scores to 0-100 for display
  const normalizeScore = (score: number) => Math.round(score * 100)
  
  const rewardComponents = [
    { name: 'Speedup', value: normalizeScore(reward_detail.speedup_score), color: getScoreColor(reward_detail.speedup_score) },
    { name: 'Equivalence', value: normalizeScore(reward_detail.equivalence_score), color: getScoreColor(reward_detail.equivalence_score) },
    { name: 'Pattern', value: normalizeScore(reward_detail.pattern_score), color: getScoreColor(reward_detail.pattern_score) },
    { name: 'Index', value: normalizeScore(reward_detail.index_score), color: getScoreColor(reward_detail.index_score) },
    { name: 'Simplicity', value: normalizeScore(reward_detail.simplicity_score), color: getScoreColor(reward_detail.simplicity_score) },
  ]
  
  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5 }}
      className="p-5 rounded-xl space-y-4"
      style={{ 
        background: '#161B22', 
        border: '1px solid #30363D',
        maxHeight: '600px',
        overflowY: 'auto'
      }}
    >
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="text-2xl">🤖</div>
        <h3 className="text-lg font-bold" style={{ color: '#E8EAF6' }}>
          AI Coach
        </h3>
      </div>
      
      {/* Anti-pattern Badge */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-sm" style={{ color: '#8B949E' }}>Pattern:</span>
        <span
          className="px-3 py-1 rounded-full text-xs font-semibold"
          style={{
            background: getPatternBadgeColor(reward_detail.pattern_score) + '20',
            color: getPatternBadgeColor(reward_detail.pattern_score),
            border: `1px solid ${getPatternBadgeColor(reward_detail.pattern_score)}40`
          }}
        >
          {observation.anti_pattern_hint || 'Pattern Optimized'}
        </span>
        {reward_detail.pattern_score >= 0.7 && (
          <span className="text-xs" style={{ color: '#00E676' }}>✓ Fixed</span>
        )}
      </div>
      
      {/* Plain English Explanation */}
      <div className="space-y-2">
        <h4 className="text-sm font-semibold" style={{ color: '#E8EAF6' }}>
          What Happened:
        </h4>
        <p className="text-sm leading-relaxed" style={{ color: '#C9D1D9' }}>
          {generateExplanation()}
        </p>
      </div>
      
      {/* Reward Breakdown */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold" style={{ color: '#E8EAF6' }}>
          Score Breakdown:
        </h4>
        <div className="space-y-2">
          {rewardComponents.map((component) => (
            <div key={component.name} className="space-y-1">
              <div className="flex justify-between text-xs">
                <span style={{ color: '#8B949E' }}>{component.name}</span>
                <span style={{ color: component.color }}>{component.value}%</span>
              </div>
              <div className="w-full h-2 rounded-full" style={{ background: '#21262D' }}>
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${component.value}%` }}
                  transition={{ duration: 0.8, delay: 0.2 }}
                  className="h-full rounded-full"
                  style={{ background: component.color }}
                />
              </div>
            </div>
          ))}
        </div>
        
        {/* Total Score */}
        <div className="pt-2 border-t" style={{ borderColor: '#30363D' }}>
          <div className="flex justify-between items-center">
            <span className="text-sm font-semibold" style={{ color: '#E8EAF6' }}>
              Total Score:
            </span>
            <span 
              className="text-lg font-bold"
              style={{ color: getScoreColor(stepResult.reward) }}
            >
              {normalizeScore(stepResult.reward)}%
            </span>
          </div>
        </div>
      </div>
      
      {/* Performance Metrics */}
      <div className="space-y-2">
        <h4 className="text-sm font-semibold" style={{ color: '#E8EAF6' }}>
          Performance:
        </h4>
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="space-y-1">
            <div style={{ color: '#8B949E' }}>Execution Time:</div>
            <div style={{ color: '#E8EAF6' }}>{observation.execution_time_ms.toFixed(1)}ms</div>
          </div>
          <div className="space-y-1">
            <div style={{ color: '#8B949E' }}>Speedup Ratio:</div>
            <div style={{ color: reward_detail.speedup_ratio >= 1 ? '#00E676' : '#FF4C4C' }}>
              {reward_detail.speedup_ratio.toFixed(1)}x
            </div>
          </div>
          <div className="space-y-1">
            <div style={{ color: '#8B949E' }}>Rows Processed:</div>
            <div style={{ color: '#E8EAF6' }}>{observation.row_count.toLocaleString()}</div>
          </div>
          <div className="space-y-1">
            <div style={{ color: '#8B949E' }}>Index Used:</div>
            <div style={{ color: observation.execution_plan?.using_index ? '#00E676' : '#FF4C4C' }}>
              {observation.execution_plan?.using_index || 'None'}
            </div>
          </div>
        </div>
      </div>
      
      {/* Next Challenge Button */}
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={onNextChallenge}
        className="w-full py-3 px-4 rounded-lg text-sm font-semibold transition-colors"
        style={{
          background: 'linear-gradient(135deg, #1E90FF, #00D4FF)',
          color: '#FFFFFF',
          border: 'none',
          cursor: 'pointer'
        }}
      >
        🚀 Next Challenge
      </motion.button>
    </motion.div>
  )
}