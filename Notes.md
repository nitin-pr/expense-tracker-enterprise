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

## Day 2 — _(next session)_

_To be filled in._
