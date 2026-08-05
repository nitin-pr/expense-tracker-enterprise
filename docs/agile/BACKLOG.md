# Expense Tracker Enterprise — Product Backlog

Status: Draft v1.0
Companion docs: [../design/HLD.md](../design/HLD.md) · [../design/LLD.md](../design/LLD.md) · [../design/DATABASE_DESIGN.md](../design/DATABASE_DESIGN.md) · [SPRINT_PLAN.md](./SPRINT_PLAN.md)

Epics map 1:1 to the bounded contexts already defined in the architecture (LLD §11's module dependency graph), so the backlog's build order matches the system's actual dependency order rather than an arbitrary feature list. "Enabler" stories are technical foundation work with no direct end-user-facing behavior — written as "As a developer" per standard Agile practice, since they still need acceptance criteria and sizing.

**Sizing scale:** Fibonacci story points (1, 2, 3, 5, 8), calibrated for a small team (1–3 developers) on a portfolio-grade build — not an enterprise team's velocity. 8 is reserved for genuinely substantial stories (e.g. the full auth flow); most CRUD stories land at 3–5.

**Priority (MoSCoW):** Must = MVP-blocking. Should = important, ships in the first post-MVP pass. Could = valuable but deferrable without weakening the core product.

---

## Epic 01 — Foundation & Authentication (`accounts` + `common`)

Everything in the system depends on this epic (LLD §11: no module is upstream of `accounts` or `common`) — it must be built first.

### US-001 (Enabler): Project Scaffolding
**As a** developer, **I want** the project skeleton (`config/`, `apps/`, `common/`, `templates/`, `static/`, `media/`, `requirements.txt`, Dockerfile) created **so that** every subsequent story has a consistent structure to build in.
- **Acceptance Criteria:** Folder structure matches the HLD's specified layout; Django project boots with `manage.py runserver`; Docker image builds successfully; `requirements.txt` pins Django 5, DRF, drf-spectacular, firebase-admin.
- **Dependencies:** None.
- **Priority:** Must · **Size:** 3

### US-002 (Enabler): Common Package
**As a** developer, **I want** `common/` (exceptions, permissions, validators, constants, base repository/service classes) implemented **so that** every feature module depends on shared, tested cross-cutting code instead of duplicating it.
- **Acceptance Criteria:** `AppException` hierarchy + global DRF exception handler registered and returns structured JSON errors; `BaseRepository`/`BaseService` generics implemented per LLD §1; `IsOwner` permission implemented; core validators (positive amount, not-future-date, file type/size) implemented with unit tests.
- **Dependencies:** US-001.
- **Priority:** Must · **Size:** 5

### US-003: Email/Password Signup & Login
**As a** new user, **I want** to sign up and log in with email and password via Firebase **so that** I can securely access my personal expense data.
- **Acceptance Criteria:** Firebase project configured; frontend signup/login forms call Firebase client SDK; a valid Firebase ID token is obtained and attached as `Authorization: Bearer` on subsequent API calls; invalid credentials show a clear error; no password ever reaches the Django backend.
- **Dependencies:** US-001.
- **Priority:** Must · **Size:** 8

### US-004: Email Verification
**As a** new user, **I want** to verify my email after signup **so that** my account is confirmed before I'm trusted with sensitive financial data.
- **Acceptance Criteria:** Firebase verification email sent on signup; unverified users see a "please verify" prompt; verification status is checkable from the decoded token claims.
- **Dependencies:** US-003.
- **Priority:** Should · **Size:** 3

### US-005: Password Reset
**As a** user, **I want** to reset my password if I forget it **so that** I'm not permanently locked out of my account.
- **Acceptance Criteria:** "Forgot password" triggers Firebase's reset-email flow; user can set a new password via the emailed link; old password stops working immediately after reset.
- **Dependencies:** US-003.
- **Priority:** Must · **Size:** 2

### US-006: Google Login
**As a** user, **I want** to log in with my Google account **so that** I don't need to create or remember a separate password.
- **Acceptance Criteria:** Google OAuth via Firebase returns a valid ID token; first-time Google login creates a local `User` exactly like email signup does (same `get_or_create_by_firebase_uid` path).
- **Dependencies:** US-003, US-007.
- **Priority:** Could · **Size:** 3

### US-007: Backend Token Verification
**As the** Django backend, **I want** to verify Firebase ID tokens and resolve them to a local `User` record on every request **so that** API access is authenticated without Django ever storing a password.
- **Acceptance Criteria:** `FirebaseAuthentication` (LLD §2.2) rejects missing/invalid/expired tokens with 401; a valid token resolves or creates the matching local `User` via `firebase_uid`; `request.user` is populated for all downstream permission checks; unit-tested with a mocked `AuthProvider`.
- **Dependencies:** US-001, US-002.
- **Priority:** Must · **Size:** 5

### US-008: Profile Management
**As a** user, **I want** to view and update my profile (name, photo, currency, timezone, theme) **so that** the app reflects my personal preferences.
- **Acceptance Criteria:** `GET/PUT /api/auth/profile` returns/updates the fields listed; a user can only ever read/update their own profile (enforced, not just filtered).
- **Dependencies:** US-007.
- **Priority:** Should · **Size:** 3

### US-009 (Enabler): Django Admin Panel
**As an** admin, **I want** core models registered in Django admin **so that** I can inspect and manage data without building custom tooling.
- **Acceptance Criteria:** User, Category, Expense, Income, Budget, Notification are registered with sensible list/search/filter configuration; admin access requires Django staff status, separate from the Firebase user flow.
- **Dependencies:** US-001.
- **Priority:** Could · **Size:** 1

---

## Epic 02 — Categories

### US-010: Default Categories
**As a** new user, **I want** a default set of categories (Food, Travel, Bills, Entertainment, Medical, Education, Shopping, Investment, Salary, Other) available immediately **so that** I can start categorizing expenses without setup work.
- **Acceptance Criteria:** Seeded via an idempotent Django data migration (`created_by=NULL`); visible to every user via `GET /api/categories/`; re-running the migration doesn't duplicate rows.
- **Dependencies:** US-002.
- **Priority:** Must · **Size:** 3

### US-011: Create Custom Category
**As a** user, **I want** to create custom categories with a name, icon, and color **so that** I can categorize spending in ways specific to my life.
- **Acceptance Criteria:** `POST /api/categories/` creates a category owned by the requesting user; duplicate name for the same owner is rejected (400, matches the DB unique constraint); invalid hex color is rejected.
- **Dependencies:** US-007, US-010.
- **Priority:** Must · **Size:** 5

### US-012: Update/Delete Custom Category
**As a** user, **I want** to update or delete my custom categories **so that** I can correct mistakes or clean up unused ones.
- **Acceptance Criteria:** A user can edit/delete only categories they created; default categories cannot be edited or deleted by any user (403).
- **Dependencies:** US-011.
- **Priority:** Should · **Size:** 3

### US-013: Protect Categories In Use
**As a** user, **I want** to be prevented from deleting a category that still has expenses tied to it **so that** I don't silently lose the categorization of my financial history.
- **Acceptance Criteria:** Deleting a category with ≥1 expense returns a clear 400/409 with an actionable message, not a 500; matches the DB's `ON DELETE RESTRICT` (DATABASE_DESIGN.md) — the API error is a graceful surfacing of that constraint, not a bypass of it.
- **Dependencies:** US-011.
- **Priority:** Must · **Size:** 2

---

## Epic 03 — Expense Management

### US-014: Create Expense
**As a** user, **I want** to create an expense with title, amount, category, payment method, date, notes, and an optional receipt **so that** I can record my spending.
- **Acceptance Criteria:** `POST /api/expenses/` validates amount > 0, date not in the future, category belongs to the user or is a default, payment method is one of the enum values; created expense is owned by `request.user` automatically (never client-supplied).
- **Dependencies:** US-007, US-010.
- **Priority:** Must · **Size:** 5

### US-015: View / Update / Delete Expense
**As a** user, **I want** to view, update, and delete my own expenses **so that** I can manage my records over time.
- **Acceptance Criteria:** `GET/PUT/DELETE /api/expenses/{id}` only succeed for the owning user (`IsOwner`, 403 otherwise); a non-existent or another user's expense ID returns 404, not 403 (no existence leakage).
- **Dependencies:** US-014.
- **Priority:** Must · **Size:** 5

### US-016: Search Expenses
**As a** user, **I want** to search my expenses by title or description **so that** I can quickly find a specific transaction.
- **Acceptance Criteria:** `?search=` matches partial, case-insensitive text in title or description; empty search returns the full (still-paginated) list; search is scoped to the requesting user only.
- **Dependencies:** US-015.
- **Priority:** Must · **Size:** 3

### US-017: Filter Expenses
**As a** user, **I want** to filter my expenses by category, date range, amount range, and payment method **so that** I can narrow down the transactions I'm looking for.
- **Acceptance Criteria:** Each filter param works independently and in combination; invalid ranges (e.g. `date_from > date_to`) return a clear 400.
- **Dependencies:** US-015.
- **Priority:** Must · **Size:** 5

### US-018: Sort & Paginate Expenses
**As a** user, **I want** my expense list sorted and paginated **so that** browsing a large history stays fast and usable.
- **Acceptance Criteria:** Default sort is `-expense_date`; sortable by amount/date; page size is configurable within a sane max; response includes total count and next/previous page links.
- **Dependencies:** US-015.
- **Priority:** Must · **Size:** 3

### US-019: Receipt Attachment
**As a** user, **I want** to attach a receipt image/PDF to an expense **so that** I have proof of purchase stored alongside the record.
- **Acceptance Criteria:** Upload accepts image/PDF only, within a size limit (`common/validators`), rejects anything else with a clear error; attachment is retrievable only by the owning user; deleting the expense removes the stored file (per DATABASE_DESIGN.md's data-lifecycle note).
- **Dependencies:** US-014.
- **Priority:** Should · **Size:** 3

---

## Epic 04 — Income Management

### US-020: Record Income
**As a** user, **I want** to record income entries (source, amount, date) **so that** I can track money coming in, not just going out.
- **Acceptance Criteria:** `POST /api/income/` validates amount > 0 and source is a valid enum value (salary/freelancing/investment/bonus/other); owned by `request.user`.
- **Dependencies:** US-007.
- **Priority:** Must · **Size:** 3

### US-021: View / Update / Delete Income
**As a** user, **I want** to view, update, and delete my income entries **so that** I can keep my records accurate.
- **Acceptance Criteria:** Same ownership/404-vs-403 rules as US-015, applied to Income.
- **Dependencies:** US-020.
- **Priority:** Must · **Size:** 3

### US-022: Savings Calculation
**As a** user, **I want** to see my calculated savings (income − expenses) for a period **so that** I understand my net financial position, not just spending.
- **Acceptance Criteria:** Correctly nets income and expense totals for a given month/year; zero income or zero expense doesn't error, just yields a boundary-correct result.
- **Dependencies:** US-018, US-021.
- **Priority:** Should · **Size:** 2

---

## Epic 05 — Budget Management

### US-023: Set Monthly Budget
**As a** user, **I want** to set a monthly budget amount **so that** I have a spending target to track against.
- **Acceptance Criteria:** `POST /api/budgets/` validates budget > 0; only one budget per user per month/year is allowed (matches the DB unique constraint — a duplicate returns a clear 400, not a raw DB error).
- **Dependencies:** US-007.
- **Priority:** Must · **Size:** 3

### US-024: View Budget Status
**As a** user, **I want** to see my budget, amount spent, and remaining balance for the current month **so that** I know where I stand at a glance.
- **Acceptance Criteria:** Spent is computed live from actual expenses in the period (never a stale cached counter); remaining can go negative and displays as such, not clamped to zero.
- **Dependencies:** US-018, US-023.
- **Priority:** Must · **Size:** 3

### US-025: Budget Threshold Alerts
**As a** user, **I want** to be alerted when my spending crosses 80%, 90%, and 100% of my budget **so that** I can course-correct before overspending.
- **Acceptance Criteria:** Crossing each threshold fires exactly one alert for that tier per budget period; crossing 100% directly from below 80% (a single large expense) still fires the highest-tier alert, not all three; the Observer wiring (LLD §6) is used, not ad hoc checks scattered in views.
- **Dependencies:** US-014, US-024.
- **Priority:** Must · **Size:** 5

### US-026: Race-Safe Threshold Evaluation
**As the** system, **I want** budget-threshold evaluation to be race-safe under concurrent expense creation **so that** a user is never double-alerted or silently missed at a threshold.
- **Acceptance Criteria:** Two expenses created concurrently for the same user/month never produce two notifications for the same threshold tier; implemented per DATABASE_DESIGN.md's Transaction Strategy (`SELECT FOR UPDATE` + `UNIQUE(budget_id, threshold_tier)` backstop); covered by a concurrency test (e.g. two threads/requests racing against the same budget).
- **Dependencies:** US-025.
- **Priority:** Must · **Size:** 5

---

## Epic 06 — Notifications

### US-027: In-App Notifications
**As a** user, **I want** to see in-app notifications for budget alerts **so that** I don't have to actively check my budget status to know I'm close to a limit.
- **Acceptance Criteria:** `InAppNotificationChannel` persists a `Notification` row and it's retrievable via `GET /api/notifications/`; a threshold-crossing event always produces a visible in-app notification even if other channels fail.
- **Dependencies:** US-025.
- **Priority:** Must · **Size:** 3

### US-028: Email Notifications
**As a** user, **I want** to receive an email when I exceed my budget **so that** I'm alerted even when I'm not using the app.
- **Acceptance Criteria:** `EmailNotificationChannel` sends on 100% threshold at minimum; failure to send email doesn't block or roll back the underlying expense/budget transaction (channels are dispatched after the DB transaction commits).
- **Dependencies:** US-027.
- **Priority:** Could · **Size:** 3

### US-029: Daily Expense Reminder
**As a** user, **I want** a daily reminder to log expenses **so that** I build a habit of tracking spending consistently.
- **Acceptance Criteria:** A scheduled job dispatches a `daily_reminder` notification once per user per day; users who already logged an expense that day are skipped.
- **Dependencies:** US-027.
- **Priority:** Could · **Size:** 2

### US-030: Mark Notifications Read
**As a** user, **I want** to mark notifications as read **so that** my notification list reflects what I've already seen.
- **Acceptance Criteria:** `PATCH /api/notifications/{id}/` toggles `read`; unread count is queryable for a badge/indicator.
- **Dependencies:** US-027.
- **Priority:** Should · **Size:** 1

---

## Epic 07 — Dashboard (Facade — read-only, no models of its own)

### US-031: Dashboard Summary
**As a** user, **I want** a dashboard showing today's expense, monthly expense/income, remaining budget, and total categories **so that** I get an at-a-glance summary the moment I log in.
- **Acceptance Criteria:** Single `GET /api/dashboard/` call returns all summary fields (backed by `DashboardService`, LLD §9 — one facade call, not four separate frontend requests); correct even for a brand-new user with zero data (no divide-by-zero, no nulls where zero is expected).
- **Dependencies:** US-018, US-021, US-024, US-011.
- **Priority:** Must · **Size:** 5

### US-032: Recent Transactions Widget
**As a** user, **I want** to see my recent transactions on the dashboard **so that** I don't have to navigate away to see what I just logged.
- **Acceptance Criteria:** Shows the N most recent expenses (configurable, sensible default e.g. 5); reuses `ExpenseService.list_expenses`, not a duplicate query path.
- **Dependencies:** US-031.
- **Priority:** Should · **Size:** 2

### US-033: Dashboard Charts
**As a** user, **I want** charts (monthly expense trend, expense by category, income vs. expense) on my dashboard **so that** I can visually understand my financial patterns.
- **Acceptance Criteria:** Three Chart.js visualizations render from `DashboardService` data; charts degrade gracefully (empty-state, not a broken chart) when a user has insufficient data.
- **Dependencies:** US-031.
- **Priority:** Should · **Size:** 5

---

## Epic 08 — Reports & Export

### US-034: Generate Period Reports
**As a** user, **I want** to generate daily/weekly/monthly/yearly reports **so that** I can review my finances over different timeframes.
- **Acceptance Criteria:** `GET /api/reports/{period}` returns totals, category breakdown, and transaction list for the correct date range per `ReportPeriodStrategy` (LLD §8); an out-of-range/invalid period value returns 400.
- **Dependencies:** US-018, US-021.
- **Priority:** Should · **Size:** 5

### US-035: Export Report as CSV
**As a** user, **I want** to export a report as CSV **so that** I can analyze my data in other tools.
- **Acceptance Criteria:** `GET /api/reports/export?format=csv` streams a valid CSV matching the on-screen report data; filename includes the period for clarity.
- **Dependencies:** US-034.
- **Priority:** Should · **Size:** 3

### US-036: Export Report as Excel
**As a** user, **I want** to export a report as Excel **so that** I get a formatted spreadsheet rather than plain CSV.
- **Acceptance Criteria:** Valid `.xlsx` via `ExcelReportExporter`, opens correctly in Excel/Sheets, includes basic header formatting.
- **Dependencies:** US-034.
- **Priority:** Could · **Size:** 3

### US-037: Export Report as PDF
**As a** user, **I want** to export a report as PDF **so that** I have a shareable, printable summary.
- **Acceptance Criteria:** Valid PDF via `PDFReportExporter`, includes summary totals and a category breakdown table; renders correctly for both very small and very large report datasets (pagination within the PDF if needed).
- **Dependencies:** US-034.
- **Priority:** Could · **Size:** 5

---

## MoSCoW Summary

| Priority | Story count | Points | Stories |
|---|---|---|---|
| **Must** (MVP) | 21 | 84 | US-001,002,003,005,007,010,011,013,014,015,016,017,018,020,021,023,024,025,026,027,031 |
| **Should** (V1.1) | 9 | 27 | US-004,008,012,019,022,030,032,033,034 |
| **Could** (V1.1 / later) | 7 | 20 | US-006,009,028,029,035,036,037 |
| **Total** | 37 | 131 | |

See [SPRINT_PLAN.md](./SPRINT_PLAN.md) for how this backlog is sequenced into sprints.
