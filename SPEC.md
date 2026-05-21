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
>
> Each milestone opens with a **Human Prerequisites** section — items Levi must supply or decide before agents can begin that milestone. Nothing in that section should be left to the agent to assume.

---

### Milestone 1 — Foundation

**Goal:** A runnable, authenticated Python web app with a loaded config system and a documented server inventory. Every downstream milestone depends on this landing first.

**Exit criterion:** `python app.py` starts a password-protected server; `config/config.yaml` loads and validates correctly; `pytest` runs and the auth tests pass; all required env vars are documented in `.env.example`.

#### Human Prerequisites

Before any agent starts Milestone 1, Levi must provide:

1. **Cloudways server inventory** — For each server (shared non-ecommerce, ecommerce demo, any existing ecommerce client servers): the Cloudways server ID, the server's public IP address, and a human-readable name. These seed `config/config.yaml` directly.
2. **Admin credentials decision** — Confirm that the generator app's login username and password will come from environment variables (`ADMIN_USERNAME`, `ADMIN_PASSWORD`). If a different auth scheme is preferred (e.g., a secrets manager), say so now — changing this after M1 is messy.
3. **Python version** — Confirm target Python version (3.11+ assumed; override if needed).
4. **Web framework confirmation** — Flask is assumed. Override to FastAPI if preferred. This decision propagates through every route file.

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
>
> **Mitigation:** Model `servers` as a typed list with a `type` field (`shared_standard`, `ecommerce_demo`, `dedicated_ecommerce`). Adding a new ecommerce client server later = appending one list entry with no schema change. Use a required `id` field on each entry so other config sections (and the orchestrator) can reference servers by ID rather than by index.

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
>
> **Mitigation:** `config/loader.py` asserts at startup that `ADMIN_USERNAME` and `ADMIN_PASSWORD` are present in the environment and raises a hard error if they are missing. The auth route reads these env vars directly and never touches config.yaml. Add a comment in config.yaml explicitly stating it must not contain secrets.

---

### Milestone 2 — External API Clients & Form Layer

**Goal:** All four external service clients are built and unit-tested in isolation. Form data models are defined. The onboarding form HTML is built. These six streams have zero file overlap and can ship in any order or fully in parallel.

**Exit criterion:** All unit tests pass against mocked HTTP responses. Form renders with all fields from the spec and enforces client-side required-field validation.

**Dependency:** Milestone 1 complete (config loader available to import).

#### Human Prerequisites

Before any agent starts Milestone 2, Levi must provide:

1. **Cloudways API key** — Required for Stream 2A. Levi must generate this in the Cloudways dashboard and store it in `.env` locally.
2. **Cloudflare API token** — Required for Stream 2B. Must have `Zone:Read` and `DNS:Edit` permissions scoped to all relevant zones. Levi must create this in the Cloudflare dashboard.
3. **Email provider decision** — Required for Stream 2D. Options: a transactional SMTP service (e.g., Postmark, Mailgun, or Gmail SMTP). Provide the SMTP host, port, and credentials. The from-address must also be decided.
4. **Starter kit GitHub repo URL** — Required for Stream 2C. The repo (containing the Divi child theme, mu-plugin, and plugin list) must exist and have its URL ready. Even a skeleton repo with the correct structure is sufficient to unblock the SSH runner tests.
5. **Form field sign-off** — Required for Stream 2F. Review the "Onboarding Form — Inputs" section of this spec and confirm the field list is complete. Any missing fields discovered after M2 ships require retroactive changes across the models, form HTML, and orchestrator.

---

#### Stream 2A — Cloudways API Client

Low-level HTTP client wrapping the Cloudways API. Exposes only the primitives consumed by Stream 3A.

**Files:**
- `integrations/cloudways.py` — `create_application()`, `poll_until_ready()`, `attach_domain()`, `provision_ssl()`, `get_server_ip()`
- `tests/unit/test_cloudways_client.py`

> **Risk:** Cloudways app creation is **asynchronous** — the API returns an operation ID and you must poll until the app status is `running`. This is a common gotcha. `poll_until_ready()` must be a first-class method with a configurable timeout and backoff, not an afterthought. Retrofitting polling later will require rewriting the orchestrator.
>
> **Mitigation:** Implement `poll_until_ready(operation_id, timeout_seconds=600, initial_delay=5, max_delay=30)` from day one using exponential backoff. It raises a typed `ProvisioningTimeoutError` (not a generic exception) if the timeout is reached, so the orchestrator can handle it distinctly. Log each poll attempt with elapsed time — this data will be invaluable when debugging slow provisioning in production.

---

#### Stream 2B — Cloudflare API Client

Low-level HTTP client wrapping the Cloudflare API. Zone lookup is dynamic — do not require a zone ID in the form.

**Files:**
- `integrations/cloudflare.py` — `get_zone_id_for_domain()`, `create_a_record()`, `delete_a_record()`
- `tests/unit/test_cloudflare_client.py`

> **Risk:** Cloudflare requires the **zone ID**, not the domain name, for record management. `get_zone_id_for_domain()` must look it up from the Cloudflare account using the API token — this implies the token must have `Zone:Read` permission in addition to `DNS:Edit`. Document required token permissions in `.env.example`.
>
> **Mitigation:** `get_zone_id_for_domain()` queries `/zones?name=<apex_domain>` and raises a typed `ZoneNotFoundError` with a human-readable message ("Domain not found in Cloudflare account — has the client pointed their nameservers to Cloudflare yet?") if no zone is returned. This surfaces the problem at Step 7 with a clear action, rather than a cryptic 404. Cache the zone ID for the duration of the provisioning job (no re-lookup needed for `create_a_record`).

---

#### Stream 2C — SSH & WP-CLI Runner

Low-level primitive for executing shell commands over SSH. WP-CLI-specific logic lives in Milestone 3, not here — this module is a general-purpose runner.

**Files:**
- `provisioning/ssh_runner.py` — `SSHRunner` class: connect, `run(command)` → `(stdout, stderr, exit_code)`, `upload_file()`, disconnect; configurable timeout and retry
- `tests/unit/test_ssh_runner.py` — mock paramiko; test success path, non-zero exit code, timeout, connection refused

> **Risk:** This is the **highest-failure-probability component** in the system. WP-CLI over SSH can fail silently, return misleading exit codes, or hang indefinitely. Requirements: always capture stderr separately; treat any non-zero exit code as a hard error with stderr surfaced to the caller; enforce a per-command timeout; retry on transient connection drops (not on WP-CLI errors). Getting this wrong produces a provisioning pipeline that appears to succeed but produces broken sites.
>
> **Mitigation:** `SSHRunner.run()` returns a `CommandResult(stdout, stderr, exit_code)` named tuple and raises `SSHCommandError(command, stderr)` on any non-zero exit code — stderr is always included in the exception message so the orchestrator can surface it. A per-command timeout (default 120s, configurable per call) is enforced via paramiko's channel deadline; a hung command raises `SSHTimeoutError`. Transient connection errors (`socket.timeout`, `EOFError`) trigger exactly one automatic retry after a 5-second delay. WP-CLI logical errors (non-zero exit) are never retried — retrying a failed `wp core install` would produce undefined state. All commands are logged at DEBUG level with full stdout/stderr for post-mortem debugging.

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

#### Human Prerequisites

Before any agent starts Milestone 3, Levi must provide:

1. **Starter kit repo — populated and accessible.** The GitHub repo must contain: the Divi child theme directory, the mu-plugin directory, the standard plugin list (as a text file or install script), and the starter database export (`starter.sql`). A skeleton repo is not sufficient here — the actual files must be present because Stream 3B tests against their structure.
2. **SSH deploy key installed on the Cloudways server.** The server's SSH public key (or a dedicated deploy key) must be added to the starter kit GitHub repo as a deploy key with read access. This is a manual step in both GitHub and Cloudways. Agents cannot do this.
3. **Divi option key research completed.** Before Stream 3B can implement `step5_configure_site`, the exact WordPress option keys Divi uses for brand colors and template selection must be documented. Levi (or an agent given SSH access to a live Divi install) must run `wp option list --search="et_*" --format=json` against a configured Divi site and document the results in `divi_option_keys.md`. Stream 3B Step 5 is **blocked** until this file exists.
4. **Test Cloudways app for SSH smoke-testing.** A throwaway app on the shared server must be available so Stream 3B can be manually smoke-tested over a real SSH connection before the orchestrator wires it up.

---

#### Stream 3A — Cloudways Steps (Steps 1 & 6)

**Files:**
- `provisioning/steps_cloudways.py` — `step1_create_application(form, config)`: creates app on correct server (non-ecommerce shared server or new dedicated server based on ecommerce flag), polls until ready, returns app credentials and server IP; `step6_attach_domain_and_ssl(app_id, domain)`: attaches domain, triggers SSL provisioning
- `tests/unit/test_steps_cloudways.py`

> **Risk (critical sequencing bug in the spec):** Step 6 (SSL provisioning) is listed before Step 7 (Cloudflare DNS). This is backwards: Cloudways SSL provisioning via Let's Encrypt requires the domain's DNS to already resolve to the server. Running Step 6 before Step 7 will cause SSL provisioning to fail.
>
> **Mitigation:** Reorder the pipeline to `1 → 2 → 3 → 4 → 5 → 7 → [DNS wait] → 6 → 8`. After Step 7 creates the Cloudflare A record, the orchestrator polls an external DNS resolver (Cloudflare's `1.1.1.1` via DNS-over-HTTPS) until the domain resolves to the correct server IP, up to a configurable timeout (default 10 minutes). Only then does it call Step 6. A "Waiting for DNS propagation" status label is shown in the UI during this wait. The Onboarding Flow diagram in this spec must be updated to reflect the corrected order when Step 6/7 are implemented — do not silently fix it in code only.

---

#### Stream 3B — WordPress Install Steps (Steps 2, 3, 4 & 5)

**Files:**
- `provisioning/steps_wordpress.py` — `step2_clone_starter_kit(ssh, app_path, repo_url)`: SSH clone of starter kit (Divi child theme + mu-plugin + plugin list); `step3_install_wp_core(ssh, app_path)`: WP-CLI core install; `step4_import_starter_db(ssh, app_path, db_file)`: WP-CLI DB import; `step5_configure_site(ssh, app_path, form)`: WP-CLI option/meta writes for all client-specific values
- `tests/unit/test_steps_wordpress.py`

> **Risk (Divi data format):** `step5_configure_site` must write Divi brand colors and template selection via `wp option update` and `wp post meta update`. Divi stores this data in serialized PHP arrays under specific option keys (e.g., `et_divi`, theme customizer options). The exact key names and value formats must be researched and validated against the actual Divi version in use **before** implementing Step 5 — getting them wrong produces a site that appears provisioned but renders with no styling.
>
> **Mitigation:** This is blocked on the human prerequisite (Divi option key research above). Once `divi_option_keys.md` exists, `step5_configure_site` maps each `OnboardingForm` field to its documented option key. The mapping is defined as a constant dict at the top of `steps_wordpress.py` (not scattered through the function) so it's easy to update when Divi releases a breaking change. After Step 5 runs, a validation pass reads the options back via `wp option get` and asserts the written values match — if they don't, the step fails loudly rather than silently producing a misconfigured site.

> **Risk (idempotency):** If the pipeline fails at Step 4 or 5 and is retried, `step3_install_wp_core` will be called against an existing WP install, which causes WP-CLI to error.
>
> **Mitigation:** `step3_install_wp_core` runs `wp core is-installed` first. Exit code 0 means WP is already installed — skip Steps 3 and 4 entirely and log a `WARNING: WordPress already installed, skipping core install and DB import`. This makes the pipeline safely retryable from any step without manual cleanup.

> **Risk (SSH key access):** Step 2 clones from GitHub over SSH. The Cloudways server must have an SSH deploy key registered on the starter kit repo. This is an infrastructure prerequisite — document it in the README and fail loudly if the clone fails due to auth rather than silently continuing.
>
> **Mitigation:** Add a `preflight_check(ssh)` function called before Step 1 (not as a numbered provisioning step, but as a pre-run gate) that verifies: (a) SSH connectivity, (b) WP-CLI is installed and callable, (c) GitHub SSH access is functional (`ssh -T git@github.com` returns exit code 1 with "successfully authenticated" in stderr — this is GitHub's expected behavior). If any preflight check fails, the entire job aborts immediately with a specific error message before any Cloudways app is created. This prevents orphaned apps that would need manual cleanup.

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

#### Human Prerequisites

Before any agent starts Milestone 4, Levi must provide:

1. **Visual sign-off on the form UI (Stream 2F output).** The form must be reviewed and approved by Levi before it is wired to the backend. Layout or field changes after wiring create rework across both the route and the data models.
2. **Background job model confirmation.** `threading.Thread` is assumed for v1 (simple, no infrastructure dependency). If Levi anticipates running multiple concurrent provisioning jobs or deploying the generator on multiple workers, confirm before this milestone starts — switching to Celery after the orchestrator is built requires rewriting both `orchestrator.py` and the routes.
3. **A live dev environment for end-to-end testing.** A real Cloudways server and a real Cloudflare zone (even a throwaway domain) must be available so the full pipeline can be triggered and observed. Unit tests alone cannot validate the orchestrator — a real run is required for the exit criterion.

---

#### Stream 4A — Orchestrator

Calls steps 1–8 in the correct order (per the sequencing fix in Stream 3A). Manages partial failure: records which step failed, wraps the error with context, and exposes job status for polling. Designed for future idempotent retry.

**Files:**
- `orchestrator.py` — `ProvisioningJob` dataclass (status, current\_step, error, result\_url); `run_provisioning(form, config)` executes steps sequentially, updating job state after each; jobs stored in a simple in-memory dict keyed by job ID (sufficient for v1 single-operator usage)
- `tests/unit/test_orchestrator.py` — happy path completes all 8 steps; failure at step N records step N and error; correct step order enforced

> **Risk (blocking HTTP):** Provisioning takes ~5–10 minutes. The orchestrator **must not block the HTTP request**. It must run in a background thread (or asyncio task) and return a job ID immediately. The form route starts the job, returns the ID, and the UI polls a `/status/<job_id>` endpoint. Choose the threading model (Python `threading.Thread` is simplest for v1; switch to Celery only if multi-operator use is needed) and commit to it here — changing it later requires rewriting both the orchestrator and the routes.
>
> **Mitigation:** The `POST /provision` route calls `threading.Thread(target=run_provisioning, args=(job, form, config), daemon=True).start()` and returns `{"job_id": "..."}` within milliseconds. The `ProvisioningJob` object is created before the thread starts, stored in the in-memory job registry, and updated by the thread at each step transition — no shared mutable state beyond the single job object, so no locking is needed. Document the known limitation explicitly in the code and README: if the process restarts, in-flight jobs are lost and the partially-provisioned Cloudways app must be cleaned up manually. This is acceptable for v1 single-operator use.

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

#### Human Prerequisites

Before any agent starts Milestone 5, Levi must provide:

1. **Dedicated test Cloudways app + Cloudflare zone for integration tests.** A throwaway domain (e.g., a cheap `.info` or a subdomain Levi controls) must be registered in Cloudflare and pointed at the shared server. Integration tests will create and destroy apps against this zone on every run — it must not be a real client zone.
2. **Decision: where does the generator app itself live?** The Python web app needs a home — a Cloudways app on the shared server, or its own server. This determines the `deploy.yml` target and must be decided before Stream 5A is written.
3. **GitHub Actions secrets configured.** All secrets from `.env.example` must be added to the GitHub repo's Actions secrets (`CLOUDWAYS_API_KEY`, `CLOUDFLARE_API_TOKEN`, SMTP credentials, `ADMIN_USERNAME`, `ADMIN_PASSWORD`) before CI can pass on a push.
4. **GitHub repository created and Actions enabled.** If the repo doesn't exist yet on GitHub, it must be created and pushed before Stream 5A can be tested.

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
