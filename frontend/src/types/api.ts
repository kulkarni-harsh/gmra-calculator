// Mirrors backend app/types/alphasophia.py Pydantic models

export interface Taxonomy {
  code: string | null
  description: string | null
  count: number | null
}

export interface Location {
  address_line_1: string | null
  address_line_2: string | null
  zip_code: string | null
  city: string | null
  state: string | null
}

export interface Affiliation {
  name: string | null
  count: number | null
  is_sole_proprietor: boolean | null
}

export interface Contact {
  email: string[] | null
  phone: string[] | null
}

export interface CPT {
  code: string
  codeType: string | null
  description: string | null
  totalServices: number
  totalCharges: number
  totalPatients: number
}

export interface Provider {
  id: number
  npi: string | null
  name: string | null
  profilePicture: string | null
  taxonomy: Taxonomy
  location: Location
  affiliation: Affiliation
  contact: Contact
  licensure: string[]
  latitude: number | null
  longitude: number | null
  cpt_list: CPT[]
}

// GET /api/v2/report/specialties response item
export interface Specialty {
  id: string
  description: string
  taxonomy_codes: string[]
  national_density: number | null   // providers per 100k nationally
}

// POST /api/v2/report/generate request body — mirrors ProviderRequest schema
export interface GenerateReportRequest {
  specialty_name: string   // Must be the description string, not the id
  client_provider: Provider
  miles_radius: number     // integer: 5 | 10 | 25 | 50
  customer_email: string
  payment_intent_id: string  // Stripe PaymentIntent ID verified server-side
}

export type RadiusOption = 5 | 10 | 25 | 50

// T0 address-only report types
export interface T0Location {
  address_line_1: string
  address_line_2?: string
  city: string
  state: string
  zip_code: string
}

export interface GenerateT0ReportRequest {
  specialty_name: string
  address_line_1: string
  address_line_2?: string
  city: string
  state: string
  zip_code: string
  miles_radius: number
  customer_email: string
  payment_intent_id: string
}

export interface CreateT0PaymentIntentPayload {
  customer_email: string
  specialty_name: string
  address_line_1: string
  address_line_2?: string
  city: string
  state: string
  zip_code: string
  miles_radius: number
}
