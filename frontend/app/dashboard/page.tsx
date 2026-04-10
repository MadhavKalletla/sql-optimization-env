'use client'
export const dynamic = 'force-static'
import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { useEnvironment } from '@/hooks/useEnvironment'
import { useCurriculum } from '@/hooks/useCurriculum'
import { QueryEditor } from '@/components/dashboard/QueryEditor'
import { RewardRadar } from '@/components/dashboard/RewardRadar'
import { QueryDiff } from '@/components/dashboard/QueryDiff'
import { ExplainTree } from '@/components/dashboard/ExplainTree'
import { CurriculumNode } from '@/components/ui/curriculum-node'
import { AntiPatternType, LEVEL_LABELS } from '@/lib/types'
import { EpisodeHistory } from '@/components/dashboard/EpisodeHistory'
import { LevelUpToast } from '@/components/dashboard/LevelUpToast'
import { RobotWidget } from '@/components/ui/RobotWidget'

// curriculum_level here means the MINIMUM level required to access this task
const TASK_OPTIONS = [
  { id: 'pds_select_star',            label: 'PDS: Avoid SELECT *',          difficulty: 'Easy',   minLevel: 1 },
  { id: 'mgnrega_count',              label: 'MGNREGA: Column Reduction',    difficulty: 'Easy',   minLevel: 1 },
  { id: 'gst_missing_index',          label: 'GST: Add Missing Index',        difficulty: 'Easy',   minLevel: 2 },
  { id: 'railway_simple_filter',      label: 'Railway: Filter Index',         difficulty: 'Easy',   minLevel: 2 },
  { id: 'railway_missing_index',      label: 'Railway: Journey Date Index',   difficulty: 'Medium', minLevel: 2 },
  { id: 'gst_unbounded_aggregation',  label: 'GST: Unbounded Aggregation',    difficulty: 'Medium', minLevel: 2 },
  { id: 'gst_n_plus_one',            label: 'GST: N+1 Correlated Query',     difficulty: 'Medium', minLevel: 3 },
  { id: 'pds_cartesian',             label: 'PDS: Cartesian Product Fix',    difficulty: 'Medium', minLevel: 3 },
  { id: 'mgnrega_wildcard',          label: 'MGNREGA: Wildcard LIKE Fix',    difficulty: 'Medium', minLevel: 3 },
  { id: 'pds_n_plus_one',            label: 'PDS: N+1 Beneficiary Query',    difficulty: 'Hard',   minLevel: 4 },
  { id: 'mgnrega_implicit_cast',     label: 'MGNREGA: Implicit Type Cast',   difficulty: 'Hard',   minLevel: 4 },
  { id: 'gst_multi_join',            label: 'GST: Multi-Table Join',         difficulty: 'Hard',   minLevel: 4 },
]

const dotColor = (d: string) => d === 'Easy' ? '#22c55e' : d === 'Medium' ? '#f59e0b' : '#ef4444'

function DashboardLoader({ label }: { label: string }) {
  return (
    <div
      className="min-h-[360px] rounded-xl flex flex-col items-center justify-center text-center px-6"
      style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)' }}
    >
      <div
        className="mb-4 h-10 w-10 rounded-full border-2 border-t-transparent animate-spin"
        style={{ borderColor: '#4A90D9', borderTopColor: 'transparent' }}
      />
      <div className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
        Preparing environment
      </div>
      <p className="mt-2 text-xs max-w-sm" style={{ color: 'var(--text-muted)' }}>
        {label}
      </p>
    </div>
  )
}

export default function DashboardPage() {
  const {
    observation,
    stepResult,
    history,
    isLoading,
    error,
    isEpisodeDone,
    reset,
    step,
    previousReward,
    originalPlan,
  } = useEnvironment()

  const { envState, isBackendOnline, isRefreshing } = useCurriculum(8000)
  const [selectedTask, setSelectedTask] = useState('pds_select_star')
  const [prevLevel, setPrevLevel] = useState<number | null>(null)
  const [showLevelUp, setShowLevelUp] = useState(false)
  const [lockedWarning, setLockedWarning] = useState<string | null>(null)
  const didInitializeRef = useRef(false)
  const [hintLevel, setHintLevel] = useState(0)
  const hintTimerRef = useRef<NodeJS.Timeout[]>([])

  const currentLevel = envState?.curriculum_level ?? 1

  useEffect(() => {
    if (prevLevel === null) {
      setPrevLevel(envState?.curriculum_level ?? 1)
      return
    }

    if (envState?.curriculum_level && envState.curriculum_level > prevLevel) {
      setShowLevelUp(true)
      setPrevLevel(envState.curriculum_level)
    }
  }, [envState?.curriculum_level])

  useEffect(() => {
    if (didInitializeRef.current) return
    didInitializeRef.current = true
    void reset(selectedTask)
  }, [reset, selectedTask])

  useEffect(() => {
    setHintLevel(0)
    hintTimerRef.current.forEach(t => clearTimeout(t))
    hintTimerRef.current = [
      setTimeout(() => setHintLevel(1), 30000),
      setTimeout(() => setHintLevel(2), 60000),
    ]
    return () => hintTimerRef.current.forEach(t => clearTimeout(t))
  }, [observation?.task_id])

  const handleTaskChange = async (taskId: string) => {
    const task = TASK_OPTIONS.find(t => t.id === taskId)
    if (task && task.minLevel > currentLevel) {
      setLockedWarning(`🔒 "${task.label}" requires Level ${task.minLevel}. Earn it by scoring ≥70% three times in a row!`)
      setTimeout(() => setLockedWarning(null), 4000)
      return
    }
    setSelectedTask(taskId)
    await reset(taskId)
  }

  const handleSubmit = async (
    query: string,
    pattern: AntiPatternType,
    explanation: string,
    indexes: string[]
  ) => {
    hintTimerRef.current.forEach(t => clearTimeout(t))
    setHintLevel(0)
    hintTimerRef.current = [
      setTimeout(() => setHintLevel(1), 30000),
      setTimeout(() => setHintLevel(2), 60000),
    ]
    await step(query, pattern, explanation, indexes)
  }

  const isInitialLoading = !observation && (isLoading || !error)
  const lastScore = stepResult?.reward ?? 0
  const episodePassed = isEpisodeDone && lastScore >= 0.70

  const autoAdvanceRef = useRef<number | null>(null)

  useEffect(() => {
    if (episodePassed) {
      autoAdvanceRef.current = window.setTimeout(() => {
        void reset()
      }, 3000)
    }

    return () => {
      if (autoAdvanceRef.current) {
        clearTimeout(autoAdvanceRef.current)
      }
    }
  }, [episodePassed, reset])

  return (
    <>
      {showLevelUp && (
        <LevelUpToast
          fromLevel={prevLevel ?? 1}
          toLevel={envState?.curriculum_level ?? 1}
          onDismiss={() => setShowLevelUp(false)}
        />
      )}
      <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg-primary)' }}>
        {/* ─── HEADER ─── */}
        <header
          className="flex items-center justify-between px-8 py-4"
          style={{ background: 'var(--bg-panel)', borderBottom: '1px solid var(--border-subtle)' }}
        >
          <div className="flex items-center gap-5">
            <div className="flex items-center gap-2">
              <div
                className="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-extrabold"
                style={{ background: 'linear-gradient(135deg,#4A90D9,#00D4FF)', color: '#fff' }}
              >
                SQL
              </div>
              <span className="font-bold text-sm" style={{ color: 'var(--text-primary)' }}>
                Optimization Dashboard
              </span>
            </div>

            <span
              className="text-xs px-3 py-1 rounded-full font-semibold"
              style={{
                background: 'linear-gradient(90deg,#4A90D920,#00D4FF15)',
                color: '#4A90D9',
                border: '1px solid #4A90D940',
              }}
            >
              Level {currentLevel} — {LEVEL_LABELS[currentLevel]}
            </span>

            <span
              className="text-xs px-3 py-1 rounded-full"
              style={{
                background: isBackendOnline === null ? '#FFD74020' : isBackendOnline ? '#00E67620' : '#FF525220',
                color: isBackendOnline === null ? '#FFD740' : isBackendOnline ? '#00E676' : '#FF5252',
                border: `1px solid ${isBackendOnline === null ? '#FFD74040' : isBackendOnline ? '#00E67640' : '#FF525240'}`,
              }}
            >
              {isBackendOnline === null
                ? '● Checking backend…'
                : isBackendOnline
                  ? isRefreshing ? '● Syncing…' : '● Backend online'
                  : '● Backend offline'}
            </span>
          </div>

          <div className="flex items-center gap-4">
            {/* Task selector — visually groups locked options */}
            <div className="relative">
              <select
                value={selectedTask}
                onChange={e => void handleTaskChange(e.target.value)}
                className="text-xs px-3 py-2 rounded-lg outline-none pr-8 appearance-none"
                style={{
                  background: '#0F1229',
                  border: '1px solid #1E2140',
                  color: '#E8EAF6',
                  minWidth: 240,
                }}
              >
                {TASK_OPTIONS.map(task => {
                  const locked = task.minLevel > currentLevel
                  return (
                    <option key={task.id} value={task.id} disabled={locked}>
                      {locked ? '🔒 ' : ''}
                      {task.label} ({task.difficulty})
                    </option>
                  )
                })}
              </select>
              <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: '#8892a4' }}>▾</div>
            </div>

            <div className="flex items-center gap-3 text-xs" style={{ color: 'var(--text-muted)' }}>
              <span>Ep: <strong style={{ color: '#E8EAF6' }}>{envState?.total_episodes ?? 0}</strong></span>
              <span>Steps: <strong style={{ color: '#E8EAF6' }}>{history?.length ?? 0}</strong></span>
            </div>
          </div>
        </header>

        {/* ─── CURRICULUM PROGRESS BAR ─── */}
        <div
          className="flex justify-center items-center gap-8 py-3 px-8"
          style={{ background: 'var(--bg-panel)', borderBottom: '1px solid var(--border-subtle)', position: 'relative' }}
        >
          {/* Progress line */}
          <div className="absolute left-[10%] right-[10%] top-1/2 h-0.5" style={{ background: 'var(--border-subtle)' }} />
          <motion.div
            className="absolute left-[10%] top-1/2 h-0.5"
            style={{ background: 'linear-gradient(90deg,#4A90D9,#00D4FF)', originX: 0 }}
            initial={{ width: 0 }}
            animate={{ width: `${((currentLevel - 1) / 4) * 80}%` }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
          />
          {[1, 2, 3, 4, 5].map(level => (
            <CurriculumNode key={level} level={level} active={currentLevel} />
          ))}
        </div>

        {/* ─── LOCKED TASK WARNING ─── */}
        <AnimatePresence>
          {lockedWarning && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="mx-8 mt-3 p-3 rounded-lg text-xs flex items-center gap-2"
              style={{ background: '#1e1400', border: '1px solid #f59e0b60', color: '#fcd34d' }}
            >
              {lockedWarning}
            </motion.div>
          )}
        </AnimatePresence>

        {/* ─── API ERROR ─── */}
        {error && (
          <div className="mx-8 mt-3 p-3 rounded-lg text-xs" style={{ background: '#FF525215', color: '#FF5252', border: '1px solid #FF525240' }}>
            ⚠ {error}
          </div>
        )}

        {/* ─── MAIN CONTENT ─── */}
        <div className="flex-1 grid grid-cols-1 xl:grid-cols-[300px_1fr_300px] gap-5 p-5">
          {/* LEFT: Task info */}
          <div className="space-y-4">
            {observation ? (
              <>
                <div
                  className="p-5 rounded-xl"
                  style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)' }}
                >
                  <div className="text-xs font-bold mb-3 flex items-center gap-2">
                    <span style={{ color: '#FFD740' }}>TASK GOAL</span>
                    <span
                      className="px-2 py-0.5 rounded text-xs"
                      style={{
                        background: dotColor(TASK_OPTIONS.find(t => t.id === observation.task_id)?.difficulty ?? 'Easy') + '22',
                        color: dotColor(TASK_OPTIONS.find(t => t.id === observation.task_id)?.difficulty ?? 'Easy'),
                      }}
                    >
                      {TASK_OPTIONS.find(t => t.id === observation.task_id)?.difficulty ?? ''}
                    </span>
                  </div>
                  <p className="text-sm leading-relaxed">{observation.goal}</p>
                </div>

                {hintLevel >= 1 && observation.anti_pattern_hint && (
                  <div className="mt-3 p-3 rounded-lg text-xs" style={{ background: '#1e293b', color: '#cbd5e1' }}>
                    ■ HINT {hintLevel === 1 ? '1' : '1 + 2'} (unlocked after {hintLevel === 1 ? '30' : '60'}s)
                    <div className="mt-1">{observation.anti_pattern_hint}</div>
                    {hintLevel >= 2 && (
                      <div className="mt-2 text-[10px]" style={{ color: '#94a3b8' }}>
                        Bonus: Try the Detected Anti-pattern dropdown — selecting correctly gives +20% score.
                      </div>
                    )}
                  </div>
                )}

                {/* DB stats */}
                <div
                  className="p-4 rounded-xl"
                  style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)' }}
                >
                  <div className="text-xs font-bold mb-2" style={{ color: 'var(--text-muted)' }}>DATABASE TABLES</div>
                  {Object.entries(observation.db_stats ?? {}).map(([table, info]: [string, any]) => (
                    <div key={table} className="flex justify-between text-xs mt-1">
                      <span style={{ color: 'var(--text-muted)' }}>{table}</span>
                      <span style={{ color: '#E8EAF6' }}>{info?.row_count?.toLocaleString() ?? '?'} rows</span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <DashboardLoader label="Loading task goal and backend state…" />
            )}
          </div>

          {/* CENTER: Query editor */}
          <div className="space-y-4 min-h-[360px]">
            {observation ? (
              <>
                <div className="rounded-xl overflow-hidden" style={{ border: '1px solid var(--border-subtle)' }}>
                  <div className="px-4 py-2 text-xs flex items-center justify-between" style={{ background: '#0F1229', color: 'var(--text-muted)' }}>
                    <span>Current Query (Slow)</span>
                    <span style={{ color: '#FF5252' }}>⏱ {observation.execution_time_ms.toFixed(1)} ms</span>
                  </div>
                  <pre className="p-4 text-xs overflow-x-auto" style={{ background: 'var(--bg-card)', color: '#E8EAF6' }}>
                    {observation.current_query}
                  </pre>
                </div>

                <AnimatePresence>
                  {/* ─── PASS BANNER ─── */}
                  {episodePassed && (
                    <motion.div
                      key="pass-banner"
                      initial={{ opacity: 0, scale: 0.97 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0 }}
                      style={{ background: '#14532d', border: '1px solid #22c55e', borderRadius: 8, padding: '12px 16px', marginBottom: 12, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
                    >
                      <span style={{ color: '#86efac', fontWeight: 600 }}>
                        ✅ Score: {(lastScore * 100).toFixed(0)}% — Excellent! Auto-advancing in 3 seconds...
                      </span>
                      <button
                        onClick={() => void reset()}
                        style={{ background: '#22c55e', color: '#000', border: 'none', borderRadius: 6, padding: '6px 16px', fontWeight: 700, cursor: 'pointer' }}
                      >
                        Next Episode →
                      </button>
                    </motion.div>
                  )}

                  {/* ─── RETRY BANNER ─── */}
                  {isEpisodeDone && !episodePassed && (
                    <motion.div
                      key="retry-banner"
                      initial={{ opacity: 0, scale: 0.97 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0 }}
                      style={{ background: '#422006', border: '1px solid #f59e0b', borderRadius: 8, padding: '12px 16px', marginBottom: 12, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
                    >
                      <span style={{ color: '#fcd34d', fontWeight: 600 }}>
                        ⚠️ Score: {(lastScore * 100).toFixed(0)}% — Need ≥70% to advance. Keep optimizing!
                      </span>
                      <button
                        onClick={() => void reset(selectedTask)}
                        style={{ background: '#f59e0b', color: '#000', border: 'none', borderRadius: 6, padding: '6px 16px', fontWeight: 700, cursor: 'pointer' }}
                      >
                        Retry Task ↺
                      </button>
                    </motion.div>
                  )}

                  <QueryEditor
                    key={observation.task_id}
                    initialQuery={observation.current_query}
                    onSubmit={handleSubmit}
                    isLoading={isLoading}
                  />

                  {stepResult && observation && (
                    <QueryDiff
                      original={observation.current_query}
                      optimized={stepResult.observation.current_query}
                    />
                  )}
                </AnimatePresence>
              </>
            ) : isInitialLoading ? (
              <DashboardLoader label="Waking the training environment. HuggingFace cold-starts can take 30–60s…" />
            ) : (
              <DashboardLoader label="No observation yet. Select a task above or wait for backend." />
            )}
          </div>

          {/* RIGHT: Metrics */}
          <div className="space-y-4">
            <RewardRadar reward={stepResult?.reward_detail ?? null} previous={previousReward} />

            {observation ? (
              <ExplainTree
                plan={stepResult?.observation.execution_plan ?? observation.execution_plan}
                originalPlan={originalPlan ?? undefined}
                timingMs={stepResult?.observation.execution_time_ms ?? observation.execution_time_ms}
                originalTimingMs={observation.execution_time_ms}
              />
            ) : (
              <DashboardLoader label="Execution plan appears after backend responds." />
            )}

            <EpisodeHistory
              history={history}
              currentLevel={currentLevel}
            />
          </div>
        </div>

        {/* ─── CSS Robot Widget ─── */}
        <RobotWidget />
      </div>
    </>
  )
}
