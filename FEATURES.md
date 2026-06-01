# Author Website Generator — Feature List

Two lists: **Feature List** (priority order) and **Backlog** (unordered).

ID prefixes: `F` = feature, `T` = task, `R` = research task, `B` = backlog item.

---

## Feature List

---

### R001 — Document Divi option keys for site configuration

**Type:** Research Task
**As** a developer on this project, I need a reference document of how Divi stores configuration in WordPress so that the site configuration step can be implemented correctly and maintainably.
**Deliverable:** `divi_option_keys.md`

- Run `wp option list --search="et_*" --format=json` against a configured Divi install (requires SSH access to a live Divi site)
- Document every relevant WP option key Divi uses for brand colors and template selection
- Document the exact value format each key expects (Divi stores data as serialized PHP arrays — format matters)
- Include recommended mapping from each `OnboardingForm` field to its corresponding option key
- Note any version-specific caveats for the Divi version in use
- Blocks F004 (Divi template picker) and the site configuration step within F005

---

### F001 — Fill out the client onboarding form

**Type:** Feature
**As** an end user, I can fill out a single-page form with all client details so I have everything needed to provision a site.

- Form is auth-gated — only accessible when logged in (`GET /`)
- **Client Identity fields:** author name (as it appears publicly), author email, WordPress admin username, WordPress admin password
- **Site Identity fields:** site/domain name (e.g. `janedoeauthor.com`), site tagline / author bio one-liner, author short bio (paragraph, shown in About section), author long bio (optional, for full About page)
- **Genre & Branding fields:** genre(s) — multi-select or free text; primary brand color (hex); secondary brand color (hex)
- **Social & Marketing fields:** newsletter signup link or Kit form ID; Twitter/X, Instagram, Facebook, TikTok, YouTube (all optional)
- **Domain & DNS fields:** domain name (used for Cloudways app config and Cloudflare DNS record); checkbox confirming nameservers are already pointed to Cloudflare
- Client-side required-field validation before submission is allowed
- Hex color validation and URL validation on social link fields
- Files: `models/onboarding.py` (Pydantic models: `BookEntry`, `SocialLinks`, `OnboardingForm`), `tests/unit/test_onboarding_models.py`, `templates/onboarding.html`, `static/css/form.css`, `static/js/form.js`
- Tests: valid input passes, required fields enforced, hex color validation, URL validation on social links
- **Human prerequisite:** Levi must sign off on the field list before this is built — any missing fields discovered after this ships require retroactive changes across models, form HTML, and orchestrator

---

### F002 — Build the client's book portfolio in the form

**Type:** Feature
**As** an end user, I can add multiple books to the form and add or remove book entries dynamically without reloading the page.

- Each book entry: title, cover image upload, description, buy links
- Add/remove rows handled client-side by `static/js/form.js` — no page reload
- Book entries modeled as a list of `BookEntry` in `OnboardingForm`
- Book data gets written to the WordPress site in the site configuration step (Step 5) of F005

---

### F003 — Upload the author's headshot in the form

**Type:** Feature
**As** an end user, I can upload an image file directly in the form so it gets placed on the generated site's About section automatically.

- Image upload field in the onboarding form
- Headshot applied to the site via WP-CLI in the site configuration step (Step 5) of F005

---

### F004 — Select a Divi template with visual preview

**Type:** Feature
**As** an end user, I can browse available Divi templates, click each one to see a screenshot of what a site built with that template looks like, and select the one I want applied to the provisioned site.

- Original spec had this as a plain dropdown — this feature upgrades it to a visual picker (clickable thumbnails with screenshots)
- Selected template value included in `OnboardingForm` and passed to the site configuration step (Step 5) of F005
- Template selection written via `wp option update` or `wp post meta update` using the key names documented in R001
- **Blocked by R001** — the WP-CLI write for template selection cannot be implemented without the Divi option key research

---

### F005 — Submit the form and watch the site provision in real time

**Type:** Feature
**As** an end user, after submitting the form I can watch labeled provisioning steps update live so I know what's happening and where the process is at.

**Provisioning pipeline (corrected order — see sequencing note):**

- **Step 1:** Cloudways API → create new application on the shared non-ecommerce server
- **Step 2:** SSH → clone starter kit repo into new app folder (starter kit = custom Divi child theme + mu-plugin + standard plugin list)
- **Step 3:** WP-CLI → install WordPress core
- **Step 4:** WP-CLI → import starter database (pre-built Divi layouts, standard pages: Home, About, Books, Contact)
- **Step 5:** WP-CLI → set all client-specific values (site name, tagline, author bio, colors, headshot, social links, Kit newsletter form, book portfolio, selected Divi template)
- **Step 6:** Cloudflare API → create A record pointing client domain to server IP
- **Step 7 (DNS wait):** Poll Cloudflare's `1.1.1.1` DNS-over-HTTPS until domain resolves to correct server IP; configurable timeout, default 10 minutes; show "Waiting for DNS propagation" label in UI during wait
- **Step 8:** Cloudways API → attach client's domain to the new app + provision SSL
- **Step 9:** Email → send client WordPress admin URL and credentials (see F006)
- **Step 10:** Show success with site URL (see F007)

> **Sequencing note — correction from original spec:** SSL provisioning (Step 8) must come after DNS resolves (Steps 6+7). The original spec had SSL before DNS, which causes Let's Encrypt to fail because the domain doesn't yet resolve to the server. Corrected order: 1 → 2 → 3 → 4 → 5 → 6 → 7(DNS wait) → 8 → 9. The Onboarding Flow diagram in SPEC.md must be updated to reflect this when the step is implemented.

**Preflight check (runs before Step 1, not a numbered provisioning step):**
- Verify SSH connectivity to the server
- Verify WP-CLI is installed and callable on the server
- Verify GitHub SSH access (`ssh -T git@github.com` returns exit code 1 with "successfully authenticated" in stderr — this is GitHub's expected behavior, not an error)
- If any preflight check fails, abort the entire job before any Cloudways app is created — prevents orphaned apps that need manual cleanup
- Surface a specific error message identifying which preflight check failed

**Background job model:**
- `POST /provision` starts a background thread and returns `{"job_id": "..."}` within milliseconds — the HTTP request does not block for the ~5–10 minute provisioning duration
- `threading.Thread` for v1 (simple, no infrastructure dependency); switch to Celery only if multi-operator use is needed — confirm this decision before starting, as changing it after the fact requires rewriting both the orchestrator and the routes
- `ProvisioningJob` dataclass fields: status, current_step, error, result_url
- Jobs stored in an in-memory dict keyed by job ID
- Known limitation (must be documented in code and README): if the process restarts, in-flight jobs are lost and the partially-provisioned Cloudways app must be cleaned up manually — acceptable for v1 single-operator use

**Cloudways API client:**
- Methods: `create_application()`, `poll_until_ready()`, `attach_domain()`, `provision_ssl()`, `get_server_ip()`
- App creation is asynchronous — API returns an operation ID; must poll until app status is `running`
- `poll_until_ready(operation_id, timeout_seconds=600, initial_delay=5, max_delay=30)` with exponential backoff
- Raises typed `ProvisioningTimeoutError` on timeout (not a generic exception) so the orchestrator can handle it distinctly
- Log each poll attempt with elapsed time — useful for debugging slow provisioning
- Files: `integrations/cloudways.py`, `tests/unit/test_cloudways_client.py`

**Cloudflare API client:**
- Methods: `get_zone_id_for_domain()`, `create_a_record()`, `delete_a_record()`
- Zone lookup is dynamic — do not require a zone ID in the form; look it up from the API using the domain name
- API token must have `Zone:Read` AND `DNS:Edit` permissions — document required permissions in `.env.example`
- `get_zone_id_for_domain()` queries `/zones?name=<apex_domain>`; raises typed `ZoneNotFoundError` with human-readable message ("Domain not found in Cloudflare account — has the client pointed their nameservers to Cloudflare yet?") if zone not found
- Cache zone ID for the duration of the provisioning job — no re-lookup needed for subsequent calls
- Files: `integrations/cloudflare.py`, `tests/unit/test_cloudflare_client.py`

**SSH & WP-CLI runner:**
- `SSHRunner` class: connect, `run(command)` → `CommandResult(stdout, stderr, exit_code)`, `upload_file()`, disconnect; configurable timeout and retry
- `run()` raises `SSHCommandError(command, stderr)` on any non-zero exit code — stderr always included in the exception message
- Per-command timeout (default 120s, configurable per call) enforced via paramiko channel deadline; hung command raises `SSHTimeoutError`
- Transient connection errors (`socket.timeout`, `EOFError`) trigger exactly one automatic retry after a 5-second delay
- WP-CLI logical errors (non-zero exit) are never retried — retrying a failed `wp core install` would produce undefined state
- All commands logged at DEBUG level with full stdout/stderr for post-mortem debugging
- Files: `provisioning/ssh_runner.py`, `tests/unit/test_ssh_runner.py`
- Tests: mock paramiko; cover success path, non-zero exit code, timeout, connection refused

**Step 2 — clone starter kit:**
- Clone via SSH (not HTTPS) — requires a deploy key registered on both the Cloudways server and the GitHub repo
- Fail loudly on auth failure — do not silently continue
- Human prerequisite: starter kit repo must be populated with actual files (Divi child theme directory, mu-plugin directory, plugin list file/install script, `starter.sql`); SSH deploy key must be installed on both GitHub and Cloudways before this step can run

**Step 3 — WP core install (idempotency):**
- Run `wp core is-installed` first; if exit code 0 (already installed), skip Steps 3 and 4 entirely and log a WARNING
- Makes the pipeline safely retryable from any step without manual cleanup

**Step 5 — configure site:**
- Mapping of `OnboardingForm` fields to Divi option keys defined as a constant dict at the top of `steps_wordpress.py` (not scattered through the function) — easy to update when Divi releases a breaking change
- After Step 5 runs, a validation pass reads the options back via `wp option get` and asserts the written values match — fails loudly rather than silently producing a misconfigured site
- **Blocked by R001** for the template selection and color mapping portions

**Orchestrator:**
- `run_provisioning(form, config)` executes steps sequentially, updating job state after each
- Records which step failed, wraps error with context, exposes job status for polling
- Files: `orchestrator.py`, `tests/unit/test_orchestrator.py`
- Tests: happy path completes all steps; failure at step N records step N and error; correct step order enforced

**Status UI:**
- Labeled steps with active / complete / error states
- `GET /status/<job_id>` returns job state as JSON
- `static/js/status.js` polls every 3 seconds
- During DNS wait: shows "Waiting for DNS propagation" label
- Files: `routes/onboarding.py`, `templates/status.html`, `static/js/status.js`
- `app.py` (update) — register the new onboarding blueprint/routes; `app.py` itself was created in M1 and is not re-created here

**Human prerequisites before starting this feature:**
- Cloudways API key (generate in dashboard, store in `.env`)
- Cloudflare API token with Zone:Read + DNS:Edit, documented in `.env.example`
- Email provider decision: SMTP host, port, credentials, from-address (options: Postmark, Mailgun, Gmail SMTP)
- Starter kit GitHub repo URL (must exist with correct structure — even a skeleton repo is sufficient to unblock SSH runner tests)
- Visual sign-off on form UI before backend is wired — layout or field changes after wiring create rework across route and data models
- Background job model confirmation (threading.Thread assumed for v1)
- Live dev environment for end-to-end testing: real Cloudways server + real Cloudflare zone (throwaway domain is fine)
- Test Cloudways app available for SSH smoke-testing before orchestrator wires up

---

### F006 — Client automatically receives a welcome email

**Type:** Feature
**As** a client author, I receive an email with my WordPress admin URL and login credentials as soon as my site is provisioned, without my account manager having to send it manually.

- Triggered as Step 9 of the provisioning pipeline in F005
- `send_welcome_email(author_email, admin_url, username, password)`
- SMTP-based; all credentials from env vars
- Files: `integrations/email_sender.py`, `templates/email/welcome.html`, `tests/unit/test_email_sender.py`

---

### F007 — Get a clear result — site URL on success, specific error on failure

**Type:** Feature
**As** an end user, when provisioning completes I see the live site URL, and if it fails I see exactly which step failed with a human-readable error message so I know what to fix.

- On success: site URL displayed in the status UI
- On failure: step name + specific error message (e.g. "Domain not found in Cloudflare — has the client pointed their nameservers yet?") + dismiss button
- No internal API response details or stack traces exposed to the client-facing status endpoint — strip internal error details; surface only human-readable messages
- Error display persists until the user dismisses it via X or resubmits

---

### F008 — Provision an ecommerce site on a dedicated server

**Type:** Feature
**As** an end user, I can toggle an "ecommerce site" flag on the form so the new site gets provisioned on a dedicated server instead of the shared one.

- "Ecommerce site?" yes/no toggle added to the form in a new Site Type section
- `is_ecommerce: bool` field added to `OnboardingForm`
- `step1_create_application`: if `form.is_ecommerce` is true, look up the dedicated ecommerce server from config by type; provision there instead of the shared server
- If dedicated ecommerce server entry is missing from config: raise typed `ServerNotConfiguredError` immediately before any Cloudways app is created — never silently fall back to the shared server
- Servers modeled in `config/config.yaml` as a typed list with a `type` field (`shared_standard`, `ecommerce_demo`, `dedicated_ecommerce`) and a required `id` field — adding a new ecommerce client server later = appending one list entry with no schema change (this schema was designed for extensibility in M1)
- Files: `config/config.yaml` (update), `models/onboarding.py` (update), `templates/onboarding.html` (update), `static/js/form.js` (update), `provisioning/steps_cloudways.py` (update), `tests/unit/test_steps_cloudways.py` (update)
- Tests: assert non-ecommerce jobs go to shared server; assert ecommerce jobs go to dedicated server; assert missing server config raises `ServerNotConfiguredError`
- **Human prerequisites:** ecommerce demo server inventory (Cloudways server ID, public IP, human-readable name); decision on whether Levi manually pre-creates the dedicated server first (then pastes its ID into config) or the generator creates it via the Cloudways API — this determines whether `step1_create_application` needs server-creation logic or just server-selection logic; Divi developer license must be in place before the first real ecommerce client site is provisioned (single-site license covers the demo only)

---

### T001 — Provision the ecommerce demo site

**Type:** Task
**As** an end user, I can point prospective clients to a live example of an ecommerce author site so they can see what they'd be getting.
**Deliverable:** A live ecommerce demo site URL, documented in the README with its Cloudways server ID and the process for adding new dedicated ecommerce client servers to `config/config.yaml`.

- Manual task — use the working generator tool to provision the demo site; no new code required
- Ecommerce demo server is a separate Cloudways server from the shared non-ecommerce server (`type: ecommerce_demo` in config)
- The demo site also lives on the shared non-ecommerce server's example slot for non-ecommerce reference
- **Depends on F008**

---

### F009 — Log in to the generator tool (security hardening)

**Type:** Feature
**As** an end user, I can sign in with a username and password, and the tool locks me out after repeated failed attempts so unauthorized users can't brute-force access.

- Basic username/password login and session management already implemented in M1 — items below are the remaining security hardening
- Login rate limiting: 5 attempts per IP per 10 minutes (Flask-Limiter)
- CSRF protection on all POST routes (Flask-WTF or equivalent)
- Secure session cookie flags: `HttpOnly`, `Secure`, `SameSite=Strict`
- Credentials come from env vars only (`ADMIN_USERNAME`, `ADMIN_PASSWORD`) — never from `config.yaml` (already enforced in M1; `config/loader.py` hard-errors at startup if env vars are missing)
- Files: `routes/auth.py` (rate limiting), `app.py` (CSRF + cookie flags)

---

## Backlog

---

### B001 — Automated deployments for the generator app

**Type:** Feature
**As** a developer on this project, I can merge to `main` and have the generator app deploy automatically so I don't have to manually SSH into the server to push updates.
**Deliverable:** `.github/workflows/ci.yml` and `.github/workflows/deploy.yml`

- CI on every push to any branch: install deps, lint (flake8/ruff), type-check (mypy), run unit test suite
- Deploy on merge to `main`: push to `production` branch, trigger Cloudways Git deployment via API
- Cloudways Git integration: each server/app configured to pull from `production` branch on deploy trigger
- **Human prerequisites:** decision on where the generator app itself lives (Cloudways app on shared server, or its own server — determines the deploy.yml target); GitHub Actions secrets configured (`CLOUDWAYS_API_KEY`, `CLOUDFLARE_API_TOKEN`, SMTP credentials, `ADMIN_USERNAME`, `ADMIN_PASSWORD`); GitHub repo created with Actions enabled

---

### B002 — Automated regression test suite

**Type:** Task
**As** a client, I want confidence that when new features are rolled out the existing provisioning workflow still works end-to-end, so that my site isn't broken by an update.
**Deliverable:** `tests/integration/` — a suite that provisions and tears down a real test app against a dedicated throwaway environment, runnable before any release.

- Tests hit real APIs — not run on every push; run manually before releases or on a nightly schedule
- `tests/integration/conftest.py` — shared fixtures: test Cloudways app credentials, test Cloudflare zone, cleanup teardown
- `tests/integration/test_full_provision.py` — full provisioning flow with real API calls; verifies site URL returns HTTP 200 after completion; cleans up the test app on teardown
- **Human prerequisite:** dedicated throwaway Cloudways app + Cloudflare zone reserved exclusively for testing — must not be a real client zone
