# Backend Changelog

Reverse-chronological log of meaningful backend changes. Append a new entry whenever a task in `docs/superpowers/plans/` lands, or whenever production behavior changes. One line per entry.

Format: `YYYY-MM-DD  <type>: <what changed>  (<plan-or-commit-ref>)`

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `ci`.

---

## 2026-04-25

- docs: README rewritten to reflect MERC backend; living docs (CLAUDE, ARCHITECTURE, MODULES, CHANGELOG) wired up (Phase 6)
- test: API endpoint tests landed for /providers, /jobs/status, /payments (Phase 5)
- test: service-layer tests with mocks landed for s3, queue, job_store, payment, email, geocoder, alphasophia (Phase 4)
- test: pure-function unit tests landed for cpt parsing, specialty lookups, validator, fee_schedule, common (severity/population/tags), distance helpers, google_maps internals (Phase 3)
- refactor: replace 8 stray `print()` calls with logging across main, utils, services
- chore: delete 5 stale `_debug_*.json` files from `backend/` root
- fix: ruff is green — 0 errors (was 9) — Phase 1 complete
- chore: relax mypy `ignore_missing_imports` to focus on real type errors (Phase 0)
- chore: backend cleanup & test coverage plan started — baseline: 9 ruff errors, 188 mypy errors, 21 tests passing, 8 stray prints, 5 debug JSON files in repo root (`docs/superpowers/plans/2026-04-25-backend-cleanup-and-test-coverage.md`)

## Final state (after 2026-04-25 cleanup)

- ruff: 0 errors
- pytest: 209 tests collected, all passing
- stray `print()`: 0
- stale `_debug_*.json` files in repo root: 0
- modules without docstrings: 0
- modules with at least 1 unit/integration test: every module listed in `docs/MODULES.md` except those marked `_no test_`
