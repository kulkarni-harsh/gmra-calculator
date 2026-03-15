import { useState } from 'react'
import { generateReport } from '@/lib/api'
import type { GenerateReportRequest } from '@/types/api'

export function useReportGeneration() {
  const [isGenerating, setIsGenerating] = useState(false)
  const [isComplete, setIsComplete] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [htmlContent, setHtmlContent] = useState<string | null>(null)

  const generate = (payload: GenerateReportRequest) => {
    setIsGenerating(true)
    setIsComplete(false)
    setError(null)
    setHtmlContent(null)

    generateReport(payload)
      .then(({ htmlContent: html }) => {
        setHtmlContent(html)
        setIsComplete(true)
      })
      .catch((err: unknown) => {
        const msg = err instanceof Error ? err.message : 'Report generation failed'
        setError(msg)
      })
      .finally(() => setIsGenerating(false))
  }

  const reset = () => {
    setIsGenerating(false)
    setIsComplete(false)
    setError(null)
    setHtmlContent(null)
  }

  return { isGenerating, isComplete, error, htmlContent, generate, reset }
}
