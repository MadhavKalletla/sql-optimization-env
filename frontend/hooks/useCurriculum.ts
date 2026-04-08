'use client'

import { useEffect, useRef, useSyncExternalStore } from 'react'
import { EnvironmentState } from '@/lib/types'
import { getState, healthCheck } from '@/lib/api'

interface CurriculumSnapshot {
  envState: EnvironmentState | null
  isBackendOnline: boolean | null
  lastUpdated: Date | null
  isRefreshing: boolean
}

interface UseCurriculumOptions {
  enabled?: boolean
  refreshOnMount?: boolean
}

let mountCount = 0

let snapshot: CurriculumSnapshot = {
  envState: null,
  isBackendOnline: null,
  lastUpdated: null,
  isRefreshing: false,
}

const listeners = new Set<() => void>()
const pollers = new Map<symbol, number>()
let intervalId: ReturnType<typeof setInterval> | null = null
let inFlightRefresh: Promise<void> | null = null

function emitChange() {
  listeners.forEach(listener => listener())
}

function setSnapshot(partial: Partial<CurriculumSnapshot>) {
  snapshot = {
    ...snapshot,
    ...partial,
  }
  emitChange()
}

function getSnapshot(): CurriculumSnapshot {
  return snapshot
}

function subscribe(listener: () => void) {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

function restartPolling() {
  if (intervalId) {
    clearInterval(intervalId)
    intervalId = null
  }

  if (pollers.size === 0) {
    return
  }

  const nextInterval = Math.min(...pollers.values())
  intervalId = setInterval(() => {
    void refreshCurriculum()
  }, nextInterval)
}

async function refreshCurriculum() {
  if (inFlightRefresh) {
    return inFlightRefresh
  }

  setSnapshot({ isRefreshing: true })

  inFlightRefresh = (async () => {
    try {
      const online = await healthCheck()

      if (!online) {
        setSnapshot({
          isBackendOnline: false,
          lastUpdated: new Date(),
          isRefreshing: false,
        })
        return
      }

      const state = await getState()
      setSnapshot({
        envState: state,
        isBackendOnline: true,
        lastUpdated: new Date(),
        isRefreshing: false,
      })
    } catch {
      setSnapshot({
        isBackendOnline: false,
        isRefreshing: false,
      })
    } finally {
      inFlightRefresh = null
    }
  })()

  return inFlightRefresh
}

export function useCurriculum(
  pollInterval = 5000,
  options: UseCurriculumOptions = {}
) {
  const { enabled = true, refreshOnMount = true } = options
  const pollerIdRef = useRef<symbol | null>(null)

  if (!pollerIdRef.current) {
    pollerIdRef.current = Symbol('useCurriculumPoller')
  }

  const state = useSyncExternalStore(subscribe, getSnapshot, getSnapshot)

  useEffect(() => {
    mountCount++

    if (!enabled) {
      return
    }

    const pollerId = pollerIdRef.current!
    pollers.set(pollerId, pollInterval)
    restartPolling()

    if (refreshOnMount) {
      void refreshCurriculum()
    }

    return () => {
      pollers.delete(pollerId)
      restartPolling()

      mountCount--

      if (mountCount === 0 && intervalId) {
        clearInterval(intervalId)
        intervalId = null
      }
    }
  }, [enabled, pollInterval, refreshOnMount])

  return {
    ...state,
    refresh: refreshCurriculum,
  }
}
