import { useState } from 'react'
import { searchProviders } from '@/lib/api'
import type { Provider } from '@/types/api'

export function useProviderSearch() {
  const [providers, setProviders] = useState<Provider[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hasSearched, setHasSearched] = useState(false)

  const search = (zipCode: string, specialtyName: string) => {
    setIsSearching(true)
    setError(null)
    setHasSearched(false)
    searchProviders(zipCode, specialtyName)
      .then((data) => {
        setProviders(data)
        setHasSearched(true)
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Provider search failed')
        setHasSearched(true)
      })
      .finally(() => setIsSearching(false))
  }

  const reset = () => {
    setProviders([])
    setHasSearched(false)
    setError(null)
  }

  return { providers, isSearching, error, hasSearched, search, reset }
}
