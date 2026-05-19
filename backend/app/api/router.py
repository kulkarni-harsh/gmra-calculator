"""Top-level API router with selective API-key auth.

Open endpoints (no key required):
  - GET  /health           — ALB target group health check
  - POST /payments/webhook/stripe — Stripe signs requests with its own secret

Everything else flows through require_api_key.
"""
from fastapi import APIRouter, Depends

from app.api.endpoints import (
    health,
    jobs,
    payment,
    providers,
    report_a1,
    report_t1,
    report_t2,
    report_t3,
)
from app.core.auth import require_api_key

# Open router — no auth dependency.
open_router = APIRouter()
open_router.include_router(health.router, tags=["health"], prefix="/health")

# Payments router on open_router — webhook has its own Stripe-signature auth;
# payment-intent endpoints validate Stripe state themselves.
open_router.include_router(payment.router, tags=["payments"], prefix="/payments")

# Protected router — every request needs an API key OR an internal Origin.
protected_router = APIRouter(dependencies=[Depends(require_api_key)])
protected_router.include_router(providers.router, tags=["providers"], prefix="/providers")
protected_router.include_router(jobs.router, tags=["jobs"], prefix="/jobs")
protected_router.include_router(report_t1.router, tags=["reports-t1"], prefix="/reports/t1")
protected_router.include_router(report_t2.router, tags=["reports-t2"], prefix="/reports/t2")
protected_router.include_router(report_t3.router, tags=["reports-t3"], prefix="/reports/t3")
protected_router.include_router(report_a1.router, tags=["reports-a1"], prefix="/reports/a1")

api_router = APIRouter()
api_router.include_router(open_router)
api_router.include_router(protected_router)
