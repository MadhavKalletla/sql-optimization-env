import { SQLOptAction, SQLOptObservation, StepResult, EnvironmentState } from './types'

const BASE_URL = ''

const DEFAULT_TIMEOUTS = {
  reset: 60000,
  step: 60000,
  state: 15000,
  health: 5000,
} as const

function isAbortError(error: unknown) {
  return error instanceof Error && error.name === 'AbortError'
}

async function fetchJson<T>(
  path: string,
  init: RequestInit = {},
  timeoutMs: number
): Promise<T> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs)

  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      ...init,
      signal: controller.signal,
      cache: 'no-store',
      headers: {
        ...(init.body ? { 'Content-Type': 'application/json' } : {}),
        ...(init.headers ?? {}),
      },
    })

    if (!res.ok) {
      const bodyText = await res.text().catch(() => '')
      throw new Error(
        `${path} failed (${res.status} ${res.statusText})${bodyText ? `: ${bodyText.slice(0, 200)}` : ''
        }`
      )
    }

    return (await res.json()) as T
  } catch (error) {
    if (isAbortError(error)) {
      throw new Error(
        `Request to ${path} timed out after ${timeoutMs}ms. The HuggingFace Space is likely cold-starting or unavailable.`
      )
    }

    throw error
  } finally {
    clearTimeout(timeoutId)
  }
}

export async function resetEnvironment(
  taskId?: string,
  timeoutMs = DEFAULT_TIMEOUTS.reset
): Promise<SQLOptObservation> {
  const res = await fetchJson<SQLOptObservation>(
    '/reset',
    {
      method: 'POST',
      body: JSON.stringify(taskId ? { task_id: taskId } : {}),
    },
    timeoutMs
  )
  // Backend now returns the observation properly formatted as required by OpenEnv spec
  return res
}

export async function submitStep(
  action: SQLOptAction,
  timeoutMs = DEFAULT_TIMEOUTS.step
): Promise<StepResult> {
  return fetchJson<StepResult>(
    '/step',
    {
      method: 'POST',
      body: JSON.stringify(action),
    },
    timeoutMs
  )
}

export async function getState(
  timeoutMs = DEFAULT_TIMEOUTS.state
): Promise<EnvironmentState> {
  return fetchJson<EnvironmentState>('/state', { method: 'GET' }, timeoutMs)
}

export async function healthCheck(
  timeoutMs = DEFAULT_TIMEOUTS.health
): Promise<boolean> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs)

  try {
    const res = await fetch(`${BASE_URL}/health`, {
      method: 'GET',
      signal: controller.signal,
      cache: 'no-store',
    })

    return res.ok
  } catch (error) {
    if (isAbortError(error)) {
      return false
    }

    return false
  } finally {
    clearTimeout(timeoutId)
  }
}
