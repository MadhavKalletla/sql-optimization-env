'use client'

import { motion } from 'framer-motion'
import { ExecutionPlan } from '@/lib/types'

interface ExplainTreeProps {
  plan: ExecutionPlan
  originalPlan?: ExecutionPlan
  timingMs: number
  originalTimingMs?: number
}

function PlanColumn({ plan, timingMs, label, color, bg }: { plan: ExecutionPlan, timingMs: number, label: string, color: string, bg: string }) {
  return (
    <div className="space-y-4">
      <h4 className="text-xs font-bold px-2" style={{ color }}>{label}</h4>
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center gap-3 p-4 rounded-lg"
        style={{
          background: bg,
          border: `1px solid ${color}30`,
        }}
      >
        <div
          className="w-3 h-3 rounded-full"
          style={{ backgroundColor: color }}
        />
        <span
          className="text-sm font-bold font-mono"
          style={{ color }}
        >
          {plan.operation}
        </span>
      </motion.div>

      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="p-3 rounded-lg" style={{ background: '#0F1229', border: '1px solid #1E2140' }}>
          <div style={{ color: 'var(--text-muted)' }}>Execution Time</div>
          <div className="font-mono font-bold mt-1" style={{ color }}>
            {timingMs.toFixed(2)} ms
          </div>
        </div>
        <div className="p-3 rounded-lg" style={{ background: '#0F1229', border: '1px solid #1E2140' }}>
          <div style={{ color: 'var(--text-muted)' }}>Rows Examined</div>
          <div className="font-mono font-bold mt-1">
            {plan.rows_examined.toLocaleString()}
          </div>
        </div>
        <div className="p-3 rounded-lg" style={{ background: '#0F1229', border: '1px solid #1E2140' }}>
          <div style={{ color: 'var(--text-muted)' }}>Rows Returned</div>
          <div className="font-mono font-bold mt-1">
            {plan.rows_returned.toLocaleString()}
          </div>
        </div>
        <div className="p-3 rounded-lg" style={{ background: '#0F1229', border: '1px solid #1E2140' }}>
          <div style={{ color: 'var(--text-muted)' }}>Cost</div>
          <div className="font-mono font-bold mt-1">
            {plan.cost_estimate.toFixed(2)}
          </div>
        </div>
      </div>
    </div>
  )
}

export function ExplainTree({ plan, originalPlan, timingMs, originalTimingMs }: ExplainTreeProps) {
  const isFullScan = plan.operation.includes('FULL TABLE SCAN')

  const color = isFullScan ? '#FF5252' : '#00E676'
  const bg = isFullScan ? '#FF525210' : '#00E67610'

  return (
    <div
      className="rounded-xl p-5 space-y-4"
      style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-subtle)',
        boxShadow: '0 0 20px #00000030',
      }}
    >
      {/* HEADER */}
      <h3
        className="text-xs font-semibold tracking-wide"
        style={{ color: 'var(--text-muted)' }}
      >
        EXPLAIN QUERY PLAN
      </h3>

      {originalPlan && originalTimingMs ? (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-6 relative">
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 rounded-full border border-slate-700 bg-slate-900 flex items-center justify-center text-slate-400 text-sm z-10 hidden md:flex">
              →
            </div>
            <PlanColumn 
              plan={originalPlan} 
              timingMs={originalTimingMs} 
              label="BEFORE (Slow)" 
              color="#FF5252" 
              bg="#FF525210" 
            />
            <PlanColumn 
              plan={plan} 
              timingMs={timingMs} 
              label="AFTER (Optimized)" 
              color="#00E676" 
              bg="#00E67610" 
            />
          </div>
          <div className="p-3 rounded-lg flex items-center justify-between text-xs" style={{ background: '#00E67610', border: '1px solid #00E67630' }}>
            <span style={{ color: 'var(--text-muted)' }}>Improvement:</span>
            <div className="flex gap-4 font-mono font-bold text-[#00E676]">
              <span>Speed: {originalTimingMs && timingMs > 0 ? (originalTimingMs / timingMs).toFixed(1) : '∞'}x faster</span>
              <span>Rows: {originalPlan.rows_examined.toLocaleString()} → {plan.rows_examined.toLocaleString()}</span>
            </div>
          </div>
        </div>
      ) : (
        <PlanColumn plan={plan} timingMs={timingMs} label="CURRENT PLAN" color={color} bg={bg} />
      )}
    </div>
  )
}