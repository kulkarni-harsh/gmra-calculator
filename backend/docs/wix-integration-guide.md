# MERC API — Wix Velo Integration Guide

This guide is for the team building the Wix frontend that consumes the MERC
backend. The MERC backend is a FastAPI service deployed on AWS ECS Fargate.

- **Production API base:** `https://api.merc.com/api`
- **Staging API base:** ask the MERC team — staging lives on a separate subdomain.

All calls happen from your **Wix Velo backend** (`.jsw` files). Do not call
MERC directly from frontend page code — that would expose the API key.

---

## 0. DNS — what we need from you (one-time)

The public-facing site (apex `merc.com` + `www.merc.com`) is served by Wix.
The backend lives at `api.merc.com` and stays on our AWS load balancer. We
keep DNS authority in AWS Route 53 (this is non-negotiable because our
transactional email records live there).

That means we need DNS values **from your Wix dashboard** so we can publish
them in our Route 53 zone:

1. In your Wix site dashboard, go to **Settings → Domains → Connect a Domain
   you already own → Pointing Method (not Nameserver method)**.
2. Wix will show you values like:
   - **A record IP(s)** for the apex (e.g. `23.236.62.147`).
   - **CNAME target** for `www` (e.g. `your-site.wixsite.com`).
3. Send those values to the MERC team. We will add them to Route 53.
4. Once DNS propagates (~5–30 min) Wix automatically provisions SSL for
   `merc.com` and `www.merc.com`. We provision SSL for `api.merc.com`
   independently in AWS.

**Do not** change Wix's "Nameserver Method". That would point the whole
domain at Wix's DNS and break our email and `api.` subdomain.

---

## 1. What you'll build

A Wix Velo backend module that:

1. Reads your shared API key from Wix Secrets Manager.
2. Calls `POST /api/reports/{tier}/generate` to start a report job.
3. Polls `GET /api/jobs/status/{job_id}` until the job is complete.

You'll also build a **status page** on the Wix site at `/status` that reads
a `job_id` query-string parameter and shows the current status to the user.
Our transactional emails link customers to `https://merc.com/status?job_id=…`,
so this page must exist.

---

## 2. Store the API key

In your Wix site dashboard:

1. Go to **Settings → Secrets Manager**.
2. Add a new secret named `merc_api_key`.
3. Paste the key value your MERC contact shared with you (delivered via
   1Password, never email/Slack).

The key is rotated on request — see [§7 Contact](#7-contact).

---

## 3. Create a Velo backend module

In your Wix site, create `backend/merc.jsw`:

```javascript
import {fetch} from 'wix-fetch';
import {getSecret} from 'wix-secrets-backend';

const BASE = 'https://api.merc.com/api';

async function headers() {
  const key = await getSecret('merc_api_key');
  return {
    'X-API-Key': key,
    'Content-Type': 'application/json',
  };
}

export async function generateReport(tier, payload) {
  const res = await fetch(`${BASE}/reports/${tier}/generate`, {
    method: 'POST',
    headers: await headers(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`MERC /reports/${tier}/generate ${res.status}: ${body}`);
  }
  return res.json();      // → { job_id }
}

export async function getJobStatus(jobId) {
  const res = await fetch(`${BASE}/jobs/status/${jobId}`, {
    headers: await headers(),
  });
  if (!res.ok) {
    throw new Error(`MERC /jobs/status ${res.status}`);
  }
  return res.json();      // → { status, download_url?, error? }
}

export async function listSpecialties() {
  const res = await fetch(`${BASE}/providers/specialties`, {
    headers: await headers(),
  });
  return res.json();
}
```

---

## 4. Polling pattern (in Velo frontend)

```javascript
import {generateReport, getJobStatus} from 'backend/merc';

async function startAndPoll(tier, payload) {
  const {job_id} = await generateReport(tier, payload);

  let delay = 3000;
  const deadline = Date.now() + 10 * 60 * 1000;  // 10 minutes

  while (Date.now() < deadline) {
    await new Promise(r => setTimeout(r, delay));
    const status = await getJobStatus(job_id);
    if (status.status === 'done')   return status;
    if (status.status === 'failed') throw new Error(status.error);
    delay = Math.min(delay * 1.5, 30000);    // cap at 30s
  }
  throw new Error('Report timed out after 10 minutes');
}
```

---

## 5. `/status` page (required)

Our backend sends transactional emails containing links of the form:

```
https://merc.com/status?job_id=<uuid>
```

Build a Wix page at `/status` that:

1. Reads `job_id` from `wixLocation.query.job_id`.
2. Calls `getJobStatus(jobId)` from the Velo backend module.
3. Renders one of: "in progress" (with a polite spinner), "done" (with the
   `download_url` from the response as a download button), or "failed"
   (with `error` text).
4. Polls every 5–10 seconds while status is `in_progress`.

---

## 6. Rate limits

- `POST /api/reports/{tier}/generate`: **120 requests per minute** per
  (api-key, source-ip). On exceed, you get `429 Too Many Requests` with
  `Retry-After: 60`.
- Other endpoints: 300 requests per minute (same bucket scheme).

On `429`, back off for the duration in `Retry-After` and retry.

---

## 7. Errors you may see

| Status | Meaning | What to do |
|--------|---------|------------|
| `401`  | Missing or invalid `X-API-Key` | Verify the secret name and value in Wix Secrets Manager. |
| `400`  | Invalid request body | Check the schema for the tier you're calling. |
| `429`  | Rate limited | Back off per `Retry-After`. |
| `5xx`  | MERC server error | Retry with exponential backoff up to 3 times; if still failing, ping us. |

---

## 8. Endpoints quick reference

| Method | Path | Purpose |
|--------|------|---------|
| `GET`  | `/api/health` | Liveness check (no key needed) |
| `GET`  | `/api/providers/specialties` | List supported specialties |
| `GET`  | `/api/providers/search-providers` | Office lookup |
| `POST` | `/api/reports/t1/generate` | Start T1 report |
| `POST` | `/api/reports/t2/generate` | Start T2 report |
| `POST` | `/api/reports/t3/generate` | Start T3 report |
| `POST` | `/api/reports/a1/generate` | Start A1 report |
| `GET`  | `/api/jobs/status/{job_id}` | Poll a running job |

The full OpenAPI schema is at `https://api.merc.com/openapi.json` in
staging (hidden in prod). Use staging to generate request/response types.

---

## 9. Local testing without the live key

Hit `GET https://api.merc.com/api/health` from your machine — it requires no
key and returns `{"status": "ok"}`. If that works, DNS and TLS for
`api.merc.com` are healthy.

To smoke-test an authenticated call from your laptop:

```bash
curl -H "X-API-Key: $MERC_API_KEY" https://api.merc.com/api/providers/specialties
```

---

## 10. Contact

Ping the MERC team if:

- A key needs rotating.
- You need higher rate limits.
- You see persistent `5xx` errors.
- The DNS values from Wix change.
