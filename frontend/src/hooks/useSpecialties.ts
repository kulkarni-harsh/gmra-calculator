import { useEffect, useState } from 'react'
import { fetchSpecialties } from '@/lib/api'
import type { Specialty } from '@/types/api'

export function useSpecialties() {
  const [specialties, setSpecialties] = useState<Specialty[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = () => {
    setIsLoading(true)
    setError(null)
    fetchSpecialties()
      .then(setSpecialties)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to load specialties')
      })
      .finally(() => setIsLoading(false))
  }

  useEffect(() => {
    load()
  }, [])

  return { specialties, isLoading, error, retry: load }
}
