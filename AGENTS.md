# EdgeTraz Agro — Coding Standards & GGA Review Rules

> **Última actualización**: 2026-06-29
> Estas reglas son aplicadas por Gentleman Guardian Angel (gga) en cada commit y PR.
> Stack: React 19 + Vite 6 + TypeScript 5.8 | Rust (Edge Engine) | AI/ML (TinyML, Gemini)

## ⛔ NON-NEGOTIABLES (MUST NOT)

These rules are absolute. Any violation causes the review to FAIL.

- **MUST NOT** break audit trail integrity, event immutability, or digital signature chains.
- **MUST NOT** introduce secrets, real credentials, API keys, or production tokens in code.
- **MUST NOT** use `any` type; use precise types, `unknown`, or justified generics instead.
- **MUST NOT** hardcode crop thresholds, sensor calibration values, or compliance limits without referencing them from config/constants.
- **MUST NOT** use raw `number` for GPS coordinates, timestamps, or monetary values without branded types or value objects.
- **MUST NOT** bypass offline-first sync logic — all mutations MUST be queued for eventual sync.
- **MUST NOT** suppress errors silently (empty catch blocks, `.catch(() => {})`, ignored Rust `Result`).
- **MUST NOT** perform broad refactors without an explicit migration plan.

## ✅ REQUIRED PRACTICES (MUST)

- **MUST** validate all user inputs with schemas at component/service boundaries (Zod schemas).
- **MUST** preserve end-to-end type safety across the full stack.
- **MUST** use branded IDs or domain value objects for Lot IDs, Plot IDs, Container IDs, and compliance records.
- **MUST** keep edge processing logic deterministic — no random seeds in sensor fusion or AI inference without explicit documentation.
- **MUST** add or update tests for changed behavior.
- **MUST** update docs when public behavior, setup, contracts, or compliance assumptions change.
- **MUST** prefer small, verifiable, reversible changes.
- **MUST** include compliance/safety validation in PRs touching phytosanitary, traceability, or export workflows.
- **MUST** validate that offline mutations are idempotent (safe to replay after reconnection).

## 🏗️ Architecture Rules

- Use **Vertical Slice** for feature organization (screen modules with co-located components, hooks, schemas).
- Keep **UI components pure and presentational** — business logic lives in custom hooks or services.
- **Offline-first**: All data mutations go through a write-ahead queue before API sync.
- **Rust Edge Engine** must be compiled with `no_std` compatibility for embedded targets (ESP32).
- AI/ML models in the frontend must use **TinyML/TensorFlow Lite** — no cloud-dependent inference.
- MQTT payloads must include message ID, timestamp, and signature for exactly-once delivery semantics.
- `screens/` contain page-level components; `components/` contain shared/reusable UI.

## 🔒 Security Rules

- **MUST NOT** have hardcoded secrets or credentials.
- **MUST NOT** have silent error handling (empty catch blocks, swallowed rejections, ignored `Result`).
- **MUST NOT** have production `console.log`.
- **MUST NOT** miss farm/plot/producer scoping in queries and APIs.
- **MUST NOT** use GPS or sensor data without precision validation (e.g., lat/lng bounds checking).
- **MUST NOT** miss tests for new business logic.
- **MUST NOT** change public contracts without tests and docs.
- **API keys** (Gemini, MQTT, etc.) MUST be configured via environment variables, validated at build time.

## 🧪 Testing Rules

- **MUST** write tests for new business logic, especially sync, audit, and compliance workflows.
- **MUST** verify sync idempotency in tests (replaying the same mutation produces the same state).
- **MUST** prefer Vitest for frontend tests.
- **Tests MUST** be deterministic — no timezone-dependent assertions, no shared mutable state.
- **Edge cases**: test offline→online transitions, sensor disconnection, partial data arrival.

## 📐 Style & Conventions

- **MUST** use TypeScript strict mode.
- **MUST** use `import type` for type-only imports in TypeScript.
- **MUST** use conventional commits: `feat:`, `fix:`, `refactor:`, `chore:`, `docs:`, `test:`, `ci:`.
- **MUST** keep commits atomic — one logical change per commit.
- **MUST NOT** add `Co-Authored-By` or AI attribution to commits.
- **Prefer** Biome over ESLint for linting and formatting (when available).
- **Prefer** small focused files over large monolithic ones.
- Rust code MUST use `rustfmt` with the project configuration.
- **Naming**: React components in PascalCase, hooks prefixed with `use`, utilities in camelCase.

## 🚜 Agro-Industrial Domain Rules

When reviewing code that touches agro-industrial / traceability logic:

- **MUST** preserve event immutability — once a trace event is recorded, it cannot be deleted, only superseded.
- **MUST** preserve `lotId` scoping across all queries that access production data.
- **MUST** validate compliance data against GlobalG.A.P. / SENASA / FSMA thresholds.
- **MUST** handle sensor data gaps gracefully (missing temperature/humidity points should not crash the pipeline).
- **MUST** include crop type and harvest date context in any export/audit report generation.
- **MUST** validate that timestamps are in UTC for cross-region synchronization.
- **Review**: any change to traceability chain or audit logic needs compliance-focused tests.

## 📦 Dependency Rules

- **MUST NOT** introduce unnecessary dependencies.
- **Prefer** existing patterns and libraries over new ones.
- **MUST** keep the lockfile in sync (`bun.lock` matches `package.json`).
- **MUST** use `bun install --frozen-lockfile` in CI.
- **Rust dependencies** MUST be audited for `no_std` compatibility when targeting embedded devices.

## 🚫 REJECT (Fail Review)

The review MUST FAIL if any of these are detected:

1. Hardcoded secrets or credentials.
2. `any` type without explicit justification.
3. Silent error handling (empty `catch` blocks, `.catch(() => {})`, ignored `Result`).
4. Production `console.log` (warn first offense, fail second).
5. Missing farm/plot/producer scoping in API/query/job.
6. Broken event immutability or offline sync logic.
7. Compliance data handling without validation against known thresholds.
8. Missing tests for new business logic.
9. Public contract changes without docs and tests.
10. `Co-Authored-By` or AI attribution in commit messages.
11. Use of `any` keyword.
12. Sensor data without precision/range validation.
13. MQTT messages without message ID or timestamp.

## Review Format

When reviewing, produce this output format:

```
## Review Summary

### ✅ Passed Rules
- {rule}: {brief evidence}

### ❌ Failed Rules
- {rule}: {violation description} — {file:line}

### ⚠️ Warnings
- {rule}: {concern} — {file:line}

### Verdict
PASS | FAIL | PASS WITH WARNINGS
```

Be objective. Quote the specific code that violates rules. For PASS WITH WARNINGS, the warnings must be non-blocking concerns.
