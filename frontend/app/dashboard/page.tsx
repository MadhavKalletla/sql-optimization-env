'use client'
export const dynamic = 'force-static'
import { useEffect, useRef, useState } from 'react'
import { AnimatePresence } from 'framer-motion'
import { useEnvironment } from '@/hooks/useEnvironment'
import { useCurriculum } from '@/hooks/useCurriculum'
import { QueryEditor } from '@/components/dashboard/QueryEditor'
import { RewardRadar } from '@/components/dashboard/RewardRadar'
import { ExplainTree } from '@/components/dashboard/ExplainTree'
import { CurriculumNode } from '@/components/ui/curriculum-node'
import { AntiPatternType, LEVEL_LABELS } from '@/lib/types'
import { EpisodeHistory } from '@/components/dashboard/EpisodeHistory'
import { LevelUpToast } from '@/components/dashboard/LevelUpToast'

const TASK_OPTIONS = [
  { id: 'pds_select_star', label: 'PDS SELECT *', difficulty: 'Easy' },
  { id: 'gst_missing_index', label: 'GST Missing Index', difficulty: 'Easy' },
  { id: 'railway_simple_filter', label: 'Railway Filter', difficulty: 'Easy' },
  { id: 'gst_n_plus_one', label: 'GST N+1 Query', difficulty: 'Medium' },
  { id: 'pds_cartesian', label: 'PDS Cartesian', difficulty: 'Medium' },
  { id: 'mgnrega_wildcard', label: 'MGNREGA Wildcard', difficulty: 'Medium' },
  { id: 'gst_multi_join', label: 'GST Multi-Join', difficulty: 'Hard' },
]

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

  const { envState, isBackendOnline, isRefreshing } = useCurriculum(10000)
  const [selectedTask, setSelectedTask] = useState('pds_select_star')
  const [prevLevel, setPrevLevel] = useState(1)
  const [showLevelUp, setShowLevelUp] = useState(false)
  const didInitializeRef = useRef(false)

  useEffect(() => {
    if (envState?.curriculum_level && envState.curriculum_level > prevLevel) {
      setShowLevelUp(true)
      setPrevLevel(envState.curriculum_level)
    }
  }, [envState?.curriculum_level, prevLevel])

  useEffect(() => {
    if (didInitializeRef.current) {
      return
    }

    didInitializeRef.current = true
    void reset(selectedTask)
  }, [reset, selectedTask])

  const handleTaskChange = async (taskId: string) => {
    setSelectedTask(taskId)
    await reset(taskId)
  }

  const handleSubmit = async (
    query: string,
    pattern: AntiPatternType,
    explanation: string,
    indexes: string[]
  ) => {
    await step(query, pattern, explanation, indexes)
  }

  const isInitialLoading = !observation && (isLoading || !error)

  return (
    <>
      {showLevelUp && (
        <LevelUpToast
          fromLevel={prevLevel}
          toLevel={envState?.curriculum_level ?? 1}
          onDismiss={() => setShowLevelUp(false)}
        />
      )}
      <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg-primary)' }}>
        <header
          className="flex items-center justify-between px-8 py-4"
          style={{ background: 'var(--bg-panel)', borderBottom: '1px solid var(--border-subtle)' }}
        >
          <div className="flex items-center gap-5">
            <span className="font-bold text-base" style={{ color: 'var(--text-primary)' }}>
              SQL Optimization Dashboard
            </span>

            <span className="text-xs px-3 py-1 rounded-full" style={{ background: '#4A90D920', color: '#4A90D9' }}>
              Level {envState?.curriculum_level ?? 1} — {LEVEL_LABELS[envState?.curriculum_level ?? 1]}
            </span>

            <span
              className="text-xs px-3 py-1 rounded-full"
              style={{
                background:
                  isBackendOnline === null
                    ? '#FFD74020'
                    : isBackendOnline
                      ? '#00E67620'
                      : '#FF525220',
                color:
                  isBackendOnline === null
                    ? '#FFD740'
                    : isBackendOnline
                      ? '#00E676'
                      : '#FF5252',
              }}
            >
              {isBackendOnline === null
                ? 'Checking backend'
                : isBackendOnline
                  ? isRefreshing
                    ? 'Backend online · syncing'
                    : 'Backend online'
                  : 'Backend offline'}
            </span>
          </div>

          <div className="flex items-center gap-4">
            <select
              value={selectedTask}
              onChange={e => void handleTaskChange(e.target.value)}
              className="text-xs px-3 py-2 rounded-lg outline-none"
              style={{
                background: '#0F1229',
                border: '1px solid #1E2140',
                color: '#E8EAF6',
              }}
            >
              {TASK_OPTIONS.map(task => (
                <option key={task.id} value={task.id}>
                  {task.label} ({task.difficulty})
                </option>
              ))}
            </select>

            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
              Episode: {envState?.total_episodes ?? 0}
            </span>

            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
              Steps: {history?.length ?? 0}
            </span>
          </div>
        </header>

        <div
          className="flex justify-center gap-8 py-4"
          style={{ background: 'var(--bg-panel)', borderBottom: '1px solid var(--border-subtle)' }}
        >
          {[1, 2, 3, 4, 5].map(level => (
            <CurriculumNode key={level} level={level} active={envState?.curriculum_level ?? 1} />
          ))}
        </div>

        {error && (
          <div className="mx-8 mt-4 p-3 rounded-lg text-xs" style={{ background: '#FF525215', color: '#FF5252' }}>
            {error}
          </div>
        )}

        <div className="flex-1 grid grid-cols-1 xl:grid-cols-[320px_1fr_320px] gap-6 p-6">
          <div className="space-y-4">
            {observation ? (
              <>
                <div
                  className="p-5 rounded-xl"
                  style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)' }}
                >
                  <div className="text-xs font-bold mb-3" style={{ color: '#FFD740' }}>
                    TASK GOAL
                  </div>
                  <p className="text-sm leading-relaxed">{observation.goal}</p>
                </div>

                {observation.anti_pattern_hint && (
                  <div
                    className="p-5 rounded-xl"
                    style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)' }}
                  >
                    <div className="text-xs font-bold mb-2">HINT</div>
                    <p className="text-sm">{observation.anti_pattern_hint}</p>
                  </div>
                )}
              </>
            ) : (
              <DashboardLoader label="Loading task goal and backend state…" />
            )}
          </div>

          <div className="space-y-5 min-h-[360px]">
            {observation ? (
              <>
                <div className="rounded-xl overflow-hidden" style={{ border: '1px solid var(--border-subtle)' }}>
                  <div className="px-4 py-2 text-xs" style={{ background: '#0F1229', color: 'var(--text-muted)' }}>
                    Current Query
                  </div>

                  <pre className="p-4 text-xs overflow-x-auto" style={{ background: 'var(--bg-card)', color: '#E8EAF6' }}>
                    {observation.current_query}
                  </pre>
                </div>

                <AnimatePresence>
                  {!isEpisodeDone ? (
                    <QueryEditor
                      key={observation.task_id}
                      initialQuery={observation.current_query}
                      onSubmit={handleSubmit}
                      isLoading={isLoading}
                    />
                  ) : (
                    <div className="p-6 text-center rounded-xl" style={{ background: 'var(--bg-card)' }}>
                      <div className="text-xl mb-2">🎉 Episode Complete</div>
                      <button
                        onClick={() => void reset()}
                        className="mt-3 px-5 py-2 rounded-lg"
                        style={{
                          background: 'linear-gradient(135deg, #4A90D9, #00D4FF)',
                          color: '#fff',
                        }}
                      >
                        New Episode
                      </button>
                    </div>
                  )}
                </AnimatePresence>
              </>
            ) : isInitialLoading ? (
              <DashboardLoader label="Waking the training environment. If the Space was sleeping, this can take a few seconds." />
            ) : (
              <DashboardLoader label="No observation is available yet. Please try selecting a task again." />
            )}
          </div>

          <div className="space-y-5">
            <RewardRadar reward={stepResult?.reward_detail ?? null} previous={previousReward} />

            {observation ? (
              <ExplainTree
                plan={stepResult?.observation.execution_plan ?? observation.execution_plan}
                originalPlan={originalPlan ?? undefined}
                timingMs={stepResult?.observation.execution_time_ms ?? observation.execution_time_ms}
                originalTimingMs={observation.execution_time_ms}
              />
            ) : (
              <DashboardLoader label="Execution plan will appear here after the environment responds." />
            )}

            <EpisodeHistory
              history={history}
              currentLevel={envState?.curriculum_level ?? 1}
            />
          </div>
        </div>
      </div>
    </>
  )
}
