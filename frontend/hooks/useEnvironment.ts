'use client'

import { useState, useCallback, useRef } from 'react'
import {
  SQLOptObservation,
  SQLOptAction,
  StepResult,
  AntiPatternType,
  SQLOptReward,
  ExecutionPlan,
} from '@/lib/types'
import { resetEnvironment, submitStep } from '@/lib/api'

interface EpisodeState {
  observation: SQLOptObservation | null
  stepResult: StepResult | null
  history: StepResult[]
  isLoading: boolean
  error: string | null
  isEpisodeDone: boolean
}

export function useEnvironment() {
  const [previousReward, setPreviousReward] = useState<SQLOptReward | null>(null)
  const [originalPlan, setOriginalPlan] = useState<ExecutionPlan | null>(null)
  const [state, setState] = useState<EpisodeState>({
    observation: null,
    stepResult: null,
    history: [],
    isLoading: false,
    error: null,
    isEpisodeDone: false,
  })

  const reset = useCallback(async (taskId?: string) => {
    setState(s => ({
      ...s,
      isLoading: true,
      error: null,
      isEpisodeDone: false,
    }))

    try {
      const obs = await resetEnvironment(taskId)
      setOriginalPlan(obs.execution_plan)

      setState({
        observation: obs,
        stepResult: null,
        history: [],
        isLoading: false,
        error: null,
        isEpisodeDone: false,
      })

    } catch (err) {
      setState(s => ({
        ...s,
        isLoading: false,
        error: String(err),
      }))
    }
  }, [])

  const step = useCallback(
    async (
      optimizedQuery: string,
      identifiedPattern: AntiPatternType,
      explanation: string,
      indexStatements: string[]
    ) => {
      setState(s => ({ ...s, isLoading: true, error: null }))

      try {
        const action: SQLOptAction = {
          optimized_query: optimizedQuery,
          identified_pattern: identifiedPattern,
          explanation,
          index_statements: indexStatements,
          schema_analysis: '',
        }

        const result = await submitStep(action)

        setState(s => {
          setPreviousReward(s.stepResult?.reward_detail ?? null)
          return {
            ...s,
            observation: result.observation,
            stepResult: result,
            history: [...s.history, result],
            isLoading: false,
            isEpisodeDone: result.done,
          }
        })

        return result
      } catch (err) {
        setState(s => ({
          ...s,
          isLoading: false,
          error: String(err),
        }))
        return null
      }
    },
    []
  )

  return {
    ...state,
    reset,
    step,
    previousReward,
    originalPlan,
  }
}