# Author Website Generator — Feature List

Related documents: [README](README.md) · [Product spec](SPEC.md) · [Product decisions](DECISIONS.md) · [Provisioning pipeline](PIPELINE.md)

## ID Tracker

- Latest feature ID: `F023`
- Latest task ID: `T002`
- Latest research ID: `R001`

Four lists: **Doing** (active work), **Milestone 1** (ordered by priority), **Backlog** (unordered), and **Done**.

ID prefixes: `F` = feature, `T` = task, `R` = research task.

---

## Doing

---






---

## Milestone 1 Epic — Generate and Preview a Standard Author Website

Milestone 1 is v1 of the product for standard, non-ecommerce author websites:
a user can complete the single-page author website form, submit it, and have
AWG generate the complete site. Each generated site is persisted with a unique
ID and is immediately visitable inside the AWG application at
`/sites/<site_id>`.

Milestone 1 stops at generation and preview. It does not include payments,
billing, website maintenance, admin pages, production deployment, customer
domains, DNS, SSL, production hosting, ecommerce features, shopping carts, or
payment processing.

---

### F004 — Select a Divi template with visual preview

**Type:** Feature
**As** an end user, I can browse available Divi templates, click each one to see a screenshot of what a site built with that template looks like, and select the one I want applied to the generated site.

- Original spec had this as a plain dropdown — this feature upgrades it to a visual picker (clickable thumbnails with screenshots)
- Selected template value is included in `OnboardingForm` and passed to F005
- The generator uses the selected template as the basis for the generated website code

**Dev note:** A plain dropdown with 6 hardcoded template options (defined as `DIVI_TEMPLATES` in `onboarding/views.py`) already exists in `onboarding/templates/onboarding/onboard.html`. Remaining work: upgrade to a visual clickable thumbnail picker with screenshot assets.

---

### F005 — Generate the full author website code

**Type:** Feature
**As** an end user, I want my submitted form data turned into a complete author website so that I can review the generated result.

- Milestone 1 generation supports standard, non-ecommerce author websites only
- `generate_site(form)` validates the submitted onboarding data and generates the full website code, including all pages, content, styling, and assets required for the preview
- Generation uses the selected template and applies the submitted author identity, biographies, branding, headshot, books, newsletter information, and social links
- The generated result is self-contained and does not depend on a production WordPress, Cloudways, Cloudflare, DNS, SSL, or hosting operation
- Generation failures return a safe, human-readable error and do not create a partial site record
- Files: `generator/site_generation.py`, `tests/unit/test_site_generation.py`
- Tests: complete generation, optional-field handling, invalid input, template/content mapping, and generation failure

---

### F020 — Store and preview each generated website

**Type:** Feature
**As** an end user, I can view the website generated from my submission on a newly created AWG page.

- After successful generation, create a cryptographically random, URL-safe unique site ID
- Persist the complete generated code and the metadata required to serve it, keyed by site ID
- `GET /sites/<site_id>` renders the generated website within AWG; it is a preview, not a production deployment or customer hosting environment
- Unknown or malformed IDs return 404 without exposing storage paths or other site records
- A successful response from `POST /generate` includes the site ID and `/sites/<site_id>` URL
- Site creation is atomic: a preview becomes addressable only after all generated code has been written successfully
- Tests cover unique ID creation, persistence, successful preview rendering, missing IDs, malformed IDs, and incomplete-write cleanup

---

### F007 — Get a clear result — site URL on success, specific error on failure

**Type:** Feature
**As** an end user, when generation completes I can open the generated website, and if it fails I see a human-readable error message.

- On success: redirect to or display a link to `/sites/<site_id>`
- On failure: show a specific, actionable error plus a dismiss button
- No internal exception details or stack traces are exposed to the user
- Error display persists until the user dismisses it via X or resubmits

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

## Backlog

---

The backlog contains work that is useful after Milestone 1 but is not required
to generate and preview a standard, non-ecommerce website inside AWG.

### R001 — Document Divi option keys for production site configuration

**Type:** Research Task
**As** a developer on this project, I need a reference for how Divi stores WordPress configuration so that generated sites can later be configured in production.
**Deliverable:** `divi_option_keys.md`

- Document relevant option keys, value formats, field mappings, and version caveats
- Required for the production configuration portions of F017, not for Milestone 1 generation and preview

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

## Done


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

**Dev note:** The headshot file input already exists in `onboarding/templates/onboarding/onboard.html`. Remaining work: server-side file handling, size/type validation, and integration with site generation.

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
website code; the endpoint is intentionally a no-op until F005.

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
- Add/remove rows handled client-side by `onboarding/static/onboarding/onboard.js` — no page reload
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
book data through actual website generation remains part of F005.

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
