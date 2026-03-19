// All API calls are centralized here. Never call fetch() directly from components.
// To switch from local to cloud hosting, update VITE_API_BASE_URL in .env.

import type { CreateT0PaymentIntentPayload, GenerateReportRequest, GenerateT0ReportRequest, Provider, Specialty } from '@/types/api'

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8000'
const API = `${BASE_URL}/api`
const API_V2 = `${BASE_URL}/api/v2/report`

export async function fetchSpecialties(): Promise<Specialty[]> {
  const res = await fetch(`${API}/specialties`)
  if (!res.ok) throw new Error(`Failed to fetch specialties (${res.status})`)
  const data: unknown = await res.json()
  // The endpoint may return string[] or Specialty[]. Normalize to Specialty[].
  if (Array.isArray(data) && typeof data[0] === 'string') {
    return (data as string[]).map((s) => ({
      id: s.toLowerCase().replace(/\s+/g, '_'),
      description: s,
      taxonomy_codes: [],
      national_density: null,
    }))
  }
  return data as Specialty[]
}

export async function searchProviders(zipCode: string, specialtyName: string): Promise<Provider[]> {
  const params = new URLSearchParams({ zip_code: zipCode, specialty_name: specialtyName })
  const res = await fetch(`${API}/search-providers?${params}`)
  if (!res.ok) throw new Error(`Provider search failed (${res.status})`)
  return res.json() as Promise<Provider[]>
}

export interface GenerateResult {
  htmlContent: string | null
  jobId: string
}

export interface JobStatus {
  job_id: string
  status: 'pending' | 'running' | 'done' | 'failed'
  created_at: string
  updated_at: string
  specialty_name?: string
  provider_name?: string
  report_pdf_s3_url?: string
  error?: string
}

export async function generateReport(payload: GenerateReportRequest): Promise<GenerateResult> {
  const submitRes = await fetch(`${API_V2}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!submitRes.ok) {
    const text = await submitRes.text().catch(() => '')
    throw new Error(`Job submission failed (${submitRes.status}): ${text}`)
  }
  const { job_id } = (await submitRes.json()) as { job_id: string }
  return { htmlContent: null, jobId: job_id }
}

export async function checkJobStatus(jobId: string): Promise<JobStatus> {
  const res = await fetch(`${API}/status/${jobId}`)
  if (res.status === 404) throw new Error('Job not found — check your tracking ID')
  if (!res.ok) throw new Error(`Status check failed (${res.status})`)
  return res.json() as Promise<JobStatus>
}

export interface CreatePaymentIntentPayload {
  customer_email: string
  provider_name: string
  specialty_name: string
  client_provider: Provider
  miles_radius: number
}

export interface CreatePaymentIntentResult {
  client_secret: string
  job_id: string
}

export async function createPaymentIntent(
  payload: CreatePaymentIntentPayload,
): Promise<CreatePaymentIntentResult> {
  const res = await fetch(`${API}/create-payment-intent`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`Failed to create payment session (${res.status}): ${text}`)
  }
  return res.json() as Promise<CreatePaymentIntentResult>
}

const API_V3 = `${BASE_URL}/api/v3`

export async function createT0PaymentIntent(
  payload: CreateT0PaymentIntentPayload,
): Promise<CreatePaymentIntentResult> {
  const res = await fetch(`${API_V3}/create-payment-intent`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`Failed to create T0 payment session (${res.status}): ${text}`)
  }
  return res.json() as Promise<CreatePaymentIntentResult>
}

export async function generateT0Report(payload: GenerateT0ReportRequest): Promise<GenerateResult> {
  const res = await fetch(`${API_V3}/report/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`T0 job submission failed (${res.status}): ${text}`)
  }
  const { job_id } = (await res.json()) as { job_id: string }
  return { htmlContent: null, jobId: job_id }
}
