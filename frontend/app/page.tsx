'use client'

import { motion } from 'framer-motion'
import dynamic from 'next/dynamic'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import { Spotlight } from '@/components/ui/spotlight'
import { CurriculumNode } from '@/components/ui/curriculum-node'
import { getState, healthCheck } from '@/lib/api'
import { EnvironmentState } from '@/lib/types'

import { QueryViz } from '@/components/ui/QueryViz'
import { RobotWidget } from '@/components/ui/RobotWidget'
import { Database, BarChart2, Award, Globe } from 'lucide-react'

export default function HomePage() {
  const [envState, setEnvState] = useState<EnvironmentState | null>(null)
  const [isBackendOnline, setIsBackendOnline] = useState<boolean | null>(null)
  const [progressWidth, setProgressWidth] = useState(0)

  useEffect(() => {
    let cancelled = false
    let timerId: number
    const startTime = Date.now()

    const check = async () => {
      const online = await healthCheck()
      if (cancelled) return

      setIsBackendOnline(online)

      if (!online) {
        timerId = window.setTimeout(check, 3000)
        return
      }

      try {
        const state = await getState()
        if (!cancelled) {
          setEnvState(state)
        }
      } catch {
        if (!cancelled) {
          setIsBackendOnline(false)
          timerId = window.setTimeout(check, 3000)
        }
      }
    }

    timerId = window.setTimeout(check, 600)

    const progressTimer = window.setInterval(() => {
      if (isBackendOnline === false) {
        const elapsed = Date.now() - startTime
        setProgressWidth(Math.min((elapsed / 30000) * 100, 100))
      }
    }, 100)

    return () => {
      cancelled = true
      window.clearTimeout(timerId)
      window.clearInterval(progressTimer)
    }
  }, [isBackendOnline])

  const currentLevel = envState?.curriculum_level ?? 1
  const totalEpisodes = envState?.total_episodes ?? 0

  return (
    <main className="min-h-screen flex flex-col" style={{ background: 'var(--bg-primary)' }}>
      <nav
        className="flex items-center justify-between px-8 py-4"
        style={{ borderBottom: '1px solid var(--border-subtle)' }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold"
            style={{ background: 'linear-gradient(135deg, #4A90D9, #00D4FF)', color: '#fff' }}
          >
            SQL
          </div>

          <span className="font-bold text-sm tracking-wide" style={{ color: 'var(--text-primary)' }}>
            SQL Optimization Curriculum
          </span>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div
              className="w-2 h-2 rounded-full"
              style={{
                backgroundColor:
                  isBackendOnline === null
                    ? '#FFD740'
                    : isBackendOnline
                      ? '#00E676'
                      : '#FF5252',
                boxShadow: isBackendOnline ? '0 0 8px #00E676' : 'none',
              }}
            />
            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
              {isBackendOnline === null
                ? 'Checking backend...'
                : isBackendOnline
                  ? 'Backend Online'
                  : 'Backend Offline'}
            </span>
          </div>

          <span
            className="text-xs px-2 py-1 rounded"
            style={{
              background: 'var(--bg-card)',
              color: 'var(--text-muted)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            Episode: {totalEpisodes}
          </span>

          <span
            className="text-xs px-2 py-1 rounded"
            style={{
              background: 'var(--bg-card)',
              color: 'var(--text-muted)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            Level: {currentLevel}
          </span>
        </div>
      </nav>

      <div
        className="px-8 py-3"
        style={{ borderBottom: '1px solid var(--border-subtle)', background: 'var(--bg-panel)' }}
      >
        <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
          Recent episode scores
        </span>

        <div className="flex items-center justify-between relative mt-3">
          <div
            className="absolute top-6 left-6 right-6 h-0.5"
            style={{ background: 'var(--border-subtle)' }}
          />

          <motion.div
            className="absolute top-6 left-6 h-0.5"
            style={{ background: 'linear-gradient(90deg, #4A90D9, #00D4FF)' }}
            initial={{ width: 0 }}
            animate={{ width: `${((currentLevel - 1) / 4) * 100}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
          />

          {[1, 2, 3, 4, 5].map(level => (
            <CurriculumNode
              key={level}
              level={level}
              active={currentLevel}
              score={envState && level < currentLevel ? 0.75 : undefined}
            />
          ))}
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-6xl min-h-[520px] relative overflow-hidden rounded-2xl"
          style={{
            background: 'radial-gradient(ellipse at 20% 50%, #0F1229 0%, #0A0B1A 100%)',
            border: '1px solid #1E2140',
            boxShadow: '0 0 60px #4A90D910, 0 0 120px #4A90D908',
          }}
        >
          <Spotlight className="-top-40 left-0 md:left-60 md:-top-20" fill="#4A90D9" />

          <div className="flex h-full flex-col lg:flex-row">
            <div className="flex-1 p-10 flex flex-col justify-center">
              <span
                className="text-xs font-semibold px-3 py-1 rounded-full w-fit"
                style={{ background: '#4A90D920', color: '#4A90D9' }}
              >
                META × PYTORCH OPENENV HACKATHON
              </span>

              <h1
                className="mt-5 text-5xl font-bold"
                style={{
                  background: 'linear-gradient(135deg, #E8EAF6, #8892A4)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                SQL Query Optimization
              </h1>

              <h2 className="text-2xl mt-2" style={{ color: '#4A90D9' }}>
                RL Training Environment
              </h2>

              <p className="mt-4 text-sm max-w-md" style={{ color: 'var(--text-muted)' }}>
                Train AI agents to optimize SQL queries across real datasets.
              </p>

              <div className="flex flex-wrap gap-4 mt-6">
                {[
                  { icon: Database, label: '12 Tasks' },
                  { icon: BarChart2, label: '5 Difficulty Levels' },
                  { icon: Award, label: '5-Dimension Reward' },
                  { icon: Globe, label: 'Indian Data Domains' }
                ].map(({ icon: Icon, label }) => (
                  <div key={label} className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-slate-700 bg-slate-800/50 text-xs text-slate-300 hover:bg-slate-800 transition-colors cursor-default hover:border-slate-500 hover:scale-105 transform duration-300">
                    <Icon size={14} className="text-[#4A90D9]" />
                    {label}
                  </div>
                ))}
              </div>

              {isBackendOnline === false && (
                <div className="mt-8 p-5 rounded-xl border border-[#FFD74050] bg-[#FFD74010] flex flex-col gap-3">
                  <div className="flex items-center gap-3">
                    <div className="w-4 h-4 rounded-full border-2 border-[#FFD740] border-t-transparent animate-spin"/>
                    <span className="text-sm font-semibold text-[#FFD740]">
                      HuggingFace Space is waking up — this can take 30 seconds on first load.
                    </span>
                  </div>
                  <div className="h-1.5 w-full bg-[#00000030] rounded-full overflow-hidden">
                     <div className="h-full bg-[#FFD740] transition-all duration-100 ease-linear" style={{ width: `${progressWidth}%` }} />
                  </div>
                </div>
              )}

              <div className="flex gap-3 mt-8">
                <Link href="/dashboard" prefetch={false}>
                  <button
                    className="px-6 py-3 rounded-xl font-bold"
                    style={{ background: 'linear-gradient(135deg, #4A90D9, #00D4FF)', color: '#fff' }}
                  >
                    Open Dashboard →
                  </button>
                </Link>
              </div>
            </div>

            <div className="flex-1 min-h-[320px] lg:min-h-full">
              <QueryViz />
            </div>
          </div>
        </motion.div>
      </div>

      {/* CSS Robot fixed at bottom-left */}
      <RobotWidget />
    </main>
  )
}
