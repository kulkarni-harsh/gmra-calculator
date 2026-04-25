# Backend Modules

One row per module. Update the **Tests** column whenever test coverage changes (add/remove tests for the module). Keep entries terse — the source is the source of truth for code; this doc explains intent.

## app/api/endpoints

| File | Responsibility | Tests |
|---|---|---|
| `health.py` | `GET /api/health` liveness check | `tests/test_health.py` |
| `jobs.py` | `GET /api/jobs/status/{job_id}` poll job state | `tests/test_api_jobs.py` |
| `providers.py` | List specialties, search providers, fetch one provider | `tests/test_api_specialties.py` |
| `payment.py` | Create Stripe PaymentIntents (A1/T1/T2), Stripe webhook | `tests/test_api_payment.py` |
| `report_a1.py` | Submit A1 (provider-centric) report jobs | _no test_ |
| `report_t1.py` | Submit T1 (market entry) report jobs | _no test_ |
| `report_t2.py` | Submit T2 (custom CPT) report jobs | _no test_ |

## app/core

| File | Responsibility |
|---|---|
| `config.py` | `Settings` (pydantic-settings) — all env vars in one place |
| `logging.py` | `configure_logging()` — single entry point |
| `types.py` | Shared TypedDicts (`SexAgeCounts`, `ZipPopulationMap`) |

## app/services

| File | Responsibility | Tests |
|---|---|---|
| `s3.py` | Upload reports, debug artifacts, generate presigned URLs | `tests/test_s3_uploads.py`, `tests/test_debug_artifacts.py` |
| `queue.py` | SQS send/receive/delete | `tests/test_queue.py` |
| `job_store.py` | DynamoDB CRUD for jobs (idempotent claim flow) | `tests/test_job_store.py` |
| `payment.py` | Stripe PaymentIntent creation + verification | `tests/test_payment_service.py` |
| `email.py` | Resend transactional emails | `tests/test_email_service.py` |
| `geocoder.py` | Mapbox forward geocoder (httpx) | `tests/test_geocoder_mapbox.py` |
| `geocoding.py` | OpenCage-based geocoding + distance helpers | `tests/test_geocoding_distance.py` |
| `google_maps.py` | Google Places nearby search + dedup + site-of-care assembly | `tests/test_google_maps_helpers.py`, `tests/test_site_of_care_aggregation.py`, `tests/test_debug_artifacts.py` |
| `census.py` | Census ACS demographics + TIGERweb ZCTA polygons | _no test_ |
| `mapbox.py` | Isochrones + map rendering | _no test_ |
| `bedrock_llm.py` | Bedrock (Claude) market analysis | _no test_ |
| `alphasophia.py` | Provider/CPT data fetcher (httpx + retry) | `tests/test_alphasophia.py` |
| `cpt.py` | CPT code parsing + range matching + placeholders | `tests/test_cpt_parsing.py` |
| `specialty.py` | Specialty population calc + anchor CPT info | _no test_ |
| `mapper.py` | Folium-based map rendering | _no test_ |
| `pdf.py` | HTML → PDF via Playwright | _no test_ |
| `ppt.py` | PowerPoint placeholder substitution | _no test_ |
| `plots.py` | Matplotlib/Seaborn chart generation | _no test_ |
| `screenshotter.py` | Selenium-based site screenshots | _no test_ |
| `html_imputers.py` | Render HTML report from template + data | _no test_ |
| `report_generator.py` | T1/T2 report orchestration | `tests/test_site_of_care_aggregation.py`, `tests/test_debug_artifacts.py` |
| `_report_generator_a1_archived.py` | A1 (legacy) orchestration — frozen | _no test_ |
| `fee_schedule.py` | Medicare PFS rate calculator | `tests/test_fee_schedule.py` |

## app/utils

| File | Responsibility | Tests |
|---|---|---|
| `common.py` | Severity scoring, density lookup, taxonomy/source-tab/anchor-CPT helpers, RVU/GPCI loaders, demographics aggregation, tag generation | `tests/test_common_utils.py`, `tests/test_specialty_lookups.py` |
| `specialty.py` | `get_google_places_keywords` | `tests/test_specialty_lookups.py` |
| `validator.py` | Specialty Master sheet validator, geocoding inputs | `tests/test_validator.py` |

## app/types

| File | Responsibility |
|---|---|
| `cpt.py` | `CPT` Pydantic model + merge logic |
| `google_maps.py` | `GooglePlace`, `SiteOfCare` |
| `alphasophia.py` | `Provider` (provider directory record) |
| `common_provider_siteofcare.py` | `Location`, `Taxonomy` |
| `baseline_report_template.py` | Report template DTOs (`CptRowV2`, `ProviderProfileV2`, etc.) |

## app/schemas

| File | Responsibility |
|---|---|
| `health.py` | Health response model |
| `provider_request.py` | A1 report request (with `client_provider`) |
| `address_report_request.py` | T1 report request (address + drive time) |
| `t2_report_request.py` | T2 report request (T1 + custom CPT codes) |
| `payment.py` | Payment intent request schemas |
| `slides.py` | (Legacy) PowerPoint slide DTOs |
