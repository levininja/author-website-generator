# Author Website Generator — Feature List

Related documents: [README](README.md) · [Product spec](SPEC.md) · [Product decisions](DECISIONS.md) · [Provisioning pipeline](PIPELINE.md)

## ID Tracker

- Latest feature ID: `F038`
- Latest task ID: `T005`
- Latest research ID: `R001`

Four lists: **Doing** (active work), **Milestone 1** (ordered by priority), **Backlog** (unordered), and **Done**.

ID prefixes: `F` = feature, `T` = task, `R` = research task.

---

## Doing

---




---

## Milestone 1 Epic — Generate and Preview a Standard Author Website

Milestone 1 is v1 of the product for standard, non-ecommerce author websites: a
user completes the onboarding form, clicks Generate, AWG enqueues a generation
job and shows a progress screen, and upon completion the user can view the
generated WordPress site running locally. Locally, only one generated site is
ever live at a time: each new generation deletes the previous one and hosts the
new one on a local PHP server on its own port, separate from the Django app's
port. Generation runs in a background worker (not in the HTTP request thread)
so the Django app stays responsive during the WP-CLI subprocess calls.

Milestone 1 stops at generation, local preview, and a first manual production
deployment for informal user testing. It does not include payments, billing,
website maintenance, admin pages, automated deployment, ecommerce features,
shopping carts, or payment processing.

**Milestone 1 is done when:**
1. A user can complete the onboarding form, click Generate, and see a working WordPress site running locally with all submitted data visible and correctly placed
2. The generated site is presentable enough for informal user testing — no broken layouts, missing fields, or obviously unfinished UI
3. One generated site has been manually deployed to a live URL following a documented runbook
---


### T003 — Break the onboarding React app into separate files

**Type:** Task
**As** a developer, I want `frontend/onboarding/App.jsx` divided into smaller,
focused files so that the onboarding frontend is easier to understand and
maintain.

The single 1,800+ line `App.jsx` file makes it hard to reason about individual
steps and means agents editing the frontend will frequently step on each other.
Decompose into per-step and per-concern component files before the next round
of frontend feature work (F028+).

---

### T004 — Harden the subprocess runner with stderr capture, timeouts, and logging

**Type:** Task
**As** a developer, when a WP-CLI command fails during generation I get a clear, actionable error instead of a silent exception, so I can debug failures without guesswork.

The current `default_runner` and `default_capture_runner` in `generation/subprocess_runner.py` call `subprocess.run(..., check=True, capture_output=True)`. When a command fails, `CalledProcessError` is raised but its `stdout` and `stderr` are never surfaced — they're silently swallowed by callers. There are also no timeouts, so a hung WP-CLI call (e.g. `wp core download` on a slow connection) will block the worker indefinitely.

- Capture and attach `stderr` (and `stdout`) to any raised exception or log entry so generation failures produce readable error messages
- Add a configurable `timeout` parameter (default 120 seconds for most commands; `wp core download` may warrant longer) — raise a clear `GenerationTimeoutError` on expiry
- Log every subprocess invocation at DEBUG level (command + args) and every failure at ERROR level (command, exit code, stdout, stderr)
- No retry logic required at this layer — callers can retry if needed
- Tests cover: successful run, non-zero exit code with stderr captured, timeout expiry

---

### F028 — Install and configure Divi with baseline settings

**Type:** Feature
**As** a developer, I can have Divi installed and configured with sensible defaults on every generated site so pages render correctly and on-brand.

- Depends on F026
- Install and activate the Divi theme on the generated site
- Set Divi's global font settings
- Set Divi's global color palette from the author's submitted primary/secondary brand colors
- Set the site logo and favicon from onboarding assets where available
- Set WordPress permalinks to a pretty (non-default) structure
- Tests or validation cover installation and global font/color/logo/favicon/permalink configuration, including behavior when optional branding assets are missing

---

### F029 — Generate header/nav and footer on site generation

**Type:** Feature
**As** an end user, my generated site has a working header/navigation and footer instead of Divi's defaults.

- Depends on F028
- Generate a header with navigation linking to the generated pages (Home, About, Books, Contact)
- Generate a footer that includes the author's submitted social links as icons/links
- Tests cover nav-link generation, footer social-link rendering, and behavior when optional social links are missing

---

### F030 — Wire generation end-to-end with a background job queue

**Type:** Feature
**As** a developer, I can trigger website generation from the onboarding review screen and have it run in a background worker so the Django app stays responsive during the multi-minute WP-CLI subprocess calls, and as an end user I can see generation progress and be shown the result when it completes.

**Architecture decision required before implementation begins:** choose and configure the background job queue library. Leading candidates are Django-Q2, Celery + Redis, and Huey. See architecture notes in DECISIONS.md once the decision is recorded.

- Generation stays inside the existing Django app (no separate app or port); the onboarding app's review/confirmation page triggers generation
- `POST /generate` validates the author ID, enqueues a generation job, and immediately returns a job ID — it does not block until generation finishes
- A `GenerationJob` model (or equivalent queue-native record) tracks job state: `pending`, `running`, `complete`, `failed`
- The background worker runs the full generation pipeline (F025–F029 steps) for the submitted author data
- `GET /generate/<job_id>/status` returns current job state and, on completion, the preview URL; on failure, a human-readable error message
- The result/error screen (F007) polls this status endpoint and updates the UI without a page reload
- Generation supports standard, non-ecommerce author websites only
- The generated result is self-contained: it does not depend on a production WordPress, Cloudways, Cloudflare, DNS, SSL, or hosting operation
- Generation failures return a safe, human-readable error; no partial site files or records persist after a failed job
- Tests cover: job enqueue on `POST /generate`, status endpoint for each job state, complete generation with all onboarding fields, optional-field handling, invalid author ID rejection, and generation failure cleanup (no partial site record created)

---

### F020 — Host the single generated WordPress site for local preview

**Type:** Feature
**As** an end user, I can view the website generated from my submission running as a real local WordPress site.

- Only one generated site is hosted at a time; generating a new site deletes the previous one first, then writes and hosts the new one in its place
- The generated site lives in its own dedicated folder and is served by a local PHP server on its own port, separate from the Django app's port
- A successful generation job (F030) surfaces a link to the locally hosted site
- Generation is atomic: the previous site is only removed once the new site's files are fully written, and the new site is only hosted once fully written
- Update the README quickstart at the same time this ships: add quickstart steps for spinning up the PHP server alongside the Django dev server and background worker
- Tests cover file replacement (old site removed, new site written), atomic write/replace behavior, and successful local serving

---

### F007 — Get a clear result — site URL on success, specific error on failure

**Type:** Feature
**As** an end user, when generation completes I can open the generated website, and if it fails I see a human-readable error message.

- Lives in the generation result screen within the existing AWG app (not a separate app)
- The UI polls `GET /generate/<job_id>/status` (F030) and updates without a page reload
- On success: display a link to the locally hosted generated site (F020)
- On failure: show a specific, actionable error plus a dismiss button
- No internal exception details or stack traces are exposed to the user
- Error display persists until the user dismisses it via X or resubmits

---

### F034 — Polish the generated site for informal user testing

**Type:** Feature
**As** the product owner, the generated site looks good enough to put in front of author friends for informal user testing — no broken layouts, no missing data, no obvious rough edges that would distract from the feedback I'm trying to get.

- Review the full generated site end-to-end: Home, About, Books, per-book pages, header/nav, footer
- All onboarding data must be visible and correctly placed — no missing fields, broken images, or placeholder copy
- Brand colors are applied visibly
- Navigation links work; social links render with icons
- Bar is not pixel-perfection — it's "an author friend can use this without being distracted by something clearly broken"
- This ticket is a human review + fix pass, not automated test coverage
- Depends on F029 (all generation features complete)

---

### F035 — First local-to-production deployment

**Type:** Task
**As** the product owner, I can deploy a generated site to production hosting so that Milestone 1 ends with a live, accessible author website and I can validate the full end-to-end pipeline.

- Deploy one generated site to production manually — no automation required
- Document every step taken (hosting setup, file transfer, WP config, DNS, SSL) in enough detail that a developer could follow them later to build an automation script
- Deliverable: a live site at a real URL, plus a deployment runbook committed to the repo
- A follow-on backlog ticket (F036) will turn that runbook into an automation script
- Scope is intentionally narrow: one site, done by hand, documented

---

## Backlog

---

The backlog contains work that is useful after Milestone 1 but is not required
to generate and preview a standard, non-ecommerce website inside AWG.

### T005 — Migrate from SQLite to PostgreSQL

**Type:** Task
**As** a developer, AWG uses PostgreSQL in production so the database can handle concurrent writes from multiple HTTP workers and a background job worker without locking.

SQLite's single-writer model means simultaneous requests (Django HTTP server + background worker + any future concurrency) can produce write contention. PostgreSQL is the standard Django production database and removes this ceiling before real users arrive.

- Replace the `sqlite3` database engine with `psycopg2` / PostgreSQL in production settings
- Keep SQLite as the local development default (acceptable for single-developer, single-worker local use)
- Add `DATABASE_URL` env var support (e.g. via `dj-database-url`) so production config is a single env var
- Document the production database setup in README and `.env.example`
- Run and verify all existing migrations against PostgreSQL before merging
- This should be completed before or alongside F035 (first production deployment)

---

### F037 — Give genre catalog entries stable integer IDs for internal references

**Type:** Feature
**As** a developer, genre categories, genres, and subgenres are identified by stable integer IDs (not by name) in all internal references — validation, persistence, and API responses — so renaming a genre does not silently break author records or require a data migration of every related table.

**Background:** `_persist_author_selections` in `services.py` currently resolves genre selections by matching the submitted string name against `BookCategory`, `BookGenre`, and `BookSubgenre` rows. If two levels share a name (plausible in a large catalog), the match resolves to the wrong level. More broadly, the frontend should submit genre IDs, not genre names, so the backend is not doing string-lookup resolution at write time.

- `GET /genres` response adds `id` (integer PK) to each category, genre, and subgenre entry alongside `name`
- The onboarding frontend submits selected genre IDs (not names) in `OnboardingForm.genres`
- `OnboardingForm.genres` type changes from `list[str]` to `list[int]` (genre-level IDs); validation resolves IDs against the loaded catalog and rejects unknown IDs
- `_persist_author_selections` looks up genre records by ID instead of by name; removes the sequential N×3 query loop in favor of a bulk lookup
- `serialize_author` continues to return genre names (human-readable output is unchanged); it resolves names from the already-loaded related objects
- All existing tests updated; new tests cover: ID submission round-trip, unknown ID rejection, duplicate ID deduplication, and the absence of name-collision ambiguity
- **Note:** this is a breaking change to the `POST /onboarding` payload shape; the frontend must be updated in the same PR

---

### F036 — Automate the production deployment runbook

**Type:** Feature
**As** a developer, I can deploy a generated site to production by running a script instead of following manual steps, so that future deployments are fast and repeatable.

- Depends on F035 (the manual runbook must exist first)
- Convert the F035 deployment runbook into an automation script covering hosting setup, file transfer, WP configuration, DNS, and SSL
- Feeds into and may overlap with F015–F017 in the backlog

---

### F019 — Protect website generation with reCAPTCHA v3

**Type:** Feature
**As** the product owner, I want automated submissions blocked so that the public website-generation flow cannot be abused to consume generation resources.

- Load reCAPTCHA v3 on the single-page generation form and request a token for the `generate_site` action immediately before submission
- Submit the token with the form; `POST /generate` verifies it with Google's server-side verification API before validation or site generation begins
- Reject missing, invalid, expired, wrong-action, wrong-hostname, and below-threshold tokens with a safe error response; no site ID or files are created
- Keep the site key, secret key, and minimum score in environment configuration; the secret is never sent to the browser or logged
- Fail closed when Google's verification service is unavailable
- Tests mock the verification API and cover valid, missing, invalid, low-score, action mismatch, hostname mismatch, and service-failure responses

---

### R001 — Document Divi option keys for production site configuration

**Type:** Research Task
**As** a developer on this project, I need a reference for how Divi stores WordPress configuration so that generated sites can later be configured in production.
**Deliverable:** `divi_option_keys.md`

- Document relevant option keys, value formats, field mappings, and version caveats
- Required for the production configuration portions of F017, not for Milestone 1 generation and preview

---

### F024 — Create the Design Systems Library

**Type:** Feature
**As** a developer, I can create, version, and manage multiple visual styles so AWG can expand its template catalog without creating separate child themes.

- Not required for Milestone 1, which ships a single hardcoded "Classic" template (F004) with no library infrastructure
- Store each Design System in its own version-controlled folder, such as `design-systems/classic/`
- Each Design System includes `manifest.json`, Theme Builder exports, page layout exports, and preview assets/templates
- `manifest.json` includes style name, genre tags, style metadata, and any values needed by the onboarding picker
- Start with 1 template layout: migrate the v1 "Classic" design into the library format
- Invalid or incomplete manifests fail validation with actionable developer errors
- Tests cover manifest parsing, required fields, invalid manifests, and lookup by selected Design System ID

---

### F031 — Upgrade Website Templates to a visual picker with OPST previews

**Type:** Feature
**As** an end user, I can browse available website templates visually and preview how each affects the top of my homepage before selecting one.

- Depends on F024 (Design Systems Library) and having more than one template available
- Upgrades F004's single hardcoded "Classic" option into a visual style picker backed by the Design Systems Library
- The preview uses a One-Page Static Template (OPST), not a full WordPress demo site
- OPST previews dynamically apply the user's primary and secondary brand colors
- OPST previews use onboarding copy where available and safe fallback copy where fields are still blank
- Selected template value is included in `OnboardingForm` and passed to the generation flow
- The generator uses the selected template as the basis for the generated website code

---

### F032 — Generate a series detail page for book series

**Type:** Feature
**As** an end user, when one of my books is part of a series, my generated site includes a dedicated page for that series.

- Only relevant once a book is marked as part of a series (F002 series fields)
- Out of scope for Milestone 1, which only generates per-book content (F026, F027)

---

### F010 — Implement the pipeline status UI page

**Type:** Feature
**As** an end user, I can see the progress of long-running production provisioning.

---

### F011 — Run production provisioning as a background job

**Type:** Feature
**As** an end user, I can start production provisioning without holding an HTTP request open.

---

### F012 — Integrate the Cloudways API client

**Type:** Feature
**As** a developer, I can create and configure production applications through Cloudways.

---

### F013 — Integrate the Cloudflare API client

**Type:** Feature
**As** a developer, I can configure production DNS records through Cloudflare.

---

### F014 — Run SSH and WP-CLI commands reliably

**Type:** Feature
**As** a developer, I can execute production setup commands with predictable failures and timeouts.

---

### F015 — Clone the starter kit into a production application

**Type:** Feature
**As** an end user, I can have generated code copied into a production application.

---

### F016 — Install WordPress core in production

**Type:** Feature
**As** an end user, I can have WordPress installed in the production application.

---

### F017 — Configure the production site

**Type:** Feature
**As** an end user, I can have generated author content and branding applied to the production WordPress site.

---

### F006 — Send the client a production welcome email

**Type:** Feature
**As** a client author, I receive the production URL and credentials after deployment.

---

### F008 — Provision an ecommerce site on a dedicated server

**Type:** Feature
**As** an end user, I can deploy an ecommerce site on isolated production infrastructure.

---

### T001 — Provision the ecommerce demo site

**Type:** Task
**Deliverable:** A deployed ecommerce demo site.

---

### F009 — Log in to the generator tool

**Type:** Feature
**As** an administrator, I can access protected administrative capabilities.

This is not required for the Milestone 1 user generation flow. Any future
administrative pages must be separately authenticated and authorized.

---

### F018 — Automate deployments for the generator app

**Type:** Feature
**As** a developer on this project, I can merge to `main` and have the generator app deploy automatically so I don't have to manually SSH into the server to push updates.
**Deliverable:** `.github/workflows/ci.yml` and `.github/workflows/deploy.yml`

- CI on every push to any branch: install deps, lint (flake8/ruff), type-check (mypy), run unit test suite
- Deploy on merge to `main`: push to `production` branch, trigger Cloudways Git deployment via API
- Cloudways Git integration: each server/app configured to pull from `production` branch on deploy trigger
- **Human prerequisites:** decision on where the generator app itself lives (Cloudways app on shared server, or its own server — determines the deploy.yml target); GitHub Actions secrets configured (`CLOUDWAYS_API_KEY`, `CLOUDFLARE_API_TOKEN`, SMTP credentials, `DJANGO_SECRET_KEY`); GitHub repo created with Actions enabled

---

### T002 — Build an automated regression test suite

**Type:** Task
**As** a client, I want confidence that when new features are rolled out the existing provisioning workflow still works end-to-end, so that my site isn't broken by an update.
**Deliverable:** `tests/integration/` — a suite that provisions and tears down a real test app against a dedicated throwaway environment, runnable before any release.

- Tests hit real APIs — not run on every push; run manually before releases or on a nightly schedule
- `tests/integration/conftest.py` — shared fixtures: test Cloudways app credentials, test Cloudflare zone, cleanup teardown
- `tests/integration/test_full_provision.py` — full provisioning flow with real API calls; verifies site URL returns HTTP 200 after completion; cleans up the test app on teardown
- **Human prerequisite:** dedicated throwaway Cloudways app + Cloudflare zone reserved exclusively for testing — must not be a real client zone

---

---

## Done

### F027 — Give each book its own detail page

**Type:** Feature
**As** an end user, each of my books gets its own page with a real URL instead of sharing one generic Book Detail Page.

**Implementation note:** `slugify_title()` (pure function) derives URL slugs; `_assign_slugs()` handles collisions by appending `-2`, `-3`, etc. Per-book pages created with `--post_name=<slug>`; Books listing page now renders a `<ul>` of links. The single generic Book Detail page from F026 is removed. 284/284 full suite green.

---

### F026 — Generate structured WordPress pages and book content

**Type:** Feature
**As** an end user, my generated website includes the key author pages and structured book content so I start with a usable site instead of a blank theme.

**Implementation note:** `generation/pages.py` generates all 5 pages (Home, About, Books, Contact, Book Detail) via WP-CLI and creates `awg_book` CPT records for each book from serialized onboarding data. Home page is set as the WordPress static front page. `generation/subprocess_runner.py` gained `default_capture_runner` (returns stdout) to capture new post IDs from `--porcelain` output. 59 unit tests; 259/259 full suite green.

---

### F033 — Register the Books custom post type

**Type:** Feature
**As** a developer, the generated WordPress site has a Books custom post type that mirrors every book field collected in onboarding, so book content is structured and queryable rather than embedded in static page copy.

- Register a Books custom post type with fields covering every book detail captured in onboarding:
  - title, cover image, description, at least one buy link, category, genre, subgenre
  - standalone/series flag; when part of a series: series name, book number, total books, series-complete flag
  - repeatable editorial reviews (publication name) and reader reviews (reviewer name, optional credentials, optional photo, optional star rating, optional original-review link)
  - starred-review flag, award icons
  - optional reader-fit copy, optional sample chapter PDF and its original filename
  - one-based onboarding position (for ordering books on the site)
- Custom post type registration code is modular and separate from WordPress core and third-party plugin code
- Depends on F025
- Tests or validation cover: custom post type registration, all fields present and correctly typed

---

### F025 — Set up the base WordPress site scaffold

**Type:** Feature
**As** a developer, I can generate a valid, self-contained WordPress site folder from onboarding data so that every subsequent generation feature has a working base to build on.

- Install WordPress core into a dedicated generated-site folder
- Apply baseline WordPress configuration: site name, tagline, admin credentials, and permalink structure
- Keep the generated site folder structure clean and self-contained; it must not depend on production hosting, Cloudways, DNS, or SSL
- Keep custom code modular and separate from WordPress core and third-party plugin code
- Tests or validation cover: WP core installation, required files present, baseline configuration applied

---

### F021 — Set up Django application scaffold

**Type:** Feature
**As** a developer, I have a working Django project structure to build on.

- Django 5.2 LTS project package in `generator/` with settings, URL conf, WSGI, and ASGI entrypoints
- Custom `User` model in `accounts/` extending `AbstractUser` with a UUID v4 primary key (`AUTH_USER_MODEL = "accounts.User"`)
- `onboarding/` Django app with `GET /onboard`, `POST /generate` (stub), and `/` → `/onboard` redirect
- Django-namespaced templates in `onboarding/templates/onboarding/` and statics in `onboarding/static/onboarding/`
- `requirements.txt` with pinned dependencies (Django, pydantic, PyYAML, python-dotenv, pytest, pytest-django)
- `pytest.ini` configured for test discovery with `DJANGO_SETTINGS_MODULE`
- `.env.example` documenting `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, and future env vars
- 19 unit tests covering views, user model, config loading, and static file paths

---

### F023 — Server inventory config loading

**Type:** Feature
**As** a developer, I can define the server inventory in a YAML config file and have it validated on app startup.

- `config/config.yaml` — YAML file tracking all servers (shared standard server, ecommerce demo server, and future ecommerce client servers)
- `models/config_models.py` — `WebsiteServer` and `AppConfig` Pydantic models; `ServerType` enum with `standard` and `ecommerce` values
- `config/loader.py` — `load_config(path)` parses and validates the YAML; raises `ConfigError` on missing file or invalid schema
- 7 unit tests in `tests/unit/test_config_loader.py`

### F003 — Upload the author's headshot in the form

**Type:** Feature
**As** an end user, I can upload an image file directly in the form so it gets placed on the generated site's About section automatically.

- Image upload field in the onboarding form
- Validate the file type and size before generation
- Headshot is copied into the generated site's assets and rendered in its About section

**Implementation note:** `OnboardingForm.author_headshot_key` identifies the multipart file key; the view validates type (JPG/PNG/WebP) and size (≤10 MB) via `_validate_image`; `persist_onboarding` saves the file via `_assign_upload` and cleans it up atomically on any failure. `serialize_author` returns `headshot_url`. Persistence-layer tests cover headshot saved, headshot omitted when key absent, and file cleanup on rollback.

---

### F002 — Build the client's book portfolio in the form

**Type:** Feature
**Status:** Completed
**As** an end user, I can add multiple books to the form and add or remove book entries dynamically without reloading the page.
**Deliverable:** The database contains every submitted book field and a
post-onboarding page reads those fields from the database and displays them.
Uploaded images are displayed on the page, and each sample chapter PDF is
available through a download link.
**Deliverable:** After reviewing the database-loaded author and books, the user can
click Generate and call `POST /generate` without error. F002 does not generate
website code; the endpoint is intentionally a no-op until F030.

- Each book requires title, cover image, description, at least one buy link,
  category, genre, and standalone/series information; subgenre is optional
- Category, genre, and subgenre occupy the first three positions of a
  four-column classification row. A "Part of a series" checkbox follows on the
  next row; series books require series name, book number, and total books,
  with an optional series-complete checkbox
- Optional repeatable editorial and reader reviews share one stored review
  model. Editorial reviews identify the publication; reader reviews identify
  the reviewer and may include credentials. Reviewer photos, star ratings, and
  original-review links are optional. A review may also independently be
  marked as a starred review; awards still require icons
- Accept link fields with or without an HTTP scheme, require a valid public
  domain suffix, and normalize bare domains to HTTPS before persistence
- Optional reader-fit copy and sample chapter PDF
- Add/remove rows handled client-side by the Vite bundle built at
  `onboarding/static/onboarding/dist/onboard.js` — no page reload
- Book entries modeled as a list of `BookEntry` in `OnboardingForm`
- Persist all validated book data in records associated with the author
- Store normalized category, genre, and subgenre records in separate lookup
  tables; books reference a genre ID and an optional subgenre ID
- Store series in a separate table; series books reference it while standalone
  books have no series
- Store one-based onboarding order as `book.onboarding_position`
- Store uploaded file metadata and durable storage references with the
  corresponding book records; do not store temporary request objects
- Persist book covers, reviewer photos, award icons, and sample chapter PDFs
- Store each sample chapter's original uploaded filename separately from its
  randomized storage key and use that filename when the PDF is downloaded
- Accept JPG, PNG, and WebP images up to 10 MB per file
- Accept PDF sample chapters up to 20 MB per file
- Validate file content as well as file extension and declared MIME type
- Use non-user-controlled storage paths and never expose filesystem paths
- Save book records and file references atomically with F001; clean up written
  files and database records if any part of the submission fails
- Tests cover complete persistence, multiple books and nested files, accepted
  image and PDF types, size/type rejection, missing files, atomic rollback, file
  cleanup, the database-backed post-onboarding display and PDF download link,
  and the callable no-op generation endpoint
- The database-backed confirmation displays every user-facing book field,
  including explicit empty or not-applicable states for optional content

**Implementation note:** Dynamic book rows, nested content, dependent genre
selection, multipart submission, image/PDF validation, and Pydantic models are
implemented. `POST /onboarding` atomically persists the author and books;
`GET /authors/<author_id>` and `GET /authors/<author_id>/books` reload the
separate resources for review; and `POST /generate` currently verifies the
author exists and returns success without generating anything. Passing saved
book data through actual website generation remains part of F030.

---

### F001 — Fill out the client onboarding form

**Type:** Feature
**As** an end user, I can fill out a single-page form with all author details so AWG has everything needed to generate and preview a site.

**Deliverable:** The `author` table contains all submitted author onboarding
information except the book fields, which are owned by F002.

- **Client Identity fields:** author name (as it appears publicly), contact email
- **Site Identity fields:** site domain, site tagline / author bio one-liner, author short bio (paragraph, shown in About section), author long bio (optional, for full About page)
- **Genre & Branding fields:** autocomplete multi-select backed by normalized
  category, genre, and subgenre tables seeded from `genres.json`; primary and
  secondary brand colors selected together
- **Social & Marketing fields:** newsletter signup link or Kit form ID; Twitter/X, Instagram, Facebook, TikTok, YouTube, Goodreads (all optional)
- Client-side required-field validation before submission is allowed
- Hex color validation and URL validation on social link fields
- Persist the complete validated non-book `OnboardingForm` data in database
  records only after the complete submission passes validation
- Invalid submissions and failed persistence operations do not retain partial
  F001 database records
- Files: `models/onboarding.py`, `onboarding/models.py`,
  `onboarding/services.py`,
  `onboarding/migrations/0001_semantic_domain_schema.py`,
  `onboarding/migrations/0002_seed_genre_catalog.py`,
  `frontend/onboarding/App.jsx`, `tests/unit/test_onboarding_models.py`,
  `tests/unit/test_onboarding_persistence.py`, and
  `tests/unit/test_django_views.py`
- Tests: valid input passes, required fields enforced, hex color validation, URL
  validation on social links, complete non-book persistence, and atomic rollback
- **Human prerequisite:** Levi must sign off on the field list before this is built — any missing fields discovered after this ships require retroactive changes across models, form HTML, and orchestrator

**Implementation note:** React presents one question at a time, groups related
color and social inputs, and submits multipart form data to Django. Author name,
contact email, site domain, at least one genre, and at least one complete book
are required. Production provisioning and existing WordPress site fields are
intentionally excluded. Author genres use a searchable autocomplete with
hierarchy paths and removable selections rather than a full checkbox list.
Successful onboarding stores F001 fields under an author UUID and preserves
author genre selection order through category-, genre-, and subgenre-selection
tables. Book records and uploaded files remain F002.

---

### F004 — Select a Website Template

**Type:** Feature
**As** an end user, I can select which website template AWG will use to generate my site.

- v1 ships exactly one selectable template, labeled "Classic," under the user-facing label "Website Templates"
- The page shows one line of copy noting more website templates are coming soon
- No visual preview of the template is shown at this stage
- Selected template value is included in `OnboardingForm` and passed to the generation flow
- A multi-template visual picker with OPST previews is out of scope for v1 — see F031 in the backlog

**Dev note:** A plain dropdown with 6 hardcoded template options (defined as `DIVI_TEMPLATES` in `onboarding/views.py`) already exists in `onboarding/templates/onboarding/onboard.html`. Replace it with a single hardcoded "Classic" option under the "Website Templates" label plus the one-line coming-soon copy; no picker UI or preview needed.
