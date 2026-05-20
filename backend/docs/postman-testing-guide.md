# MERC API — Postman Testing Guide

End-to-end walkthrough: from health check through Stripe payment to report generation and polling.

---

## 0. Setup

### Environments

Create two Postman **Environments** (not just variables) so you can switch with one click:

**Personal / Staging**

| Variable | Value |
|---|---|
| `base_url` | `https://api.tryingmybest.site` |
| `stripe_secret_key` | `sk_test_51TBuNh...` (from `personal.tfvars`) |
| `api_key` | *(blank — auth off)* |

**Client / Prod**

| Variable | Value |
|---|---|
| `base_url` | `https://api.medicalrealestatecalculator.com` |
| `stripe_secret_key` | `sk_test_51TBuNh...` (same test key for now) |
| `api_key` | *(blank — auth off until you flip `auth_enforced`)* |

> Swagger UI (interactive docs) is at `{{base_url}}/docs` — available in personal env (`openapi_public = true`), hidden in client env (`openapi_public = false`). Use `https://api.tryingmybest.site/docs` to browse the full schema interactively.

### Collection Variables (shared across both environments)

In the Collection, add:

| Variable | Notes |
|---|---|
| `client_secret` | Auto-filled by the payment intent request (Tests tab script) |
| `payment_intent_id` | Auto-filled — extracted from `client_secret` |
| `job_id` | Auto-filled by the generate request |

### Auth Header (only when AUTH_ENFORCED=true)

Add a **Collection-level header** (disabled by default):
```
X-API-Key: {{api_key}}
```

Right now `auth_enforced = false` in both tfvars, so no key is required. When you flip it to `true` and deploy, fill in `api_key` in the environment and enable the header.

### Stripe CLI — deployed env setup (one-time)

For the **deployed** environment, the Stripe webhook is called by Stripe directly — no CLI listener needed. But you still need the CLI to **confirm test payments**. Install it once:

```bash
brew install stripe/stripe-cli/stripe
stripe login   # opens browser, links to your Stripe dashboard
```

The Stripe dashboard must have a webhook endpoint registered:
- **URL:** `https://api.tryingmybest.site/api/payments/webhook/stripe`
- **Events:** `payment_intent.succeeded`
- The signing secret from that webhook endpoint must match `stripe_webhook_secret` in your tfvars / Secrets Manager.

To check: go to Stripe Dashboard → Developers → Webhooks.

### Allowed test emails

The backend hard-validates `customer_email`. Only these addresses work:
- `harshsk17@gmail.com`
- `harsh.kulkarni.42774@gmail.com`
- `david@gm-ra.com`
- `d.rutson@gmail.com`

Use one of these in every request that has `customer_email`.

---

## 1. Health Check

Verify the server is up. This endpoint is always open — no auth needed.

```
GET {{base_url}}/api/health
```

**Expected response (200):**
```json
{"status": "ok"}
```

---

## 2. List Specialties

```
GET {{base_url}}/api/providers/specialties
```

**Expected response (200):** Array of specialty objects.

```json
[
  {
    "id": "family_medicine",
    "description": "Family Medicine",
    "taxonomy_codes": ["207Q00000X"],
    "national_density": 42.3
  },
  ...
]
```

Copy one of the `"description"` values (e.g. `"Family Medicine"`) — you'll use it as `specialty_name` throughout.

---

## 3. Search Providers (needed for A1 tier only)

A1 reports are built around a specific provider's NPI. Skip to §4 if you're testing T1/T2/T3.

```
GET {{base_url}}/api/providers/search-providers?zip_code=90210&specialty_name=Family Medicine
```

**Expected response (200):** Array of provider objects.

```json
[
  {
    "id": 12345,
    "npi": "1234567890",
    "name": "Jane Smith MD",
    "location": {
      "address_line_1": "100 Main St",
      "city": "Beverly Hills",
      "state": "CA",
      "zip_code": "90210"
    },
    ...
  }
]
```

Copy one full provider object — you'll paste it as `client_provider` in the A1 payment intent.

---

## 4. The Stripe Payment Flow

Every report tier requires a paid Stripe PaymentIntent before `/generate` will work.
The full flow is:

```
Create Payment Intent → Confirm Payment (Stripe) → Submit Generate → Poll Status
```

### 4a. Stripe CLI (already installed from §0 setup)

For the deployed environment you do **not** run `stripe listen`. Stripe calls your live webhook URL directly. The CLI is only needed to confirm test PaymentIntents (step 2 of each tier below).

If you ever want to test locally, you would run:
```bash
stripe listen --forward-to http://localhost:8000/api/payments/webhook/stripe
```
But for the deployed env, skip that entirely.

---

## 5. T1 — Market Entry Report ($399)

### Step 1: Create T1 Payment Intent

```
POST {{base_url}}/api/payments/create-t1-payment-intent
Content-Type: application/json

{
  "customer_email": "harshsk17@gmail.com",
  "specialty_name": "Family Medicine",
  "address_line_1": "100 Main St",
  "address_line_2": null,
  "city": "Beverly Hills",
  "state": "CA",
  "zip_code": "90210",
  "drive_time_minutes": 15
}
```

**Expected response (200):**
```json
{
  "client_secret": "pi_3ABC123_secret_XYZ",
  "job_id": "MREC-01HXXX..."
}
```

In the Postman **Tests** tab, add a script to auto-extract the payment intent ID:
```javascript
const body = pm.response.json();
const clientSecret = body.client_secret;
pm.collectionVariables.set("client_secret", clientSecret);
pm.collectionVariables.set("payment_intent_id", clientSecret.split("_secret_")[0]);
pm.collectionVariables.set("job_id", body.job_id);
```

### Step 2: Confirm the Payment

**Option A — Stripe CLI (simplest):**

```bash
stripe payment_intents confirm {{payment_intent_id}} \
  --payment-method pm_card_visa
```

Replace `{{payment_intent_id}}` with the actual `pi_xxx` value from Step 1 (copy from the Postman response or the auto-filled collection variable).

**Option B — Postman request direct to Stripe:**

```
POST https://api.stripe.com/v1/payment_intents/{{payment_intent_id}}/confirm
Authorization: Basic   ← set Type to "Basic Auth", username = sk_test_51TBu..., password blank
Content-Type: application/x-www-form-urlencoded

payment_method=pm_card_visa
```

After confirming, the PaymentIntent status becomes `succeeded` and Stripe fires the `payment_intent.succeeded` webhook to your deployed endpoint automatically. You'll see the job move from `awaiting_payment` to `pending` in the status poll.

> Stripe test payment method tokens: `pm_card_visa` (succeeds), `pm_card_chargeDeclined` (fails).

### Step 3: Submit Report Generation

```
POST {{base_url}}/api/reports/t1/generate
Content-Type: application/json

{
  "specialty_name": "Family Medicine",
  "address_line_1": "100 Main St",
  "address_line_2": null,
  "city": "Beverly Hills",
  "state": "CA",
  "zip_code": "90210",
  "drive_time_minutes": 15,
  "customer_email": "harshsk17@gmail.com",
  "payment_intent_id": "{{payment_intent_id}}"
}
```

**Expected response (200):**
```json
{
  "job_id": "MREC-01HXXX...",
  "status": "pending"
}
```

**If you get 402:** The payment intent was not confirmed (`status != succeeded`). Go back to Step 2.
**If you get 409:** This payment intent was already used to generate a report. Create a new one.

---

## 6. T2 — Current Market Analysis ($499, up to 5 CPT codes)

Same flow as T1. The only differences are the endpoint and the added `cpt_codes` field.

### Step 1: Create T2 Payment Intent

```
POST {{base_url}}/api/payments/create-t2-payment-intent
Content-Type: application/json

{
  "customer_email": "harshsk17@gmail.com",
  "specialty_name": "Family Medicine",
  "address_line_1": "100 Main St",
  "city": "Beverly Hills",
  "state": "CA",
  "zip_code": "90210",
  "drive_time_minutes": 15,
  "cpt_codes": ["99213", "99214"]
}
```

### Step 2: Confirm (same as T1 — `stripe payment_intents confirm ...`)

### Step 3: Generate

```
POST {{base_url}}/api/reports/t2/generate
Content-Type: application/json

{
  "specialty_name": "Family Medicine",
  "address_line_1": "100 Main St",
  "city": "Beverly Hills",
  "state": "CA",
  "zip_code": "90210",
  "drive_time_minutes": 15,
  "customer_email": "harshsk17@gmail.com",
  "payment_intent_id": "{{payment_intent_id}}",
  "cpt_codes": ["99213", "99214"]
}
```

---

## 7. T3 — In-depth Market Analysis ($599, up to 15 CPT codes)

Same flow as T2 but with endpoint `/create-t3-payment-intent` / `/reports/t3/generate` and up to 15 CPT codes.

```json
"cpt_codes": ["99213", "99214", "99215", "99232", "99233"]
```

---

## 8. A1 — Provider Report ($500, NPI-based)

A1 requires a full `Provider` object (fetched from §3) as `client_provider`.

### Step 1: Create A1 Payment Intent

```
POST {{base_url}}/api/payments/create-payment-intent
Content-Type: application/json

{
  "customer_email": "harshsk17@gmail.com",
  "provider_name": "Jane Smith MD",
  "specialty_name": "Family Medicine",
  "miles_radius": 10,
  "client_provider": {
    "id": 12345,
    "npi": "1234567890",
    "name": "Jane Smith MD",
    "location": {
      "address_line_1": "100 Main St",
      "city": "Beverly Hills",
      "state": "CA",
      "zip_code": "90210"
    }
  }
}
```

### Step 2: Confirm (same as T1)

### Step 3: Generate

```
POST {{base_url}}/api/reports/a1/generate
Content-Type: application/json

{
  "specialty_name": "Family Medicine",
  "miles_radius": 10,
  "customer_email": "harshsk17@gmail.com",
  "payment_intent_id": "{{payment_intent_id}}",
  "client_provider": {
    "id": 12345,
    "npi": "1234567890",
    "name": "Jane Smith MD",
    "location": {
      "address_line_1": "100 Main St",
      "city": "Beverly Hills",
      "state": "CA",
      "zip_code": "90210"
    }
  }
}
```

---

## 9. Poll Job Status

After any `/generate` call succeeds, poll this until `status` is `done` or `failed`:

```
GET {{base_url}}/api/jobs/status/{{job_id}}
```

**Status progression:** `awaiting_payment` → `pending` → `running` → `done` | `failed`

**Done response:**
```json
{
  "job_id": "MREC-01HXXX...",
  "status": "done",
  "created_at": "2026-05-20T10:00:00Z",
  "updated_at": "2026-05-20T10:08:00Z",
  "specialty_name": "Family Medicine",
  "provider_name": "100 Main St, Beverly Hills CA 90210",
  "report_pdf_s3_url": "https://..."
}
```

**Failed response:**
```json
{
  "job_id": "MREC-01HXXX...",
  "status": "failed",
  "error": "AlphaSophia timeout after 3 retries"
}
```

Reports typically take **5–15 minutes** to generate.

---

## 10. Testing with Auth Enabled

To test the full Wix auth flow locally:

1. In `backend/.env`, set:
   ```bash
   AUTH_ENFORCED=true
   API_KEY_WIX=test-wix-key
   API_KEY_REACT=test-react-key
   INTERNAL_ORIGINS=http://localhost:5173
   ```

2. Restart the server.

3. In Postman, add the header `X-API-Key: test-wix-key` to protected requests.

4. Verify:

| Request | Header | Expected |
|---|---|---|
| `GET /api/health` | none | 200 — always open |
| `GET /api/providers/specialties` | none | 401 |
| `GET /api/providers/specialties` | `X-API-Key: test-wix-key` | 200 |
| `GET /api/providers/specialties` | `Origin: http://localhost:5173` | 200 (React bypass) |
| `POST /api/payments/webhook/stripe` | none | 400 (Stripe sig error, not 401) |

---

## 11. Common Errors

| Status | Message | Fix |
|---|---|---|
| `401 Unauthorized` | — | Add `X-API-Key` header, or set `AUTH_ENFORCED=false` locally |
| `402` | PaymentIntent status is 'requires_payment_method' | Run `stripe payment_intents confirm ...` first |
| `402` | PaymentIntent amount is X, expected Y | You used a T1 intent with a T2 generate (or vice versa) |
| `402` | PaymentIntent email does not match | `customer_email` in `/generate` must match the one used in `/create-payment-intent` |
| `409` | Already used to generate a report | Each PaymentIntent is single-use. Create a new one. |
| `422` | Ineligible Customer Email | Use one of the four whitelisted test emails |
| `422` | drive_time_minutes must be one of: 5, 10, 15, 30, 45, 60 | Use only those exact values |
| `500/502` | Failed to create payment session | Stripe key is wrong or not set in `.env` |

---

## 12. Stripe Test Cards

Use these in Stripe CLI `--payment-method` or in the Stripe dashboard:

| Scenario | Token |
|---|---|
| Successful payment | `pm_card_visa` |
| Card declined | `pm_card_chargeDeclined` |
| 3D Secure required | `pm_card_threeDSecureRequired` |
| Insufficient funds | `pm_card_visa_chargeDeclined_insufficientFunds` |

For Stripe Elements in the browser (React frontend), type:
- Card number: `4242 4242 4242 4242`
- Expiry: any future date, e.g. `12/30`
- CVC: any 3 digits, e.g. `123`
- ZIP: any 5 digits, e.g. `90210`
