import { useState } from 'react'
import type { GenerateResult } from '@/lib/api'

export function useReportGeneration() {
  const [isGenerating, setIsGenerating] = useState(false)
  const [isComplete, setIsComplete] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [htmlContent, setHtmlContent] = useState<string | null>(null)
  const [jobId, setJobId] = useState<string | null>(null)

  // Accept any async function that returns a GenerateResult — works for both T0 and T1
  const generate = (generateFn: () => Promise<GenerateResult>) => {
    setIsGenerating(true)
    setIsComplete(false)
    setError(null)
    setHtmlContent(null)
    setJobId(null)
    generateFn()
      .then(({ htmlContent: html, jobId: id }) => {
        setHtmlContent(html)
        setJobId(id)
        setIsComplete(true)
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Report generation failed')
      })
      .finally(() => setIsGenerating(false))
  }

  const reset = () => {
    setIsGenerating(false)
    setIsComplete(false)
    setError(null)
    setHtmlContent(null)
    setJobId(null)
  }

  return { isGenerating, isComplete, error, htmlContent, jobId, generate, reset }
}
