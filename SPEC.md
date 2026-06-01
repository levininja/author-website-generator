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
- DNS transfers during onboarding can be done by Levi manually for now; later, give the user a UI for this
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
[ Step 1 ] Cloudways API → create new Application on the shared non-ecommerce server
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
[ Step 6 ] Cloudflare API → create A record pointing client domain → server IP
        ↓
[ Wait  ] Poll DNS propagation until domain resolves to server IP (up to 10 min)
        ↓
[ Step 7 ] Cloudways API → attach client's domain to the new app + provision SSL
        ↓
[ Step 8 ] Email → send client their WordPress admin URL and credentials
        ↓
Form UI → show success message with site URL
        ↓
Live site ✓
```

**Expected provisioning time:** ~5–10 minutes (most time: DNS propagation + SSL provisioning).

---

## Provisioning Steps Reference

| # | Step | Owner module | Description | Key notes |
|---|------|-------------|-------------|-----------|
| 1 | Create Cloudways app | `steps_cloudways.py` | Create new Application on the shared non-ecommerce server | Async — must poll until app status is `running`; raises `ProvisioningTimeoutError` on timeout |
| 2 | Clone starter kit | `steps_wordpress.py` | SSH into server, clone Divi child theme + mu-plugin + plugin list repo into new app folder | Fails loudly on SSH auth error; requires deploy key on GitHub repo |
| 3 | Install WordPress core | `steps_wordpress.py` | WP-CLI `core install` | Idempotency guard: skips if WP already installed |
| 4 | Import starter database | `steps_wordpress.py` | WP-CLI DB import — pre-built Divi layouts and standard pages (Home, About, Books, Contact) | Skipped if Step 3 was skipped (WP already installed) |
| 5 | Configure site | `steps_wordpress.py` | WP-CLI writes all client-specific values: site name, tagline, bio, colors, logo/headshot, social links, Kit newsletter form, book portfolio, selected Divi template | Validates written values back via `wp option get`; fails loudly on mismatch |
| 6 | Create DNS record | `steps_dns_email.py` | Cloudflare API — create A record pointing client domain → server IP | Looks up zone ID dynamically; raises `ZoneNotFoundError` if domain not in Cloudflare |
| — | DNS wait | `orchestrator.py` | Poll `1.1.1.1` (DNS-over-HTTPS) until domain resolves to server IP | Configurable timeout (default 10 min); UI shows "Waiting for DNS propagation" |
| 7 | Attach domain + SSL | `steps_cloudways.py` | Cloudways API — attach client domain to app and trigger Let's Encrypt SSL provisioning | Must run after DNS propagates; Let's Encrypt requires domain to resolve first |
| 8 | Send welcome email | `steps_dns_email.py` | Email client their WordPress admin URL and credentials | SMTP credentials from env vars |

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
- Ecommerce support (dedicated server routing, ecommerce flag on form) — deferred to Milestone 6

---

## Open Questions / Decisions Deferred

- v2 deployment spec: what exactly should propagate to client site databases on deploy?
- Client self-service form: security model, access control, whether to build at all
- Email hosting provider (Google Workspace reseller, Zoho, Fastmail, other?)
- Billing/invoicing integration
- Maintenance workflow (WP-CLI update scripts, ManageWP, hosting-native, other?)
