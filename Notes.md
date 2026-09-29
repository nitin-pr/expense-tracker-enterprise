# Learning Notes — Expense Tracker Enterprise

A running, dated log of what I actually learned while building this project — commands run, what each parameter does, concepts, and mistakes (kept, not hidden, because they're often the best teacher). Updated daily as we go.

**How to read this file:** newest work is added as a new `## Day N` section at the bottom, in the order things actually happened. Each command is shown exactly as run, followed by a parameter-by-parameter breakdown.

---

## Day 1 — 2026-08-05 — Sprint 1: US-001 Project Scaffolding

**Goal for the day:** stand up the Django project skeleton per the HLD/LLD, wire it into Docker, and take it through a full branch → PR → merge cycle on GitHub — the first real implementation work after the design/planning phase (HLD, LLD, Database Design, Agile backlog + sprint plan, GitHub repo/issues/project board — all from earlier sessions, see `docs/design/` and `docs/agile/`).

### 1. Tooling decisions

- **Shell: Git Bash**, not PowerShell — chosen for portability. Its command syntax (`source venv/Scripts/activate`, forward slashes) matches what almost every Django tutorial, official doc, and GitHub Actions log (Linux-based) uses, so commands learned here transfer directly to other machines/OSes without mental translation.
- **Editor: VS Code**, with its integrated terminal's default profile switched to Git Bash (`Ctrl+Shift+P` → *Terminal: Select Default Profile* → Git Bash) so terminal work and file editing stay in one window.

### 2. Virtual environment

**Why it matters:** the global Python on this machine already had Django 4.2.4 and ~300 unrelated packages installed. Without a virtual environment, this project's dependencies would mix with every other Python project on the machine — a classic source of version-conflict bugs. A venv gives one project its own private, disposable copy of Python packages.

```bash
python -m venv venv
```
- `-m venv` — runs Python's built-in `venv` module as a script (no separate install needed, it ships with Python 3.3+).
- `venv` (final argument) — the name/path of the folder to create the environment in. By convention this folder is called `venv` and is git-ignored, never committed.

```bash
source venv/Scripts/activate
```
- `source` — runs the script *in the current shell* rather than a subshell, so the environment variables it sets (`PATH`, `VIRTUAL_ENV`) persist in your terminal session instead of vanishing when the script exits.
- `venv/Scripts/activate` — the activation script's path. (Note: `Scripts/` on Windows, `bin/` on macOS/Linux — this is the one command that differs by OS even under Git Bash.)
- Tell: prompt gains a `(venv)` prefix once active.

```bash
pip list
```
- No arguments — lists every package installed in the *currently active* environment. Used here purely as a sanity check: right after creating the venv it should show almost nothing (`pip`, `setuptools`), proving isolation from the global environment.

### 3. Installing core dependencies

```bash
pip install "django>=5,<6" djangorestframework drf-spectacular firebase-admin
```
- `"django>=5,<6"` — a **version specifier**, quoted because `>` and `<` are shell redirection operators and would otherwise be interpreted by Bash instead of passed to pip. This pins Django to the 5.x series specifically (matching the HLD's tech stack decision), excluding a future 6.x that hasn't been vetted against this design.
- `djangorestframework` — the DRF package (importable as `rest_framework`, confusingly a different name than the PyPI package).
- `drf-spectacular` — generates OpenAPI/Swagger schema from DRF views/serializers automatically.
- `firebase-admin` — server-side SDK for verifying Firebase ID tokens (needed later for US-007, installed now so `requirements.txt` is complete from day one per US-001's acceptance criteria).

Result confirmed: **Django 5.2.17**, DRF 3.17.2, drf-spectacular 0.30.0, firebase_admin 7.5.0 — all correctly on the 5.x/current lines, not the stale global 4.2.4.

### 4. Freezing dependencies

```bash
pip freeze > requirements.txt
```
- `freeze` — lists every installed package **with its exact resolved version** (`Django==5.2.17`, not just `Django`), including every transitive dependency pip pulled in automatically (e.g. `grpcio`, `protobuf` came along with `firebase-admin`).
- `>` — shell redirection: sends the command's stdout into `requirements.txt`, overwriting any existing content. This file is what makes the project reproducible — `pip install -r requirements.txt` on any machine (or inside Docker) recreates this exact dependency set.

### 5. Generating the Django project

```bash
django-admin startproject config .
```
- `startproject config` — scaffolds a new Django project named `config` (matches the HLD's folder layout, where `config/` holds settings/URLs/WSGI, separate from the `apps/` and `common/` packages).
- `.` (trailing dot) — tells Django to use the **current directory** as the project root instead of creating a new wrapping folder. Without it, you'd get a redundant `config/config/` nested structure with `manage.py` one level too deep.

Verified with `ls -la` / `ls config` — confirmed `config/` (with `settings.py`, `urls.py`, `wsgi.py`, `asgi.py`, `__init__.py`) and `manage.py` landed directly at the repo root, no nesting.

```bash
python manage.py runserver
```
- No arguments — starts Django's built-in **development** server, default `127.0.0.1:8000`. Confirmed the vanilla scaffold boots (Django's default "it worked" page) before layering any customization on top.
- **Important distinction learned:** this is a *dev-only* server (single-threaded, not hardened) — never what you'd run in production or in a Docker image. That's why we installed `gunicorn` separately later (see §7).

### 6. Building the folder skeleton

```bash
mkdir -p apps common/constants common/middleware common/permissions common/utils common/validators common/exceptions templates static media tests
```
- `-p` — create parent directories as needed, and don't error if a directory already exists. Lets you create a whole nested tree (`common/constants`, etc.) in one call instead of one `mkdir` per folder.

**Mistake made:** a typo/terminal-wrapping issue caused this folder to be created as `test/` (singular) instead of `tests/`. Caught it by running a plain `ls` and comparing against the expected HLD layout before doing anything else with it — cheaper to fix a wrong folder name before files exist inside it than after.

```bash
mv test tests
```
- Renames `test` → `tests` (on the same filesystem, `mv` is a rename, not a copy+delete).

```bash
touch apps/__init__.py common/__init__.py common/constants/__init__.py common/middleware/__init__.py common/permissions/__init__.py common/utils/__init__.py common/validators/__init__.py common/exceptions/__init__.py tests/__init__.py
```
- `touch` — creates each listed file if it doesn't exist (empty), or just bumps its modified-time if it does.
- **Why `__init__.py` specifically:** it's what marks a folder as an importable Python *package* rather than just a plain directory — e.g. it's what makes `from common.exceptions import AppException` resolve. `templates/`, `static/`, and `media/` deliberately do **not** get one — they're not Python packages, Django locates them by path configuration in `settings.py` instead.

```bash
find apps common tests -type f
```
- Searches inside the three given directories.
- `-type f` — restrict results to regular files (excludes the directories themselves). Used to verify all nine `__init__.py` files landed in the right places.

### 7. Wiring `settings.py`

Four manual edits made in VS Code (not shell commands):
1. Added `'rest_framework'` and `'drf_spectacular'` to `INSTALLED_APPS`.
2. Added `REST_FRAMEWORK = {'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema'}` and a `SPECTACULAR_SETTINGS` dict (title/description/version for the generated API docs).
3. Changed `TEMPLATES[0]['DIRS']` from `[]` to `[BASE_DIR / 'templates']` so Django actually looks in our `templates/` folder.
4. Added `STATICFILES_DIRS = [BASE_DIR / 'static']`, `MEDIA_URL = '/media/'`, `MEDIA_ROOT = BASE_DIR / 'media'` below the existing `STATIC_URL` line.

```bash
python manage.py check
```
- Runs Django's **system check framework** — validates settings/models/URL config for obvious errors *without* starting a server or touching the database. Much faster than a full `runserver` boot for a quick sanity pass.

**Mistake made (the important one):** the first time this was run, it printed "no issues" — but that was misleading. The edits above had been made in VS Code but **not saved** yet. `manage.py check` reads the file *from disk*, not from the editor's unsaved buffer, so it was silently validating the *old* version of the file (which was also valid, just without any of the four edits). This surfaced much later, after the changes had already gone through `git add`/commit/push/PR — the PR simply didn't contain them, because they were never actually written to disk at commit time.

**Lesson:** an editor with unsaved changes and the terminal are looking at two different versions of the file. Always save (`Ctrl+S`) before running anything that reads from disk, and don't fully trust a "no issues" result as proof a specific edit is present — when in doubt, `git diff` the file to see what's *actually* changed on disk.

### 8. Production server + Docker

```bash
pip install gunicorn
pip freeze > requirements.txt
```
- Installed **gunicorn**, a production-grade WSGI server, specifically *instead of* ever shipping `manage.py runserver` inside Docker. Re-froze `requirements.txt` to capture it.

**`.dockerignore`** (repo root) — keeps `venv/`, `.git/`, local DB, and docs out of the Docker build context, for speed and image size:
```
venv/
.git/
.gitignore
.gitattributes
__pycache__/
*.pyc
db.sqlite3
media/
docs/
*.md
.env
```

**`Dockerfile`** (repo root):
```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```
- `PYTHONDONTWRITEBYTECODE=1` — stops Python writing `.pyc` cache files into the image; dead weight in a container rebuilt from scratch each time.
- `PYTHONUNBUFFERED=1` — makes stdout/logs show up immediately in `docker logs` instead of being buffered.
- `COPY requirements.txt .` + `RUN pip install ...` **before** `COPY . .` — deliberate layer ordering. Docker caches each instruction as a layer; if only application code changes (not `requirements.txt`), Docker can reuse the cached "install dependencies" layer instead of redoing it on every build.
- `config.wsgi:application` — the WSGI entry point gunicorn serves: the `application` object inside `config/wsgi.py`, which Django's `startproject` generated automatically.

```bash
docker build -t expense-tracker-enterprise .
```
- `-t expense-tracker-enterprise` — tags the built image with this name (so it can be referenced later without a hash, e.g. `docker run expense-tracker-enterprise`).
- `.` (trailing) — the **build context**: the directory Docker sends to the daemon and where it looks for `Dockerfile` by default.
- Confirmed a successful build (image exported/tagged cleanly).

### 9. Git branching workflow — "like a real developer"

**Branch naming convention adopted:** `feature/us-XXX-short-description` — ties every branch back to its backlog ID so it's traceable to both the GitHub issue and the sprint plan.

```bash
git status
```
- Shows staged / unstaged / untracked changes relative to the last commit. Used repeatedly throughout the day as a sanity check before committing — confirmed `venv/` and `db.sqlite3` never appeared (correctly gitignored) and that only the intended files were new.

```bash
git checkout -b feature/us-001-project-scaffolding
```
- `-b <name>` — creates a new branch with the given name **and** switches to it in one step (equivalent to `git branch <name>` + `git checkout <name>`).
- Since nothing had been committed yet, all the day's uncommitted work simply "came with" onto the new branch — `master` stayed untouched.

```bash
git branch
```
- Lists local branches; the current one is marked with `*`. Used to confirm the switch worked.

```bash
git add config apps common tests static templates manage.py requirements.txt Dockerfile .dockerignore
```
- Stages each named path for the next commit. `static`/`templates` were included even while empty — harmless no-op, kept for consistency since they'll have content later.

```bash
git commit -m "Scaffold Django project structure per HLD/LLD" -m "Sets up config/, apps/, common/ packages, static/media/templates wiring, DRF + drf-spectacular registration, and a production Dockerfile using gunicorn."
```
- `-m "..."` — supplies the commit message inline (skips opening an external editor).
- **Repeating `-m`** creates additional message *paragraphs*, each separated by a blank line automatically — an easier alternative to typing a literal multi-line string, where you'd otherwise need to keep an open quote across several `Enter` presses (Bash won't execute the command until the quote closes; it just shows a `>` continuation prompt for each line typed inside it).

```bash
git push -u origin feature/us-001-project-scaffolding
```
- `-u` (`--set-upstream`) — links the local branch to `origin/feature/us-001-project-scaffolding`, so future `git push`/`git pull` on this branch need no extra arguments.

```bash
gh pr create --base master --head feature/us-001-project-scaffolding \
  --title "US-001: Project Scaffolding" \
  --body "..."
```
- `--base master` — the branch we want to merge *into*.
- `--head feature/us-001-project-scaffolding` — the branch containing our changes.
- `--title` / `--body` — the PR's title and description. The body included `Closes #1` — GitHub's special syntax that auto-closes issue #1 (US-001) the moment this PR merges into the default branch.
- **First attempt failed** (`No commits between master and feature/...`) because the `git push` above hadn't actually been run yet — `gh pr create` can't diff against a branch that doesn't exist on the remote. Re-ran push, then PR creation succeeded → **PR #38** (numbered 38, not 2, because GitHub shares one counter across issues *and* PRs in a repo — we'd already used 1–37 on the 37 backlog issues).

### 10. Debugging the unsaved-settings.py mistake (see §7)

```bash
git commit u "Updated config/setting.py"
```
- **This is broken** — missing the `-m` flag. Without a leading `-`, git parses `u` as a **pathspec** (a file/path to limit the commit to), not an option — so it went looking for a literal file named `u`, not a message flag. No commit was created.

```bash
git diff config/settings.py
```
- Shows **unstaged** changes only. Came back empty — not because nothing changed, but because the change was already staged (see below), and staged changes don't show in a plain `git diff`.

```bash
git diff --staged config/settings.py
```
- `--staged` (alias `--cached`) — shows changes that **are** staged (added) but not yet committed. This is what revealed the actual diff.
- Output got cut short by git's default pager (`less`) — visible as a trailing `:` prompt.

```bash
q
```
- Exits `less`, the pager — returns to the normal shell prompt.

```bash
git --no-pager diff --staged config/settings.py
```
- `--no-pager` — disables piping output through `less`, printing the full diff directly to the terminal instead. Confirmed all four intended settings.py edits were present in the staged change.

```bash
python manage.py check
```
- Re-run against the now-actually-saved file, this time as a genuine confirmation (not the earlier false positive).

```bash
git commit -m "Fix settings.py DRF/static/media wiring not saved before initial commit" -m "INSTALLED_APPS, REST_FRAMEWORK/SPECTACULAR_SETTINGS, TEMPLATES DIRS, and STATICFILES_DIRS/MEDIA_URL/MEDIA_ROOT edits from earlier were left unsaved in the editor and missed the original commit."
git push
```
- A second, honest "fixup" commit on the same branch — no shame in this, it's normal. `git push` alone (no `-u` needed this time) worked because the upstream link was already set in step 9.
- This landed as a second commit on `feature/us-001-project-scaffolding`; **PR #38 picked it up automatically** since GitHub PRs track the branch itself, not a fixed snapshot — no new PR needed.

### 11. Review and merge

```bash
gh pr merge 38 --squash --delete-branch
```
- `38` — the PR number.
- `--squash` — combines every commit in the PR (here: the real scaffolding commit + the fixup commit) into **one clean commit on `master`**. Chosen over a plain merge commit or rebase specifically because the branch had a messy "forgot to save" fixup commit that didn't need to live forever in `master`'s history — squashing keeps `master` at "one commit per story," while the detailed history is still visible on the PR itself if ever needed.
- `--delete-branch` — deletes `feature/us-001-project-scaffolding` both locally and on the remote once the merge succeeds, since its job is done.
- This single command also auto-switched the local repo back to `master` and fast-forwarded it to the merge commit — no separate "sync local" step was needed.

**Verified the outcome:**
```bash
gh issue view 1 --repo nitin-pr/expense-tracker-enterprise --json state,title,closedByPullRequestsReferences
```
- `--json state,title,closedByPullRequestsReferences` — restricts output to just these fields instead of the full issue payload.
- Confirmed: issue #1 (US-001) shows `"state":"CLOSED"`, correctly linked back to PR #38 via the `Closes #1` keyword.

### Concepts learned today (quick recap)

| Concept | One-line takeaway |
|---|---|
| Virtual environment | Isolates a project's dependencies from the global Python install and from other projects |
| `startproject config .` | The trailing `.` avoids Django's default nested-folder scaffolding |
| `__init__.py` | Marks a folder as an importable Python package; not needed for non-code folders like `static/`/`media/` |
| Dev server vs. WSGI server | `runserver` is for local development only; `gunicorn` is what production/Docker should run |
| Docker layer caching | Copying `requirements.txt` and installing before copying the rest of the code lets Docker skip reinstalling deps when only app code changes |
| Feature branches | Isolate in-progress work from `master`; named after the backlog ID for traceability |
| Staged vs. unstaged | `git diff` shows unstaged changes; `git diff --staged` shows what's already been `git add`ed |
| Pathspec vs. option | A shell arg without a leading `-` is treated as a file path by git, not a flag — `git commit u "..."` failed because `u` was read as a path, not `-m`'s missing dash |
| Editor buffer vs. disk | Commands like `manage.py check` read the saved file, not an editor's unsaved changes — always save first |
| Squash merge | Collapses every commit on a PR's branch into one commit on the base branch — keeps history clean when a branch has "fixup" commits |
| `Closes #N` | Special GitHub keyword (in a commit or PR body) that auto-closes an issue when the PR merges to the default branch |

### End-of-day state

- `master` contains the full project skeleton: `config/`, `apps/`, `common/` (with all subpackages), `templates/`, `static/`, `media/`, `tests/`, `manage.py`, `requirements.txt`, `Dockerfile`, `.dockerignore`.
- Issue **#1 (US-001)** closed. PR **#38** merged (squashed) and its branch deleted.
- Sprint 1 remaining: **US-002** (Common Package), **US-003** (Signup/Login), **US-007** (Backend Token Verification), **US-005** (Password Reset).
- Optional follow-up noted but not yet done: enable a GitHub Projects workflow rule ("Item closed → Set Status: Done") so future merges auto-move cards on the board.

---

## Day 2 — 2026-08-06 — Addressing US-001 review feedback + Sprint 1: US-002 Common Package

**Goal for the day:** respond to real Copilot code-review feedback on yesterday's merged PR, then implement and merge US-002 (`common/` package: exceptions, permissions, repositories, services, validators) — including two more rounds of review feedback along the way.

### 1. Resuming a session

```bash
git status && git branch --show-current
source venv/Scripts/activate
pip list
```
- New terminal session = venv is **not** auto-activated; re-activating and re-checking `pip list` each session start is worth doing before touching anything, so a stale/global environment can't silently sneak in.
- Confirmed clean working tree, on `master`, and the exact same package set as yesterday (Django 5.2.17, DRF, drf-spectacular, firebase-admin, gunicorn) — no drift.

### 2. Addressing Copilot's review of PR #38 (already merged)

Copilot's automated review, run after yesterday's merge, flagged three real issues in the already-merged US-001 code:
1. `SECRET_KEY`/`DEBUG` hardcoded in `settings.py` — a real risk (leaks the Django secret key if the repo is ever public; risks running with `DEBUG=True` in production).
2. `drf-spectacular` registered in `INSTALLED_APPS`/`REST_FRAMEWORK` but no actual routes exposed to view the generated schema — dead configuration.
3. `Dockerfile` ran the app as `root` — standard hardening miss.

**Key lesson for this whole section:** since PR #38 had already merged, these fixes went on a **new** branch (`fix/...` prefix, not `feature/...`), not a reopened old one. Convention adopted: `feature/` for new work, `fix/` for bugs/hardening on already-shipped work.

```bash
git checkout master
git pull
git checkout -b fix/us-001-address-review-feedback
```

**Fix 1 — secrets via environment variables:**

```bash
pip install python-decouple
pip freeze > requirements.txt
```
- `python-decouple` lets `settings.py` read config from environment variables / a local `.env` file instead of hardcoding them.

Created `.env` (real values, **never committed**) and `.env.example` (template, **committed**, no real secrets) — but hit a `.gitignore` trap: the existing `.env.*` glob pattern would *also* match and silently exclude `.env.example`. Fixed by adding a negation line right after it:
```
.env
.env.*
!.env.example
```
- `!` in a `.gitignore` line means "un-ignore this, even though a broader pattern above would otherwise match it."

`settings.py` changes:
```python
from decouple import config
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
```
- `SECRET_KEY` has **no default** — missing `.env` → Django crashes loudly on startup instead of silently using an insecure fallback.
- `DEBUG` defaults to **`False`** (secure by default) — `.env` explicitly opts into `True` locally; if the env var is ever missing (e.g. a misconfigured deploy), it fails safe.

**Mistake made:** `python manage.py check` initially failed with `decouple.UndefinedValueError: SECRET_KEY not found`. Diagnosed with:
```bash
ls -la | grep env
```
— which revealed `.env.example` existed but the real `.env` file had never actually been created (only the template was). Fixed with a **heredoc**:
```bash
cat > .env << 'EOF'
SECRET_KEY=<your-generated-secret-key-here>
DEBUG=True
EOF
```
- `cat > file << 'EOF' ... EOF` writes everything between the two `EOF` markers straight into `file` — a clean way to create a short file from the terminal. The quotes around `'EOF'` stop the shell from trying to interpret `&`/`(`/`)` in the secret key as shell syntax.

**Fix 2 — expose drf-spectacular routes**, in `config/urls.py`:
```python
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
```
- `/api/schema/` = raw OpenAPI schema; `/api/docs/` = interactive Swagger UI; `/api/redoc/` = read-only ReDoc reference view. Verified by hitting `/api/docs/` directly (hitting bare `/` still 404s — expected, no route was ever mapped there).

**Fix 3 — Dockerfile non-root user:**
```dockerfile
RUN groupadd --system app && useradd --system --gid app app \
    && chown -R app:app /app
USER app
```
- `--system` = a service account, not a real login user (system UID/GID range).
- `chown -R app:app /app` — everything was copied in as `root` during build, so ownership has to be transferred before `app` can use it.
- `USER app` — every instruction *after* this line runs as `app`, not `root`.

**False alarm caught and cleared:** the Dockerfile briefly appeared in VS Code as `DockerFile` (capital F) instead of `Dockerfile`. Verified with `ls -la Dockerfile* [Dd]ocker*` and `git status` — turned out to be the *same* file matched twice by overlapping glob patterns, not a real duplicate. Worth having checked anyway: a real case mismatch works fine on Windows (case-insensitive filesystem) but silently breaks on Linux CI/deploy targets (case-sensitive).

Committed only the fix-related files — deliberately left `common/repositories/`/`common/services/` (leftover untracked folders from starting US-002 early) out of this commit, since they belong to a different story:
```bash
git add .gitignore Dockerfile config/settings.py config/urls.py requirements.txt .env.example
git commit -m "Address Copilot review feedback on US-001" -m "..."
git push -u origin fix/us-001-address-review-feedback
gh pr create --base master --head fix/us-001-address-review-feedback --title "..." --body "... Refs #1 ..."
```
- `Refs #1` instead of `Closes #1` — issue #1 was already closed by PR #38; this is a follow-up, not the original work.

**Second review round — on this new PR, before it merged.** Two real findings:
1. **`DEBUG = config('DEBUG', default=True, cast=bool)`** — a genuine regression: `default=True` is the *opposite* of the secure-by-default design just described above. Fixed to `default=False`.
2. **Dockerfile `chown -R` timing** — the original fix created the user *after* `COPY . .`, then ran a separate recursive `chown -R` over the whole copied tree. Wasteful (full extra pass over every file) and cache-unfriendly (invalidates on every code change). Fixed by creating the user *before* any `COPY`, and using `COPY --chown=app:app . .` to set ownership *during* the copy instead of as a separate step:
```dockerfile
RUN groupadd --system app && useradd --system --gid app app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=app:app . .
USER app
```

A third point from that same review round (give `SECRET_KEY` a dev-only fallback so a fresh clone doesn't need `.env` set up first) was a genuine **judgment call**, not a bug — decided to keep it strict (no fallback), since `.env.example` already documents what's needed and "fail loudly when misconfigured" was a deliberate choice worth keeping even where the friction it prevents doesn't fully apply yet (solo project).

Fixup committed and pushed to the *same* branch (pre-merge review comments → same branch; post-merge findings → new branch, per the distinction learned above):
```bash
git add Dockerfile config/settings.py
git commit -m "Address second round of Copilot feedback" -m "..."
git push
gh pr merge --squash --delete-branch
```
- Confirmed `common/repositories/`/`common/services/` (untracked) survived every branch switch throughout this whole detour — git never touches untracked files on checkout unless they'd conflict with something being checked out.

### 3. US-002: Common Package

```bash
git checkout -b feature/us-002-common-package
```

Built five pieces of `common/`, each as a small package (`base.py`/specific files + `__init__.py` re-exporting the public names):

**`common/exceptions/`** — one base `AppException` (carries `code`, `http_status`, `message`, optional `details` dict) plus five subclasses (`ValidationError` 400, `AuthenticationError` 401, `PermissionDenied` 403, `NotFoundError` 404, `DatabaseError` 500), and a DRF `EXCEPTION_HANDLER` (`app_exception_handler`) that: (1) turns any `AppException` into a consistent `{code, message, details}` JSON response at its own status code, (2) delegates anything else to DRF's own default handler, (3) falls back to a generic logged 500 for truly unexpected exceptions. Wired into `settings.py` via `REST_FRAMEWORK['EXCEPTION_HANDLER']` (a dotted string path, resolved lazily by DRF at request time).

**`common/permissions/`** — `IsOwner(BasePermission)`, checking `obj.user_id == request.user.id`. Deliberately no defensive `getattr` fallback — if it's ever applied to a model without `user_id`, we want a loud `AttributeError`, not a silently-wrong permission denial.

**`common/repositories/` + `common/services/`** — `BaseRepository(Generic[T])` with real default CRUD methods (`get_by_id`, `list`, `create`, `update`, `delete`) working generically off a `model: Type[T]` class attribute set by each concrete subclass; `BaseService.__init__(self, repository)` takes its repository via constructor injection. **Design note worth remembering:** the LLD showed `BaseRepository` as an `ABC` with `...` method bodies — that notation meant "elided for brevity" in a design doc, not "literally abstract." Making it a real `ABC` would force every concrete repository to reimplement basic CRUD, defeating the point.

**`common/validators/`** — `validate_positive_amount`, `validate_not_future_date`, `validate_file_size_and_type`, each raising **our own** `common.exceptions.ValidationError` specifically — not Django's or DRF's near-identically-named classes — so every error in the system flows through the same handler and comes out the same shape.

**14 unit tests** across `tests/common/` (exceptions: 3, permissions: 2, validators: 9), using `SimpleNamespace` to build lightweight stand-in objects (a request with a `.user.id`, a file with `.content_type`/`.size`) instead of needing real Django models — useful specifically because these pieces only touch a couple of attributes each.

```bash
python manage.py test tests.common
# Ran 14 tests ... OK
```

### 4. Debugging moments during the build

- **`print()` not showing up in a passing test.** First hypothesis (wrong, corrected once the actual code was shown): "an exception stopped execution before the print ran." Actually the prints were *before* the failing call. Real cause turned out to be simpler — the terminal output being compared was from a run *before* the print statements were even added to the file. Once re-run with them in place and the underlying bug fixed, they still didn't show on a **passing** test specifically — consistent with `unittest`/Django test-runner output buffering (captured output is discarded for passing tests, shown for failing ones), though this wasn't fully pinned down with certainty. Practical takeaway: use `logging` instead of `print()` for anything you need visible in test output regardless of pass/fail.
- **`IsOwner` typo:** `return obj.user_id == request.user_id` instead of `request.user.id` — missing the `.user` in the middle. Caught by the test's `AttributeError` traceback, not by reading the code first.
- **`common/services/base.py` self-import bug** (caught by Copilot on the US-002 PR): the file correctly defined `BaseService`, but also had a leftover `from .base import BaseRepository` + `__all__ = ["BaseRepository"]` block copy-pasted in from `common/repositories/__init__.py` — since `.base` inside `common/services/base.py` refers to itself, this was importing from a module still mid-execution. Fixed by deleting the stray block.
- **`common/services/__init__.py` found completely empty** while diagnosing the above (not something Copilot even caught) — meant `from common.services import BaseService` silently didn't work at all. Fixed with the same `from .base import BaseService` / `__all__` pattern every other `common/` subpackage uses.
- **Misleading validator message** (Copilot): file-type error said "Allowed: image or PDF" while only `jpeg`/`png`/`pdf` were actually accepted — technically true-sounding but implies any image format works. Fixed to list `ALLOWED_CONTENT_TYPES` directly so the message can never drift from the actual allowed set again.
- **Exception handler logging every `AppException` at `ERROR`** (Copilot) — contradicted our *own* HLD, which specifies `WARNING` for expected/recoverable issues like validation rejections and `ERROR` only for genuinely unhandled exceptions. Fixed: `level = logging.WARNING if exc.http_status < 500 else logging.ERROR`.
- **Missing tests for `BaseRepository`/`BaseService`** (Copilot) — judgment call, not a clear bug: testing them meaningfully needs a real migrated Django model, which doesn't exist yet (no `Category`/`Expense` until later stories). Decided to leave as-is rather than build throwaway test-only model infrastructure just to close the gap early.

### 5. Final manual review pass, before merging US-002

Before merging, did one more full pass independent of Copilot: read every changed file in the branch (`git diff master...feature/us-002-common-package --stat` to enumerate them, then each file in full), reran `manage.py check` + the full test suite with `-v 2` (verbose, one line per test) + `git status` + `git fetch` and diffed local vs. remote to confirm the branch was fully pushed before giving a "safe to merge" verdict — not just trusting that earlier fixes were correct without re-verifying end to end.

**Follow-up review, after merging:** asked specifically to re-examine `common/repositories/base.py` alone. Found one real, if currently low-risk, gap not caught by any prior review: `update()` uses plain `setattr(instance, attr, value)` for every keyword passed in — a typo'd field name (e.g. `amonut` instead of `amount`) doesn't raise anything; it just creates a throwaway Python attribute that `instance.save()` silently ignores, since Django only persists real model fields. This directly contradicts the "fail loudly" convention the rest of the file already follows correctly (e.g. `model` having no default). Decided to defer the fix until a real repository exists to verify a proper check against (a naive `hasattr` check isn't fully precise either, since it'd also pass for non-field properties).

### 6. Making the GitHub repo + Projects board public

Before flipping visibility, checked for anything that shouldn't go public — and found something real: the actual `SECRET_KEY` value was sitting in `Notes.md`'s own committed history, quoted verbatim as part of a documented example command from earlier. Harmless while private; would become visible to anyone the moment the repo went public.

```bash
git grep -n "django-insecure" -- . ':!Notes.md'
```
- Confirmed the value existed nowhere else in tracked files — only in `Notes.md`'s example.

Fix chosen: **rotate the key locally** (the real fix — generated a fresh one via `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`, updated `.env`, which is untracked so this alone doesn't touch git) **and redact the documented value going forward** in `Notes.md`, rather than rewriting git history to fully scrub it. Reasoning: the exposed value was about to become a *dead* key (no longer in use anywhere once rotated), so a destructive history rewrite (every commit hash changes, requires a force-push) wasn't worth it just to hide a value that no longer protects anything.

```bash
git ls-files | grep -i "^\.env$"   # confirms .env itself was never tracked, exit code 1 = no match
```

Then flipped both visibility settings — worth knowing these are **two separate, independent settings**, not one:
```bash
gh repo edit nitin-pr/expense-tracker-enterprise --visibility public --accept-visibility-change-consequences
gh project edit 1 --owner nitin-pr --visibility PUBLIC --format json -q '.public'
```
- `gh repo edit` requires that extra `--accept-visibility-change-consequences` flag specifically for public changes — a deliberate friction point, since it's a consequential, hard-to-fully-reverse action (anything public can get cloned/cached/indexed before you'd ever flip it back).
- `gh project edit` is the *separate* command for the Projects v2 board's own visibility — confirmed via `gh project edit --help` that `--visibility {PUBLIC|PRIVATE}` exists there too.

**Real-world hiccup, not a mistake:** mid-push, hit a genuine network outage — `git push` failed with `Could not resolve host: github.com`. Diagnosed it wasn't git-specific before assuming anything:
```bash
nslookup github.com
ping -n 2 github.com
```
Both timed out against the local router — confirming it was a local DNS/network problem, not a GitHub-side or git-specific issue. Waited, retried `git push` once connectivity returned, succeeded immediately. Lesson: when a command fails with a network-shaped error, verify with a tool *other* than the one that failed (here, `nslookup`/`ping` instead of just retrying `git push` blindly) before concluding anything about the root cause.

### 7. US-003: Email/Password Signup & Login — Firebase console + frontend build

**Firebase console setup** (browser, not terminal): created a new Firebase project, skipped Google Analytics (not needed for an auth backend), registered a **Web App** to get a `firebaseConfig` object (`apiKey`, `authDomain`, `projectId`, etc.) — confirmed these values are **not secret**, they're meant to be visible in frontend JS; Firebase's actual security boundary is enforced server-side, not by hiding them. Then enabled the **Email/Password** sign-in provider under Authentication → Sign-in method.

Built the frontend using Firebase's **modular SDK loaded directly from their CDN as ES modules** — no npm/webpack build step, fitting this project's plain HTML/Bootstrap/JS stack:
```javascript
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";
```

Structure built: `templates/base.html` (shared layout using Django's `{% block %}` template inheritance — child templates only define what's actually different), `templates/accounts/signup.html`/`login.html` (Bootstrap 5 forms), and `static/js/firebase-config.js`/`signup.js`/`login.js`.

Core Firebase Auth calls used: `createUserWithEmailAndPassword(auth, email, password)` for signup, `signInWithEmailAndPassword(auth, email, password)` for login, and `userCredential.user.getIdToken()` on either to retrieve the signed JWT identifying that user — the token US-007 will later verify server-side. **Django never sees the password** — the entire signup/login exchange happens directly between the browser and Firebase, satisfying that acceptance criterion by construction, not by any special Django-side handling.

`TemplateView.as_view(template_name=...)` used in `config/urls.py` to serve these pages — Django's simplest built-in generic view, appropriate since all real logic is client-side JS talking to Firebase, not server-side business logic.

**Scope decision made explicitly, not by accident:** noticed signup doesn't verify the email address is actually owned by the signer. Confirmed this is deliberate — **US-004 (Email Verification)** is its own separate, lower-priority (`Should`) backlog story scheduled for Sprint 6, not bundled into US-003 (`Must`, Sprint 1). Considered pulling it forward since we were already in `signup.js`, decided against it — stuck to the sprint plan rather than scope-creeping ad hoc.

Tested against the real, live Firebase project: signed up a test user, confirmed it appeared in the Firebase console's Authentication → Users tab, confirmed a token was returned, then logged in with the same credentials.

### 8. Copilot review on US-003 — seven findings, triaged

1. **ID token logged to console** — real risk (bearer credential, could leak via shared logs/screen recordings/extensions). Removed.
2. **Raw Firebase `error.message` shown to users** (e.g. `"Firebase: Error (auth/invalid-credential)."`) — ties directly to US-003's own "clear error message" AC. Fixed with a shared `static/js/auth-errors.js` mapping `error.code` → friendly text, imported by both `signup.js` and `login.js` (DRY — same reasoning as `BaseRepository`/`BaseService`). Notable detail: modern Firebase deliberately returns the *same* `auth/invalid-credential` code for both "wrong password" and "no such account" during login, to prevent **user enumeration** (an attacker probing which emails have accounts) — kept that same generic message for both rather than trying to be more specific.
3. **Token textarea had no accessible label** — fixed by replacing a plain `<p>` with a proper `<label for="token-text">`.
4. **Token only displayed, never persisted** — real gap vs. the AC's "attached as Authorization: Bearer on subsequent API calls." Fixed with `sessionStorage.setItem("idToken", idToken)`. Chose `sessionStorage` over `localStorage` deliberately: it clears when the tab/browser closes, shortening how long a bearer token sits in browser storage — reasonable for something Firebase itself also expires after an hour regardless.
5. **Hardcoded `firebaseConfig` in committed JS** — genuine judgment call (unlike `SECRET_KEY`, these values aren't actually secret, so this was about environment-separation hygiene, not confidentiality). Decided **to** build the fix this time (opposite call from the earlier `SECRET_KEY`-dev-fallback decision) — moved the six config values into `.env`, added a Django **context processor** (`common/context_processors.py`) that runs automatically for every template render, and used Django's `json_script` template filter to safely emit them as JSON:
   ```html
   {{ firebase_config|json_script:"firebase-config-data" }}
   ```
   Worth remembering *why* `json_script` specifically, not just `{{ firebase_config }}` directly: Django would render Python's dict `repr()` — single-quoted, `True`/`None` instead of valid JS syntax — which is a real bug, not a style nitpick. `json_script` renders a properly-escaped `<script type="application/json">` data container instead, which JS then reads with `JSON.parse(...)`.
6. **Missing `name`/`autocomplete` attributes** on email/password inputs — cheap accessibility/UX fix, enables password-manager autofill (`autocomplete="new-password"` on signup vs. `"current-password"` on login — browsers treat these differently).
7. **Bootstrap CDN missing Subresource Integrity (SRI)** — a compromised CDN could otherwise silently serve tampered CSS/JS. **Did not guess the hash** — a wrong SRI hash doesn't degrade gracefully, it just fails the resource load entirely with a cryptic browser error. Used `WebFetch` against Bootstrap's own official docs page to get verified hashes, which turned out to be for version 5.3.8 (current) rather than the originally-pinned 5.3.3 — since hashes are tied to exact file bytes, bumped the version to match the verified hash rather than trying to find a 5.3.3-specific one.

### 9. US-007 kickoff (started, not finished today)

US-007 is what makes the tokens from US-003 actually *mean* something server-side — Django needs to verify a token is genuine, then resolve/create the matching local `User`. This needs a **service account key** from Firebase — a different, genuinely secret credential from the frontend `firebaseConfig` (this one grants admin-level backend access to the Firebase project, never goes in frontend JS or gets committed). Guided to Firebase console → Project Settings → Service Accounts → "Generate new private key." Session ended here — key not yet generated/wired in; pick this up next time before writing any of the `accounts` app, `User` model, or `FirebaseAuthentication` DRF class.

### Concepts learned today (quick recap)

| Concept | One-line takeaway |
|---|---|
| `fix/` vs `feature/` branches | `feature/` for new work, `fix/` for bugs/hardening on already-shipped work |
| Pre- vs. post-merge review feedback | Comments before merge → fixup commit on the *same* branch/PR; comments after merge → a *new* branch/PR |
| `python-decouple` | Reads settings from environment variables/`.env` instead of hardcoding them in `settings.py` |
| Secure-by-default | `DEBUG` should default to `False`; `SECRET_KEY` should have no default at all — fail loudly rather than silently insecure |
| `.gitignore` negation (`!pattern`) | Un-ignores a file that a broader pattern above it would otherwise exclude |
| Heredoc (`cat > file << 'EOF'`) | Quick way to write a short file's contents directly from the shell |
| `COPY --chown=` | Sets file ownership during a Docker copy instead of a separate, slower, cache-unfriendly `RUN chown -R` afterward |
| ABC vs. concrete generic base class | A design doc's `...` method body means "elided," not necessarily "must be abstract" — read intent, not just notation |
| Constructor injection vs. class attribute | Inject via constructor only what genuinely needs to vary at runtime (a service's repository); fix what doesn't vary as a class attribute (a repository's model) |
| Repository vs. Service (plain English) | Repository = *how* to get/store data. Service = *what* should happen, and whether/when the data gets involved |
| `SimpleNamespace` for tests | Quick throwaway object with arbitrary attributes — useful for testing logic that only touches a couple of fields, without needing a real model |
| Exception class name collisions | Django, DRF, and our own code all have a `ValidationError` — imports must be checked carefully, wrong one silently breaks `.details`/`.code` access |
| Test output buffering | Passing tests may not show `print()` output the way failing ones do; `logging` is the more reliable choice for anything you need to see regardless of outcome |
| Silent `setattr` risk | Setting arbitrary attributes by name (`setattr(obj, attr, value)`) doesn't validate the field exists — a typo fails silently instead of raising |
| Committed secrets live forever in history | Redacting a file's *current* content doesn't remove a value from earlier commits — only a history rewrite does, which has its own real costs |
| Repo visibility vs. Projects board visibility | Two separate `gh` commands/settings (`gh repo edit --visibility`, `gh project edit --visibility`) — flipping one doesn't touch the other |
| Diagnosing network failures | When a command fails with a network-shaped error, check with an independent tool (`nslookup`/`ping`) before assuming it's the original tool's fault |
| Firebase frontend config vs. service account | `firebaseConfig` (apiKey, etc.) is meant to be public in frontend JS; a service account key is genuinely secret backend-only admin access — very different risk levels despite both being "Firebase credentials" |
| Context processor | A function Django runs for *every* template render, merging its return value into that template's context automatically — avoids passing the same data manually from every view |
| `json_script` template filter | Safely serializes a Python value to JSON inside a non-executing `<script type="application/json">` tag; `{{ value }}` alone would render Python's `repr()`, not valid JSON/JS |
| SRI (`integrity`/`crossorigin`) | Browser verifies a downloaded CDN file's hash before running it — but the hash is tied to exact file bytes, so it must match the *exact* version being loaded |
| `sessionStorage` vs `localStorage` | `sessionStorage` clears when the tab/browser closes — shorter exposure window, reasonable default for something like an auth token |
| User enumeration | Deliberately returning the *same* error for "wrong password" and "no such account" prevents an attacker from using error differences to discover which emails have accounts |

### End-of-day state

- `master` has: US-001's review-feedback fixes, the full `common/` package (US-002), and now the complete US-003 signup/login flow (env-injected Firebase config, friendly errors, sessionStorage token persistence, SRI-hardened Bootstrap CDN, accessibility fixes) — all reviewed twice (Copilot + prior manual pass) and merged.
- The **GitHub repo** and **Projects board** are both now public; the `SECRET_KEY` exposed in `Notes.md`'s history was rotated and the documented example redacted before doing so.
- Issues **#1** (follow-up merged), **#2**, **#3** all closed via their respective PRs.
- One still-open known gap from Day 2: `BaseRepository.update()`'s silent-typo risk — still deferred.
- **US-007 (Backend Token Verification) started but not complete** — stopped right after being pointed to generate a Firebase service account key; nothing in the `accounts` app has been built yet.
- Sprint 1 remaining: **US-007** (in progress), **US-005** (Password Reset).

---

## Day 3 — 2026-09-29 — Finishing Sprint 1 + all of Sprint 2 (Categories & Expense CRUD)

**Context shift for this session, worth naming explicitly:** ~7 weeks passed since Day 2. Picked back up with "complete Sprint 1 and Sprint 2" and Auto Mode active — a genuinely different working mode from Days 1-2's "I guide, you type every line." Here, execution was direct: writing files, running commands, and committing/merging PRs without pausing at each step, while still keeping the same engineering discipline (branch-per-story, tests before merge, real verification over assumption) built up over the first two days. The learning value shifts accordingly — less "typing muscle memory," more "here's what a real multi-hour push through a backlog actually looks like, bugs included."

### 1. The environment had quietly broken during the gap

Resuming hit an immediate wall: `python manage.py check` failed with a garbled "No Python at..." error.

```bash
git check-ignore -v firebase-service-account.json   # sanity-checked secrets survived the gap first
where python
```
- `where python` no longer listed Python 3.11 at all — only 3.14. Checked directly:
```bash
ls -la "C:\Users\user\...\Python311\python.exe"   # No such file or directory
```
Python 3.11 (what the venv was built against) had been removed from the machine entirely sometime in the gap. A venv doesn't bundle its own interpreter — it references the base install — so this wasn't fixable, only rebuildable.

```bash
py -0                       # list all Python versions the launcher knows about - only 3.14 available
rm -rf venv
py -3.14 -m venv venv
source venv/Scripts/activate
python -m pip install --upgrade pip -q   # `pip install --upgrade pip` alone fails on Windows -
                                          # pip can't overwrite its own running executable;
                                          # `python -m pip` sidesteps that
pip install -r requirements.txt
```
Rather than assume Django 5.2 either does or doesn't support Python 3.14 (a version that postdates this project's original planning), verified practically: full install succeeded with native `cp314` wheels for every package with C extensions (`grpcio`, `google-crc32c`, `rpds-py`), and `manage.py check` + the full existing test suite (14 tests) passed clean. Real compatibility questions get answered by running the thing, not by recalling documentation that might be stale.

### 2. Real bugs in already-written (but never tested) US-007 code

The `apps/accounts/` code from Day 2's final session was still sitting uncommitted, never actually exercised end to end. Reading it fresh surfaced three real bugs before writing anything new:
1. **`authentication.py`**: `self.user_repository = UserRepository()` in `__init__`, but `authenticate()` called `self.user_repo....` — an attribute name that didn't exist. Would have raised `AttributeError` the moment a real token was verified.
2. **`WhoAmIView`** (the protected test endpoint discussed at length on Day 2) had never actually been written — `views.py` was still Django's default stub.
3. **`config/urls.py`** never got the `include('apps.accounts.urls')` wiring discussed.

None of these were caught earlier because the session ended right before the "test it live in a browser" step. Lesson already learned on Day 1 (unsaved files giving false confidence) generalized: **code that's never actually executed carries no real confidence, no matter how carefully it was reasoned through when written.**

### 3. `on_delete=RESTRICT` vs `on_delete=PROTECT` — different exceptions, verified not guessed

`DATABASE_DESIGN.md` specifies `ON DELETE RESTRICT` for `expenses.category_id`. Django has *two* similar-but-distinct options here. Rather than assume `RESTRICT` behaves like the more commonly-seen `PROTECT` (which raises `ProtectedError`), checked directly:
```python
from django.db.models.deletion import RestrictedError   # confirmed: RESTRICT raises this, not ProtectedError
```
This mattered concretely: `CategoryService.delete_category` (written back on Day 2, before `Expense` existed to reference a category) was catching `ProtectedError` — dead code that would have silently let a real `RestrictedError` become an unhandled 500 the first time it actually mattered. Fixed once `Expense.category` was actually built with `on_delete=models.RESTRICT`, and proved with a real `Expense` row referencing a real `Category` (US-013's actual acceptance criterion, finally testable once US-014 existed).

### 4. `is_authenticated` — caught only because a full-pipeline test existed, not just unit tests

Writing `WhoAmIView`'s tests, the mocked-`AuthProvider` unit tests (matching US-007's literal AC wording) all passed — but a separate test hitting the *real* URL through DRF's `APIClient` failed:
```
AttributeError: 'User' object has no attribute 'is_authenticated'
```
DRF's `IsAuthenticated` permission checks `request.user.is_authenticated` — a convention from Django's built-in `AbstractBaseUser` that this project's plain `User` model (intentionally not inheriting from it, since Firebase owns identity) doesn't have. The isolated `authenticate()` unit tests never touched DRF's actual permission-checking code path, so they couldn't catch this. Fixed with a simple `@property` returning `True` (any resolved `User` instance is authenticated by definition — `FirebaseAuthentication` never returns one otherwise). **Concrete argument for writing both kinds of test**: narrow unit tests prove your own logic is correct in isolation; full-pipeline tests prove your logic actually *connects* to the framework correctly. Neither alone is sufficient.

### 5. Two different "who owns this" fields needed two different permission classes

`common.permissions.IsOwner` (built Day 2) hardcodes `obj.user_id` — fine for `Expense`/`Income`/`Budget` (all use a `user` FK per the DB design), wrong for `Category` (deliberately uses `created_by` instead — a more precise name). Rather than bend the data model to fit an existing permission class, or make `IsOwner` needlessly generic for a problem that only affects one model, wrote a small `IsCategoryOwner` local to `apps/categories/`, checking `obj.created_by_id`. A `None` `created_by_id` (default categories) never equals a real user id, which for free satisfies "default categories can't be edited/deleted by anyone" with no special-casing.

### 6. 404 vs 403 genuinely differs by model, and the reasoning matters

`Category` and `Expense` both needed "you can only touch your own records" enforcement, but landed on opposite HTTP semantics:
- **Category**: every category (defaults + everyone's custom ones) is visible via the list endpoint. No "existence leakage" risk in confirming a specific ID exists but isn't yours — so `CategoryDetailView` uses `IsCategoryOwner` normally, producing a real **403** for "exists, not yours."
- **Expense**: never visible cross-user at all (no shared list). Revealing "this ID exists, just not to you" via 403 would leak information an attacker could use to enumerate valid IDs. So `ExpenseDetailView` deliberately skips DRF's permission-class mechanism entirely and folds "doesn't exist" and "exists but isn't mine" into the identical **404** path, by design, in `get_object()` itself.

Same underlying concern ("don't leak what an attacker can't already see") as the login-error-message reasoning from Day 2 — reapplied at the HTTP-status-code layer instead of the error-message layer.

### 7. A real gap in the original sprint planning, resolved with a build-order fix, not a doc rewrite

`BACKLOG.md` lists US-013 (protect categories in use) as depending only on US-011. But the actual protection mechanism is the FK's `on_delete=RESTRICT`, which has to live *on the Expense model* — which doesn't exist until US-014. US-013 as written is mechanically untestable before US-014 exists. Resolved by building in dependency-correct order (US-010 → US-011 → US-014 → US-015 → US-013) rather than the nominal listed order, flagged explicitly rather than silently reordered. Sometimes a plan's stated dependencies are incomplete, and the fix is to notice and route around it, not to treat the doc as ground truth over the actual system.

### 8. Self-review caught a factual error in a PR description before merge

Wrote "Full test suite (99 tests total)" in a PR body from memory/estimate rather than checking. Before merging, re-ran the suite to verify — actual count was 72, not 99 — and corrected the PR description (`gh pr edit`) before merging. Small thing, but the standard applied to the user's own claims in earlier sessions ("verify, don't just assert") applies the same way to summaries written about one's own work.

### 9. A genuine test-coverage gap found during final review, not by the tests themselves

Final review pass (reading every changed file fresh, same rigor as the Day 2 "green flag" review) noticed: `ExpenseService.update_expense` validates category-*ownership* on a category change, but no test exercised a *successful* category change reaching all the way through to `BaseRepository.update()`'s field-name check (`instance._meta.get_fields()`) - the change could work by construction and still have never been proven to. Verified the FK's `.name` is `"category"` (not `"category_id"`) via direct inspection, then wrote the missing test. The lesson from Day 2 held again: a passing test suite proves what's tested, not what's true — worth actively hunting for what *isn't* covered, not just trusting green output.

### 10. Loose ends, left visible rather than silently ignored

- **GitHub Projects board status desync**: issues #10 and #11 (closed by one PR that closed both at once) didn't auto-flip to "Done" on the board the way single-issue-closing PRs did — fixed manually via `gh project item-edit`, but the underlying cause (multi-issue-closing PRs and board automation) wasn't root-caused.
- **Docker build not verified this session**: Docker Desktop wasn't running in this environment and couldn't be started without GUI access. `requirements.txt` didn't change and all new code is plain Python copied in via the existing `COPY . .`, so risk is low, but this is stated as an assumption, not a verified fact — worth an actual `docker build` next session before treating it as proven.

### Concepts learned today (quick recap)

| Concept | One-line takeaway |
|---|---|
| A venv references, not bundles, its base interpreter | Removing the Python version a venv was built against breaks it permanently — rebuild, don't try to repair |
| `python -m pip install --upgrade pip` | The `pip` executable can't overwrite itself while running on Windows; invoking it via `python -m pip` avoids the self-lock |
| Verify version compatibility by running, not recalling | Especially for anything that postdates a project's original planning - actual install + test run beats memory |
| Code that's never executed carries no real confidence | Reasoning carefully about code while writing it doesn't substitute for actually running it, no matter how much time passed in between |
| `on_delete=RESTRICT` vs `on_delete=PROTECT` | Similar-sounding, different exception classes (`RestrictedError` vs `ProtectedError`) - verify library internals directly rather than assume |
| Unit tests vs full-pipeline tests | Isolated unit tests prove your logic; full-pipeline tests prove your logic actually connects to the framework - `is_authenticated` was invisible to the former, caught immediately by the latter |
| One permission class doesn't always fit every model | A hardcoded field name (`user_id`) in a shared permission class breaks for a model that deliberately names its ownership field differently (`created_by`) - don't force the data model to match the tool |
| 404 vs 403 depends on what's otherwise visible | The right status code for "not yours" depends on whether the resource's existence is already knowable through some other path (Category's shared list) or not (Expense's total privacy) |
| A backlog's stated dependencies can be incomplete | US-013's real dependency on US-014 wasn't written down anywhere - noticing and routing around a planning gap is part of the job, not a sign the plan should be trusted blindly |
| Verify your own summaries before publishing them | A wrong number in a PR description is still wrong even when self-authored under time pressure - re-check, don't estimate |
| Green tests prove coverage, not completeness | Actively look for what a passing suite *doesn't* exercise, especially for code paths that "should obviously work" |

### End-of-day state

- **Sprint 1 complete**: US-001, 002, 003, 005, 007 all merged. Issue tracker and Projects board both accurate.
- **Sprint 2 complete**: US-010, 011, 013, 014, 015 all merged - full Category (defaults + custom, with delete protection) and Expense (create + detail get/update/delete) functionality, backed by 76 passing tests.
- `common/constants/` gained its first real content (`PaymentMethod`), deferred since Day 2 until Expense actually needed it.
- Local dev environment rebuilt on Python 3.14 (3.11 no longer available on this machine) - Django 5.2 confirmed compatible.
- Two open items, stated honestly rather than assumed fine: Docker build not re-verified this session; GitHub Projects board automation has a rough edge with multi-issue-closing PRs.
- Sprint 3 (`US-016` Search, `US-017` Filter, `US-018` Sort & Paginate Expenses, `US-020` Record Income, `US-021` Income CRUD) is next per `SPRINT_PLAN.md`.
