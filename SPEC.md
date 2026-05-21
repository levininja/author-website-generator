# Author Website Generator — Product Spec

---

## The Product Definition

The product is an engineering-grade, managed website service built exclusively for authors. It replaces manual, one-off contractor builds with standardized, high-performance WordPress platforms. The system functions as a productized service—balancing affordability with technical stability—while guaranteeing authors retain full autonomy, true site portability, and domain ownership.


### Core Features & Author Tools

- **Standardized Front-End:** High-performance, mobile-responsive layouts built formulaically using the Divi builder.
- **Essential Author Components:** Dedicated architecture for "About" sections, book portfolios, and optimized lead magnets.
- **Marketing Funnel Integration:** Built-in connectivity for newsletters (Kit) and podcast marketing funnels.
- **Author Platform Ecosystem:** Integrations with standard author tools like BookFunnel, StoryOrigin, BetaBooks, BetaReader.io, and Plottr. *(Solve later — not in v1)*
- **Serialization & Monetization:** Substack integration capabilities for hosting serialized fiction and managing audience donations. *(Solve later — not in v1)*
- Allows for user to select from many different Divi templates and for that to be passed into the tool.

### Managed Infrastructure & Backend Automation

- **Complete Technical Maintenance:** Ongoing troubleshooting, mobile responsiveness optimization, and core technical SEO management. *(Solve later — not in v1)*
- **Infrastructure Management:** Fully handled email hosting, DNS administration, and secure team login management. *(DNS in v1; email hosting and client login management — solve later)*

---

## Technical Architecture & Decisions
### Core Platform & Tech Stack of This Project
Python

### Core Platform & Tech Stack of Websites we will Generate

- **Content Management System:** WordPress.
- **Theme/Builder:** Divi Builder for standardized, formulaic front-end design.
  - **Licensing:** Start with a normal (single-site) Divi license for POC on one site. When scaling to multiple sites, upgrade to a developer license. *(Reminder: prompt Levi to upgrade when multi-site scaling begins.)*
- **Development Environment:** VS Code for coding and local environment management.
- **Custom Code:** All PHP modifications live in either:
  - A custom **must-use plugin (mu-plugin)** specific to this system, OR
  - A custom **Divi child theme**
  - We do **not** modify WordPress core, Divi core, or any other plugin directly, so that WP/PHP updates never override our code. All custom code is modular and easy to find.

### Infrastructure & Hosting of Websites we will Generate

- **Primary Hosting Provider:** Cloudways (A plan). Fallback: Liquid Web (B plan).
- **NO WordPress Multisite.** Every client gets a separate WordPress install.
- **Server Architecture:**
  - All non-ecommerce author websites share **one server** (Cloudways has strong site isolation; the rare kernel-level exploit that could break out of one app targets ecommerce sites, not standard author sites).
  - Each ecommerce author website gets its **own dedicated server**. This raises costs for ecommerce clients.
  - The example/demo site lives on the shared non-ecommerce server.
  - The ecommerce example/demo site lives on its own separate server.
- **Config file:** A config file will track all servers (shared non-ecommerce server, ecommerce example server, and each ecommerce client server).
- **Staging:** One shared staging environment for the example site only. Clients do not get individual staging environments — the underlying code is identical across all sites; only skins and content differ.

### Domain & DNS

- **Clients purchase and own their own domains.**
- Levi performs DNS transfers with clients during onboarding.
- **Standard DNS: Cloudflare (free tier, per client).**
  - Cloudflare is free, fast, and excellent
  - Real DNS dashboard with API access
  - DNS record management can be fully automated (new client = API call to create their records)
  - Clients get free SSL, DDoS protection, and CDN as a bonus
  - Levi can manage their zone if they add him as a member
- Process: client moves nameservers to Cloudflare; Levi creates/manages the A record pointing their domain to the Cloudways server.

### Source Control & Deployment

- **Source Control:** GitHub manages configurations and site templates.
- **Git integration:** Cloudways has a built-in Git integration. Each server/app is configured to pull from a specific branch (`production`). When a deployment is triggered, the Cloudways API fetches the latest commit from the `production` branch and deploys it.
- **Deployment model:**
  - **v1 (implement now):** A deployment replaces the backend PHP code (mu-plugin + child theme) for **all sites** on the server. It replaces the database only for the **example site**. Client site databases are not touched by deployments.
  - **v2 (document, do not implement):** *(TBD — Levi to define. Likely: per-client database seeding or update propagation for structural/schema changes.)*
- **CI/CD:** GitHub Actions automates deployment and ongoing maintenance, replacing manual contractor builds. Automated testing is integrated into the pipeline to ensure sites remain stable and scalable.
- **Client Autonomy:** Architecture mandates true site portability. Clients retain full domain ownership. The system is a managed service, not a proprietary locked-in platform.

### Automation & Orchestration

- **Workflow Engine:** OpenClaw handles orchestration.
- **AI Integration:** Multi-agent orchestration (OpenClaw framework, Claude, ChatGPT/Codex) handles complex automated workflows, hooking into site generation and maintenance tasks.
- **WP-CLI:** Used to generate and configure WordPress sites automatically over SSH. All WP configuration (install, DB import, option-setting, user creation) is scripted via WP-CLI — no manual dashboard interaction required.

### Security

- The orchestration/generator web app is deployed as a public-facing URL but is a **black box** to anyone without credentials:
  - The single page (the onboarding/generation form) is protected by username and password.
  - No external API endpoints exposed.
  - Nothing accessible to unauthenticated users — no attack surface beyond the login form.
- Future consideration: potentially allow clients to access the form themselves to self-provision, but this is not planned and requires significant security review before implementation.

### Integrations

- **Newsletter:** Kit (ConvertKit) — v1.
- **BookFunnel, StoryOrigin, BetaBooks, BetaReader.io, Plottr:** Solve later.
- **Substack:** Solve later.
- **Billing / Client Management:** Solve later.
- **Analytics & Feedback:** Solve later.
- **Email Hosting:** Solve later.

---

## Onboarding Form — Inputs

The generator is triggered by a single form (one page, username/password protected). Fields:

### Client Identity
- Author name (as it appears publicly)
- Author email address
- WordPress admin username
- WordPress admin password

### Site Identity
- Site/domain name (e.g. `janedoeauthor.com`)
- Site tagline / author bio one-liner
- Author short bio (paragraph, shown in About section)
- Author long bio (optional, for full About page)
- Author headshot (image upload)

### Genre & Branding
- Genre(s) — multi-select or free text
- Primary brand color (hex)
- Secondary brand color (hex)
- Divi template selection — dropdown of available starter templates

### Book Portfolio
- Book title(s) — repeatable field (title, cover image, description, buy links)

### Social & Marketing
- Newsletter signup link or Kit form ID
- Social media links (Twitter/X, Instagram, Facebook, TikTok, YouTube — all optional)

### Domain & DNS
- Domain name (for Cloudways app configuration and Cloudflare DNS record)
- Confirm: nameservers already pointed to Cloudflare? (checkbox)

### Site Type
- Ecommerce site? (yes/no) — determines which server the app is provisioned on

---

## Onboarding Flow: Intake to Live Site

> Scope: v1. No maintenance. Pure site generation from form inputs.

```
Client/Levi fills out onboarding form and submits
        ↓
Form validates all required fields client-side
        ↓
On submit: show "Provisioning..." status message
On error: show full error message (persists until user dismisses via X or resubmits)
        ↓
Orchestration app receives form data
        ↓
[ Step 1 ] Cloudways API → create new Application on the correct server
           (non-ecommerce server OR new dedicated server if ecommerce)
        ↓
[ Step 2 ] SSH into server → clone starter kit repo into new app folder
           Starter kit = custom Divi child theme + mu-plugin + standard plugin list
        ↓
[ Step 3 ] WP-CLI → install WordPress core
        ↓
[ Step 4 ] WP-CLI → import starter database
           (pre-built Divi layouts, standard pages: Home, About, Books, Contact)
        ↓
[ Step 5 ] WP-CLI → set all client-specific values
           (site name, tagline, author bio, colors, logo/headshot, social links,
            Kit newsletter form, book portfolio entries, selected Divi template)
        ↓
[ Step 6 ] Cloudways API → attach client's domain to the new app + provision SSL
        ↓
[ Step 7 ] Cloudflare API → create A record pointing client domain → server IP
        ↓
[ Step 8 ] Email → send client their WordPress admin URL and credentials
        ↓
Form UI → show success message with site URL
        ↓
Live site ✓
```

**Expected provisioning time:** ~5–10 minutes (most time: DNS propagation + SSL provisioning).

---

## What's Out of Scope for v1

- Per-client staging environments
- Maintenance automation (plugin/core updates, backups, uptime monitoring)
- BookFunnel / StoryOrigin / BetaBooks / Plottr integrations
- Substack integration
- Billing and client management portal
- Email hosting setup
- Client self-service access to the generator form
- v2 deployment behavior (database propagation to client sites)
- Ecommerce functionality beyond server isolation

---

## Open Questions / Decisions Deferred

- v2 deployment spec: what exactly should propagate to client site databases on deploy?
- Client self-service form: security model, access control, whether to build at all
- Email hosting provider (Google Workspace reseller, Zoho, Fastmail, other?)
- Billing/invoicing integration
- Maintenance workflow (WP-CLI update scripts, ManageWP, hosting-native, other?)

---

## Milestones

> Each milestone has a hard exit criterion. Streams within a milestone are fully parallel — each stream touches only its own files, so separate agents or developers cannot conflict. File paths are relative to the project root.

---

### Milestone 1 — Foundation

**Goal:** A runnable, authenticated Python web app with a loaded config system and a documented server inventory. Every downstream milestone depends on this landing first.

**Exit criterion:** `python app.py` starts a password-protected server; `config/config.yaml` loads and validates correctly; `pytest` runs and the auth tests pass; all required env vars are documented in `.env.example`.

---

#### Stream 1A — Project Scaffold & Config System

Establish the project layout, dependency manifest, environment variable contract, and the config loader that all other modules will import.

**Files:**
- `requirements.txt`
- `.env.example`
- `pytest.ini`
- `config/config.yaml` — server inventory: shared non-ecommerce server, ecommerce example server, per-ecommerce-client servers; Cloudways + Cloudflare API credentials pointers
- `config/loader.py` — loads and validates config.yaml; raises on missing required keys
- `models/config_models.py` — Pydantic models for config schema (ServerEntry, AppConfig, etc.)
- `tests/unit/test_config_loader.py`

> **Risk:** The config schema is the shared contract for the entire system. Design it broadly enough now that adding an ecommerce client server later doesn't require a breaking change.

---

#### Stream 1B — Web App Shell & Authentication

A minimal Flask app with session-based login protecting all routes. No form logic yet — just the shell.

**Files:**
- `app.py` — Flask app factory; mounts routes; loads config
- `routes/auth.py` — login / logout routes; session management
- `templates/base.html` — base layout (nav, flash messages)
- `templates/login.html` — username + password form
- `static/css/base.css`
- `tests/unit/test_auth.py` — correct credentials pass, wrong credentials fail, protected routes redirect unauthenticated users

> **Risk:** Credentials must come from env vars only — never from config.yaml, which may be committed to source control.

---

### Milestone 2 — External API Clients & Form Layer

**Goal:** All four external service clients are built and unit-tested in isolation. Form data models are defined. The onboarding form HTML is built. These six streams have zero file overlap and can ship in any order or fully in parallel.

**Exit criterion:** All unit tests pass against mocked HTTP responses. Form renders with all fields from the spec and enforces client-side required-field validation.

**Dependency:** Milestone 1 complete (config loader available to import).

---

#### Stream 2A — Cloudways API Client

Low-level HTTP client wrapping the Cloudways API. Exposes only the primitives consumed by Stream 3A.

**Files:**
- `integrations/cloudways.py` — `create_application()`, `poll_until_ready()`, `attach_domain()`, `provision_ssl()`, `get_server_ip()`
- `tests/unit/test_cloudways_client.py`

> **Risk:** Cloudways app creation is **asynchronous** — the API returns an operation ID and you must poll until the app status is `running`. This is a common gotcha. `poll_until_ready()` must be a first-class method with a configurable timeout and backoff, not an afterthought. Retrofitting polling later will require rewriting the orchestrator.

---

#### Stream 2B — Cloudflare API Client

Low-level HTTP client wrapping the Cloudflare API. Zone lookup is dynamic — do not require a zone ID in the form.

**Files:**
- `integrations/cloudflare.py` — `get_zone_id_for_domain()`, `create_a_record()`, `delete_a_record()`
- `tests/unit/test_cloudflare_client.py`

> **Risk:** Cloudflare requires the **zone ID**, not the domain name, for record management. `get_zone_id_for_domain()` must look it up from the Cloudflare account using the API token — this implies the token must have `Zone:Read` permission in addition to `DNS:Edit`. Document required token permissions in `.env.example`.

---

#### Stream 2C — SSH & WP-CLI Runner

Low-level primitive for executing shell commands over SSH. WP-CLI-specific logic lives in Milestone 3, not here — this module is a general-purpose runner.

**Files:**
- `provisioning/ssh_runner.py` — `SSHRunner` class: connect, `run(command)` → `(stdout, stderr, exit_code)`, `upload_file()`, disconnect; configurable timeout and retry
- `tests/unit/test_ssh_runner.py` — mock paramiko; test success path, non-zero exit code, timeout, connection refused

> **Risk:** This is the **highest-failure-probability component** in the system. WP-CLI over SSH can fail silently, return misleading exit codes, or hang indefinitely. Requirements: always capture stderr separately; treat any non-zero exit code as a hard error with stderr surfaced to the caller; enforce a per-command timeout; retry on transient connection drops (not on WP-CLI errors). Getting this wrong produces a provisioning pipeline that appears to succeed but produces broken sites.

---

#### Stream 2D — Email Integration

Transactional email sender for the post-provisioning welcome message.

**Files:**
- `integrations/email_sender.py` — `send_welcome_email(author_email, admin_url, username, password)`; SMTP or API-based (SMTP credentials from env vars)
- `templates/email/welcome.html` — welcome email with site URL, admin URL, and credentials
- `tests/unit/test_email_sender.py`

---

#### Stream 2E — Onboarding Form Data Models

Pydantic models for all onboarding form fields. These are the validated input contract handed to the orchestrator.

**Files:**
- `models/onboarding.py` — `BookEntry`, `SocialLinks`, `OnboardingForm` covering all fields from the spec: client identity, site identity, genre & branding, book portfolio (list of `BookEntry`), social & marketing, domain & DNS, site type (ecommerce flag)
- `tests/unit/test_onboarding_models.py` — valid input passes, required fields enforced, hex color validation, URL validation on social links

---

#### Stream 2F — Onboarding Form UI

The single-page form users submit to trigger provisioning. Pure frontend — no backend route wiring yet (that is Stream 4B).

**Files:**
- `templates/onboarding.html` — all form fields; repeatable book portfolio rows (add/remove); "Provisioning..." overlay state; inline error display; success state
- `static/css/form.css`
- `static/js/form.js` — client-side required-field validation; dynamic book portfolio rows; submits via fetch; manages UI state transitions (idle → provisioning → success / error)

---

### Milestone 3 — WordPress Provisioning Steps

**Goal:** Each of the 8 provisioning steps is implemented as a discrete, independently testable function. Steps are pure domain logic — they call clients from Milestone 2 and return structured success/error results. They have no knowledge of each other or of the HTTP layer.

**Exit criterion:** All step unit tests pass with mocked dependencies from M2.

**Dependency:** Milestone 2 complete.

---

#### Stream 3A — Cloudways Steps (Steps 1 & 6)

**Files:**
- `provisioning/steps_cloudways.py` — `step1_create_application(form, config)`: creates app on correct server (non-ecommerce shared server or new dedicated server based on ecommerce flag), polls until ready, returns app credentials and server IP; `step6_attach_domain_and_ssl(app_id, domain)`: attaches domain, triggers SSL provisioning
- `tests/unit/test_steps_cloudways.py`

> **Risk (critical sequencing bug in the spec):** Step 6 (SSL provisioning) is listed before Step 7 (Cloudflare DNS). This is backwards: Cloudways SSL provisioning via Let's Encrypt requires the domain's DNS to already resolve to the server. Running Step 6 before Step 7 will cause SSL provisioning to fail. **The recommended fix:** reorder to 1 → 2 → 3 → 4 → 5 → 7 → 6 → 8, adding a DNS propagation wait between Steps 7 and 6. Document this decision in the orchestrator. Do not "fix" it silently — update the Onboarding Flow diagram in this spec when implementing.

---

#### Stream 3B — WordPress Install Steps (Steps 2, 3, 4 & 5)

**Files:**
- `provisioning/steps_wordpress.py` — `step2_clone_starter_kit(ssh, app_path, repo_url)`: SSH clone of starter kit (Divi child theme + mu-plugin + plugin list); `step3_install_wp_core(ssh, app_path)`: WP-CLI core install; `step4_import_starter_db(ssh, app_path, db_file)`: WP-CLI DB import; `step5_configure_site(ssh, app_path, form)`: WP-CLI option/meta writes for all client-specific values
- `tests/unit/test_steps_wordpress.py`

> **Risk (Divi data format):** `step5_configure_site` must write Divi brand colors and template selection via `wp option update` and `wp post meta update`. Divi stores this data in serialized PHP arrays under specific option keys (e.g., `et_divi`, theme customizer options). The exact key names and value formats must be researched and validated against the actual Divi version in use **before** implementing Step 5 — getting them wrong produces a site that appears provisioned but renders with no styling. Add a `divi_option_keys.md` reference document to the repo once confirmed.

> **Risk (idempotency):** If the pipeline fails at Step 4 or 5 and is retried, `step3_install_wp_core` will be called against an existing WP install, which causes WP-CLI to error. Add a pre-flight check: if WP is already installed, skip Steps 3 and 4.

> **Risk (SSH key access):** Step 2 clones from GitHub over SSH. The Cloudways server must have an SSH deploy key registered on the starter kit repo. This is an infrastructure prerequisite — document it in the README and fail loudly if the clone fails due to auth rather than silently continuing.

---

#### Stream 3C — DNS & Email Steps (Steps 7 & 8)

**Files:**
- `provisioning/steps_dns_email.py` — `step7_create_dns_record(domain, server_ip, config)`: Cloudflare A record creation; `step8_send_welcome_email(form, admin_url)`: sends credentials email
- `tests/unit/test_steps_dns_email.py`

---

### Milestone 4 — Orchestration & Form Wiring

**Goal:** The complete 8-step pipeline runs as a single background job. The web form submits to a route that kicks off the job. The UI polls for real-time status and renders the correct state at every phase.

**Exit criterion:** Submitting the form against a dev Cloudways/Cloudflare environment triggers the full pipeline; UI progresses through step labels and displays the final site URL on success or a specific error message on failure.

**Dependency:** Milestones 2 and 3 complete.

---

#### Stream 4A — Orchestrator

Calls steps 1–8 in the correct order (per the sequencing fix in Stream 3A). Manages partial failure: records which step failed, wraps the error with context, and exposes job status for polling. Designed for future idempotent retry.

**Files:**
- `orchestrator.py` — `ProvisioningJob` dataclass (status, current\_step, error, result\_url); `run_provisioning(form, config)` executes steps sequentially, updating job state after each; jobs stored in a simple in-memory dict keyed by job ID (sufficient for v1 single-operator usage)
- `tests/unit/test_orchestrator.py` — happy path completes all 8 steps; failure at step N records step N and error; correct step order enforced

> **Risk (blocking HTTP):** Provisioning takes ~5–10 minutes. The orchestrator **must not block the HTTP request**. It must run in a background thread (or asyncio task) and return a job ID immediately. The form route starts the job, returns the ID, and the UI polls a `/status/<job_id>` endpoint. Choose the threading model (Python `threading.Thread` is simplest for v1; switch to Celery only if multi-operator use is needed) and commit to it here — changing it later requires rewriting both the orchestrator and the routes.

---

#### Stream 4B — Form Route & Status UI

Connects the form frontend to the orchestrator and provides real-time step-by-step status.

**Files:**
- `routes/onboarding.py` — `GET /`: renders `onboarding.html` (auth-gated); `POST /provision`: validates `OnboardingForm`, starts background job, returns `{"job_id": "..."}` as JSON; `GET /status/<job_id>`: returns job state as JSON (current step, error if any, result URL if complete)
- `templates/status.html` — step-progress display (8 labeled steps, active/complete/error states)
- `static/js/status.js` — polls `/status/<job_id>` every 3s; updates step indicators; on success shows site URL; on error shows step name + message with dismiss button

---

### Milestone 5 — CI/CD & Hardening

**Goal:** The system is deployable, passing CI, and hardened against the attack surface described in the spec.

**Exit criterion:** Green CI on `main`; full provisioning flow verified end-to-end against real APIs in a dedicated test environment; security checklist passed.

**Dependency:** Milestone 4 complete.

---

#### Stream 5A — GitHub Actions CI/CD Pipeline

**Files:**
- `.github/workflows/ci.yml` — on push to any branch: install deps, lint (flake8/ruff), type-check (mypy), run unit test suite
- `.github/workflows/deploy.yml` — on merge to `main`: push to `production` branch; trigger Cloudways Git deployment via API

---

#### Stream 5B — Integration Tests

Tests that hit real APIs in a dedicated test environment (separate Cloudways app + Cloudflare zone reserved for testing). These are **not** run in CI on every push — they are run manually before releases or on a nightly schedule.

**Files:**
- `tests/integration/conftest.py` — shared fixtures: test Cloudways app credentials, test Cloudflare zone, cleanup teardown
- `tests/integration/test_full_provision.py` — full provisioning flow with real API calls; verifies site URL returns HTTP 200 after completion; cleans up the test app on teardown

---

#### Stream 5C — Security Hardening

Addresses the attack surface defined in the spec: login form is the only entry point; everything behind it is a black box.

**Files:**
- `routes/auth.py` (update) — add login rate limiting (e.g., 5 attempts per IP per 10 minutes via Flask-Limiter)
- `app.py` (update) — enforce CSRF protection on all POST routes (Flask-WTF or equivalent); set secure session cookie flags (`HttpOnly`, `Secure`, `SameSite=Strict`)
- `config/loader.py` (update) — assert no secrets present in config.yaml at load time; secrets must come from env vars only
- `routes/onboarding.py` (update) — validate that no raw API response data is passed through to the client-facing status endpoint; strip internal error details from user-facing messages
