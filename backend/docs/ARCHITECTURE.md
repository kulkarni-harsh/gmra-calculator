# Backend Architecture

## Two processes, one image

The backend ships as a single Docker image with two CMDs:

1. **API** — `uvicorn app.main:app` — handles HTTP requests.
2. **Worker** — `python -m app.worker` — long-polls SQS and generates reports. Launched on-demand as a Fargate task by `ensure_worker_running()` when a job is enqueued; self-terminates after ~60 s idle.

Both processes load the same lookup tables at startup (`app/utils/common.load_fee_schedule_tables`, specialty/CPT lookups via `app/services/report_generator.load_state`).

## Request lifecycle (paid report)

```
Customer
  │
  ├─ POST /api/payments/create-payment-intent
  │   ├─ Stripe.PaymentIntent.create   → client_secret
  │   └─ DynamoDB put_item(status="awaiting_payment")
  │
  ├─ Stripe Elements completes payment in browser
  │
  ├─ Stripe → POST /api/payments/webhook/stripe (payment_intent.succeeded)
  │   ├─ DynamoDB update(status="awaiting_payment" → "pending")  [conditional]
  │   ├─ SQS send_message({job_id})
  │   └─ Resend "we received your request" email
  │
  ▼
Worker (on-demand Fargate task — spawned by API, self-terminates after 60 s idle)
  │
  ├─ SQS receive_message
  ├─ DynamoDB update(status="running")
  ├─ run_html_report() / run_report()
  │   ├─ geocode address (Mapbox)
  │   ├─ fetch ZCTA polygons + Census demographics
  │   ├─ fetch nearby providers (AlphaSophia)
  │   ├─ fetch Google Places sites of care
  │   ├─ fetch isochrones + drive-time map (Mapbox)
  │   ├─ aggregate CPT data + compute Medicare fees
  │   ├─ ask Bedrock (Claude) for narrative
  │   └─ render HTML via Jinja
  ├─ html_to_pdf (Playwright)
  ├─ S3 upload html + pdf
  ├─ DynamoDB update(status="done", report_*_url=...)
  ├─ Resend "your report is ready" email
  └─ SQS delete_message
```

## Modules

See `backend/docs/MODULES.md` for the per-module breakdown.

## Failure modes

| Failure | Behavior |
|---|---|
| Worker crashes mid-job | SQS visibility timeout (15 min) re-queues message; DLQ catches after `maxReceiveCount` |
| Stripe webhook fires twice | `claim_job_for_generation` uses DynamoDB conditional update; second call gets `JobAlreadyExistsError` and is a no-op |
| Mapbox geocode fails | Falls back to ZIP centroid in `_geocode_with_fallback` |
| AlphaSophia 504 | Tenacity retry (3 attempts, exponential backoff). After exhaustion, the worker logs `critical` and re-raises (job marked failed) |
| Resend down | Email functions catch and log — never crash the worker |
| S3 down | `upload_*` functions return `""` and log; report still ends up in DynamoDB but customer gets no link |

## External dependencies

| Vendor | Purpose | SDK | Failure isolated? |
|---|---|---|---|
| AWS S3 | Report + debug storage | boto3 | Yes (returns "") |
| AWS DynamoDB | Job state | boto3 | No — job tracking is critical |
| AWS SQS | Worker queue | boto3 | No — webhook needs to enqueue |
| AWS Bedrock | LLM narrative | langchain-aws | Yes (graceful degradation) |
| Stripe | Payments | stripe | No — payment flow is critical |
| Resend | Email | resend | Yes (logs + continues) |
| Mapbox | Geocoding + isochrones + maps | httpx | Partial (fallback to ZIP centroid) |
| Census | ACS demographics + ZCTA polygons | requests + tenacity | No — population is core to the report |
| AlphaSophia | Provider directory + CPT volumes | httpx + tenacity | No — provider data is core |
| Google Places | Site-of-care discovery | requests | No — site of care is core |

## Local development

LocalStack provides S3 + DynamoDB + SQS endpoints; switch on by setting `AWS_ENDPOINT_URL=http://localhost:4566` in `.env`. The init script in `localstack-init/` provisions the bucket, table, and queue.
