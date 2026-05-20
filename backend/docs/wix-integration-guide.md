# MERC API — Wix Velo Integration Guide

This guide is for the team building the Wix frontend that consumes the MERC
backend. The MERC backend is a FastAPI service deployed on AWS ECS Fargate
and reachable at `https://api.merc.com/api/`.

## What you'll build

A Wix Velo backend module that:

1. Reads your shared API key from Wix Secrets Manager.
2. Calls `POST /api/reports/{tier}/generate` to start a report job.
3. Polls `GET /api/jobs/status/{job_id}` until the job is complete.

All calls happen from your **Velo backend** (`.jsw` files). Do not call MERC
directly from frontend page code — that would expose the API key.

## 1. Store the key

In your Wix site dashboard:

1. Go to **Settings → Secrets Manager**.
2. Add a new secret named `merc_api_key`.
3. Paste the key value your MERC contact shared with you (via 1Password).

## 2. Create a Velo backend module

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

## 3. Polling pattern (in Velo frontend)

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

## 4. Rate limits

- `POST /api/reports/{tier}/generate`: **120 requests per minute** per
  (api-key, source-ip). On exceed, you get `429 Too Many Requests` with
  `Retry-After: 60`.
- Other endpoints: 300 requests per minute (same bucket scheme).

On `429`, back off for the duration in `Retry-After` and retry.

## 5. Errors you may see

| Status | Meaning | What to do |
|--------|---------|------------|
| `401`  | Missing or invalid `X-API-Key` | Verify the secret name and value in Wix Secrets Manager. |
| `400`  | Invalid request body | Check the schema for the tier you're calling. |
| `429`  | Rate limited | Back off per `Retry-After`. |
| `5xx`  | MERC server error | Retry with exponential backoff up to 3 times; if still failing, ping us. |

## 6. Endpoints quick reference

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

The full OpenAPI schema is at `https://api.merc.com/openapi.json` in staging
(it's hidden in prod).

## 7. Contact

Ping the MERC team if a key needs rotating or you need higher rate limits.
