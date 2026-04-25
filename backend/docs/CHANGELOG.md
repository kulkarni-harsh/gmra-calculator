# Backend Changelog

Reverse-chronological log of meaningful backend changes. Append a new entry whenever a task in `docs/superpowers/plans/` lands, or whenever production behavior changes. One line per entry.

Format: `YYYY-MM-DD  <type>: <what changed>  (<plan-or-commit-ref>)`

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `ci`.

---

## 2026-04-25

- refactor: replace 8 stray `print()` calls with logging across main, utils, services
- chore: delete 5 stale `_debug_*.json` files from `backend/` root
- fix: ruff is green — 0 errors (was 9) — Phase 1 complete
- chore: relax mypy `ignore_missing_imports` to focus on real type errors (Phase 0)
- chore: backend cleanup & test coverage plan started — baseline: 9 ruff errors, 188 mypy errors, 21 tests passing, 8 stray prints, 5 debug JSON files in repo root (`docs/superpowers/plans/2026-04-25-backend-cleanup-and-test-coverage.md`)
