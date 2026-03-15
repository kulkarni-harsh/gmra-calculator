import { useEffect, useState } from 'react'
import { openHtmlInNewTab } from '@/lib/api'
import { useSpecialties } from '@/hooks/useSpecialties'
import { useProviderSearch } from '@/hooks/useProviderSearch'
import { useReportGeneration } from '@/hooks/useReportGeneration'
import { useMediaQuery } from '@/hooks/useMediaQuery'
import type { Provider, RadiusOption } from '@/types/api'

import TierSelection from '@/components/buy/TierSelection'
import StepIndicator from '@/components/buy/StepIndicator'
import OrderSidebar from '@/components/buy/OrderSidebar'
import StepSpecialty from '@/components/buy/StepSpecialty'
import StepLocation from '@/components/buy/StepLocation'
import StepContact from '@/components/buy/StepContact'
import StepConfirm from '@/components/buy/StepConfirm'
import GeneratingScreen from '@/components/buy/GeneratingScreen'
import ConfirmationScreen from '@/components/buy/ConfirmationScreen'

interface BuyFormState {
  selectedTierId: 1 | 2 | 3
  specialtyName: string
  zipCode: string
  milesRadius: RadiusOption
  selectedProvider: Provider | null
  email: string
  phone: string
  currentStep: 1 | 2 | 3 | 4
}

const INITIAL_STATE: BuyFormState = {
  selectedTierId: 1,
  specialtyName: '',
  zipCode: '',
  milesRadius: 5,
  selectedProvider: null,
  email: '',
  phone: '',
  currentStep: 1,
}

export default function Buy() {
  const [state, setState] = useState<BuyFormState>(INITIAL_STATE)
  const isDesktop = useMediaQuery('(min-width: 768px)')

  const { specialties, isLoading: loadingSpecialties, error: specialtiesError, retry: retrySpecialties } = useSpecialties()
  const { providers, isSearching, error: searchError, hasSearched, search, reset: resetSearch } = useProviderSearch()
  const { isGenerating, isComplete, error: genError, htmlContent, generate, reset: resetGen } = useReportGeneration()

  // Auto-open report in new tab when generation completes
  useEffect(() => {
    if (isComplete && htmlContent) {
      openHtmlInNewTab(htmlContent)
    }
  }, [isComplete, htmlContent])

  const advance = () =>
    setState((prev) => ({ ...prev, currentStep: Math.min(prev.currentStep + 1, 4) as 1 | 2 | 3 | 4 }))

  const back = () =>
    setState((prev) => ({ ...prev, currentStep: Math.max(prev.currentStep - 1, 1) as 1 | 2 | 3 | 4 }))

  const resetForm = () => {
    setState(INITIAL_STATE)
    resetSearch()
    resetGen()
  }

  const handleGenerate = () => {
    if (!state.selectedProvider) return
    generate({
      specialty_name: state.specialtyName,
      client_provider: state.selectedProvider,
      miles_radius: state.milesRadius,
    })
  }

  const handleRetry = () => {
    resetGen()
    // Return user to step 4 to try again without losing form data
  }

  // Show generating / confirmation screens
  if (isGenerating) {
    return (
      <div className="min-h-screen bg-[hsl(215_63%_14%)]">
        <div className="mx-auto max-w-[1280px] px-6 py-12">
          <GeneratingScreen providerName={state.selectedProvider?.name ?? null} />
        </div>
      </div>
    )
  }

  if (isComplete || genError) {
    return (
      <div className="min-h-screen bg-[hsl(215_63%_14%)]">
        <div className="mx-auto max-w-[1280px] px-6 py-12">
          <ConfirmationScreen
            providerName={state.selectedProvider?.name ?? null}
            email={state.email}
            htmlContent={htmlContent}
            error={genError}
            onRetry={handleRetry}
            onReset={resetForm}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[hsl(215_63%_14%)]">
      <div className="mx-auto max-w-[1280px] px-6 py-12">
        {/* Tier Selection — full width above the form */}
        <TierSelection
          selectedTierId={state.selectedTierId}
          onSelect={(id) => setState((prev) => ({ ...prev, selectedTierId: id }))}
        />

        {/* Two-column layout: sidebar (desktop) + form */}
        <div className="flex gap-8">
          {/* Left sidebar (desktop only) */}
          {isDesktop && (
            <aside className="w-72 shrink-0">
              <div className="sticky top-24">
                <OrderSidebar
                  specialtyName={state.specialtyName}
                  selectedProvider={state.selectedProvider}
                  milesRadius={state.milesRadius}
                  email={state.email}
                />
              </div>
            </aside>
          )}

          {/* Right form area */}
          <div className="min-w-0 flex-1">
            {/* Mobile compact sidebar banner */}
            {!isDesktop && (
              <div className="mb-4">
                <OrderSidebar
                  specialtyName={state.specialtyName}
                  selectedProvider={state.selectedProvider}
                  milesRadius={state.milesRadius}
                  email={state.email}
                  compact
                />
              </div>
            )}

            <div className="rounded-xl bg-[hsl(217_33%_17%)] p-6 md:p-8">
              <StepIndicator currentStep={state.currentStep} />

              {state.currentStep === 1 && (
                <StepSpecialty
                  specialties={specialties}
                  isLoading={loadingSpecialties}
                  error={specialtiesError}
                  value={state.specialtyName}
                  onChange={(v) => {
                    setState((prev) => ({ ...prev, specialtyName: v, selectedProvider: null }))
                    resetSearch()
                  }}
                  onRetry={retrySpecialties}
                  onNext={advance}
                />
              )}

              {state.currentStep === 2 && (
                <StepLocation
                  zipCode={state.zipCode}
                  milesRadius={state.milesRadius}
                  onZipChange={(v) => setState((prev) => ({ ...prev, zipCode: v }))}
                  onRadiusChange={(v) => setState((prev) => ({ ...prev, milesRadius: v as RadiusOption }))}
                  onSearch={search}
                  isSearching={isSearching}
                  searchError={searchError}
                  hasSearched={hasSearched}
                  providers={providers}
                  selectedProvider={state.selectedProvider}
                  onSelectProvider={(p) => setState((prev) => ({ ...prev, selectedProvider: p }))}
                  specialtyName={state.specialtyName}
                  onNext={advance}
                  onBack={back}
                />
              )}

              {state.currentStep === 3 && (
                <StepContact
                  email={state.email}
                  phone={state.phone}
                  onEmailChange={(v) => setState((prev) => ({ ...prev, email: v }))}
                  onPhoneChange={(v) => setState((prev) => ({ ...prev, phone: v }))}
                  onNext={advance}
                  onBack={back}
                />
              )}

              {state.currentStep === 4 && (
                <StepConfirm
                  specialtyName={state.specialtyName}
                  selectedProvider={state.selectedProvider}
                  milesRadius={state.milesRadius}
                  email={state.email}
                  phone={state.phone}
                  onGenerate={handleGenerate}
                  onBack={back}
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
