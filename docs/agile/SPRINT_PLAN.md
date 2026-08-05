# Expense Tracker Enterprise — Sprint Plan

Status: Draft v1.0
Companion docs: [BACKLOG.md](./BACKLOG.md) · [../design/HLD.md](../design/HLD.md) · [../design/LLD.md](../design/LLD.md)

## Methodology & Assumptions

- **Framework:** Scrum, 2-week sprints.
- **Team:** 1–3 developers (portfolio/small-team scale — sprint sizing below assumes ~2, at a conservative ~18–22 points/sprint; a solo developer should expect roughly double the calendar time per sprint, not double the point count).
- **Sequencing rule:** sprints follow the architecture's actual module dependency graph (LLD §11) — `accounts`/`common` first, then `categories`, then `expenses`/`income`, then `budgets`, then `notifications`, then `dashboard`/`reports` last, since those two are pure aggregators over everything else. No sprint schedules a story ahead of something it depends on.
- **Ceremonies (scaled for a small team):**
  - *Sprint Planning* (start of sprint): pull stories per this plan, confirm each meets Definition of Ready.
  - *Daily Standup*: async (e.g. a written 3-line update) is sufficient below 3 people — the ceremony's value is the habit of surfacing blockers, not the meeting format.
  - *Sprint Review/Demo* (end of sprint): demo working software against the sprint goal — every sprint below ends with something runnable, not just merged code.
  - *Sprint Retrospective* (end of sprint): what worked, what didn't, one concrete change for next sprint.

## Definition of Ready (a story may enter a sprint when)

- Written in "As a / I want / so that" form with acceptance criteria (already done for all stories in the Backlog).
- Dependencies are either already done or explicitly sequenced into an earlier sprint.
- The relevant HLD/LLD/DB design section is identified, so implementation doesn't require re-deriving architecture mid-sprint.
- Sized by the team (all stories below are pre-sized; re-confirm at planning time — sizes are estimates, not commitments).
- No open question blocks starting work (e.g. "which PDF library" should be resolved before US-037 starts, not during it).

## Definition of Done (a story is done when)

- Implemented per the mandated layering — business logic lives in the Service layer, never in views or serializers (HLD, non-negotiable).
- Unit tests written for Service-layer logic and passing (Repository layer mocked/faked per LLD's Dependency Inversion design — this is *why* that boundary exists).
- New/changed endpoints documented via drf-spectacular and visible in the generated Swagger UI.
- Manually verified against every acceptance criterion on the story.
- Code reviewed (self-review with a fresh-eyes pass for solo work; peer review if 2–3 developers).
- No new linter errors; migrations included and applied cleanly on a fresh DB.
- Merged to the main integration branch.

---

## Release Plan

| Release | Sprints | Content |
|---|---|---|
| **MVP** | 1–5 | All *Must* stories: auth, categories, full expense/income CRUD + search/filter/sort, budgets with race-safe threshold alerts, in-app notifications, dashboard summary |
| **V1.1** | 6–8 | All *Should*/*Could* stories: profile polish, attachments, savings calc, dashboard charts, reports + all export formats, Google login, email/reminder notifications, admin polish |

MVP ships a genuinely complete core product (everything in the doc's "Project Goals" except polish/exports) at the end of Sprint 5 — about 10 weeks in — rather than holding everything for one big-bang release.

---

## Sprint 1 — Foundation & Authentication Core

**Goal:** The project skeleton and shared `common/` package exist; a user can register and log in through Firebase, and the Django API can verify their identity end-to-end.

| Story | Points |
|---|---|
| US-001 Project Scaffolding | 3 |
| US-002 Common Package | 5 |
| US-003 Email/Password Signup & Login | 8 |
| US-007 Backend Token Verification | 5 |
| US-005 Password Reset | 2 |
| **Total** | **23** |

*Note:* slightly above target velocity — acceptable for Sprint 1, since foundational/scaffolding work is inherently front-loaded and has no prior sprint to have absorbed it.

---

## Sprint 2 — Categories & Expense CRUD

**Goal:** Users can categorize spending (defaults + custom) and fully create/view/update/delete individual expenses.

| Story | Points |
|---|---|
| US-010 Default Categories | 3 |
| US-011 Create Custom Category | 5 |
| US-013 Protect Categories In Use | 2 |
| US-014 Create Expense | 5 |
| US-015 View / Update / Delete Expense | 5 |
| **Total** | **20** |

---

## Sprint 3 — Expense Power Features & Income

**Goal:** The expense list is production-grade (searchable, filterable, sortable, paginated), and income tracking is available alongside expenses.

| Story | Points |
|---|---|
| US-016 Search Expenses | 3 |
| US-017 Filter Expenses | 5 |
| US-018 Sort & Paginate Expenses | 3 |
| US-020 Record Income | 3 |
| US-021 View / Update / Delete Income | 3 |
| **Total** | **17** |

---

## Sprint 4 — Budgets & Threshold Safety

**Goal:** Users can set a monthly budget and see accurate, race-safe spend/remaining/threshold-alert status — the highest-risk piece of business logic in the whole system (concurrency), tackled deliberately in its own sprint rather than squeezed in alongside other work.

| Story | Points |
|---|---|
| US-023 Set Monthly Budget | 3 |
| US-024 View Budget Status | 3 |
| US-025 Budget Threshold Alerts | 5 |
| US-026 Race-Safe Threshold Evaluation | 5 |
| **Total** | **16** |

---

## Sprint 5 — Notifications, Dashboard & MVP Hardening

**Goal:** Threshold alerts are visible in-app, the dashboard aggregates everything built so far into one summary view, and the sprint closes with a deliberate hardening pass — MVP demo-ready.

| Story | Points |
|---|---|
| US-027 In-App Notifications | 3 |
| US-031 Dashboard Summary | 5 |
| Hardening buffer: cross-module manual QA, bug-fixing, MVP demo prep | ~8 (buffer, not a backlog story) |
| **Total** | **~16 (8 backlog + buffer)** |

*Why a buffer here specifically:* Sprint 5 is the first point every module (accounts, categories, expenses, income, budgets) is exercised together through the Dashboard facade — integration bugs are far more likely to surface here than in earlier, more isolated sprints. Building in explicit hardening time instead of assuming zero integration risk is the realistic choice, not a padded estimate.

**→ MVP release candidate at the end of Sprint 5.**

---

## Sprint 6 — Account & Expense Polish

**Goal:** The account/profile experience and expense/category management reach full polish beyond bare CRUD.

| Story | Points |
|---|---|
| US-004 Email Verification | 3 |
| US-008 Profile Management | 3 |
| US-012 Update/Delete Custom Category | 3 |
| US-019 Receipt Attachment | 3 |
| US-022 Savings Calculation | 2 |
| **Total** | **14** |

---

## Sprint 7 — Dashboard Richness & Reports

**Goal:** The dashboard becomes visually rich (charts, recent transactions), notifications gain a read/unread state, and users can generate period reports.

| Story | Points |
|---|---|
| US-030 Mark Notifications Read | 1 |
| US-032 Recent Transactions Widget | 2 |
| US-033 Dashboard Charts | 5 |
| US-034 Generate Period Reports | 5 |
| **Total** | **13** |

---

## Sprint 8 — Export, Secondary Auth & Remaining Notifications

**Goal:** All report export formats ship, Google login is available, and the remaining notification channels (email, daily reminder) complete the full scope of the original spec.

| Story | Points |
|---|---|
| US-006 Google Login | 3 |
| US-009 Django Admin Panel | 1 |
| US-028 Email Notifications | 3 |
| US-029 Daily Expense Reminder | 2 |
| US-035 Export Report as CSV | 3 |
| US-036 Export Report as Excel | 3 |
| US-037 Export Report as PDF | 5 |
| **Total** | **20** |

**→ Full V1.1 release at the end of Sprint 8** — complete coverage of every module in the original project spec.

---

## Velocity Summary

| Sprint | Points | Cumulative |
|---|---|---|
| 1 | 23 | 23 |
| 2 | 20 | 43 |
| 3 | 17 | 60 |
| 4 | 16 | 76 |
| 5 | 16 (incl. buffer) | 92 |
| 6 | 14 | 106 |
| 7 | 13 | 119 |
| 8 | 20 | 139 |

131 backlog points + Sprint 5's hardening buffer ≈ 139 total, across 8 sprints / 16 weeks (~4 months at assumed 2-developer velocity; longer for a solo developer, unchanged in sequencing). Re-baseline this table after Sprint 1–2 actuals — story points are a planning estimate, not a guarantee, and this plan should be treated as living, not fixed.

## Post-Release Backlog Candidates (explicitly out of scope for Sprints 1–8)

Per the original doc's "Future Improvements" and this project's own Evolution Roadmap (HLD): Celery + Redis for async report export/notifications, PostgreSQL-specific production hardening, CI/CD via GitHub Actions, cloud deployment. These are infrastructure/scale investments, correctly deferred until the product they'd support already exists.
