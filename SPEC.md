# Author Website Generator — Product Spec

Related documents: [README](README.md) · [Feature list](FEATURES.md) · [Product decisions](DECISIONS.md) · [Provisioning pipeline](PIPELINE.md)

---

## The Product Definition

The product is an engineering-grade, managed website service built exclusively for authors. It replaces manual, one-off contractor builds with standardized, high-performance WordPress platforms. The system functions as a productized service—balancing affordability with technical stability—while guaranteeing authors retain full autonomy, true site portability, and domain ownership.

## Common Terms

- **AWG:** The Author Website Generator application itself. AWG contains the public product and marketing pages, onboarding experience, website-generation workflow, previews, and future account and service-management functionality. It is separate from the author websites it generates.
- **End user:** A person using AWG to create an author website. An end user does not need an account before using onboarding or generating a website.
- **User account:** A future AWG account used to associate an end user with generated websites and account-management functionality. Account creation is not part of onboarding and is not a prerequisite for generation.
- **User ID:** AWG's internal identifier for a user account. It is a randomly generated, non-sequential UUID and is not an email address or other personally identifiable information.
- **Onboarding:** The public, single-page form where an end user supplies author, book, branding, and related website metadata and clicks the button to generate an author website. In this codebase, onboarding does not mean account registration, payment setup, or an internal administrative process.
- **Website generation:** Transforming validated onboarding data into the complete website code and assets needed for an AWG preview. Generation does not create production infrastructure or deploy a live WordPress site.
- **Generated-site preview:** The generated website as viewed inside AWG at `/sites/<site_id>`. A preview is not a production WordPress installation.
- **Production author website:** The independent WordPress/PHP website created for an author on production hosting. It is separate from AWG and from the generated-site preview.
- **Provisioning:** Creating and configuring the production infrastructure and WordPress installation for an author website, including hosting, WordPress setup, DNS, and SSL.
- **Provisioning pipeline:** The ordered, automated production-provisioning workflow documented in [PIPELINE.md](PIPELINE.md). The pipeline is distinct from website generation.
- **Deployment:** Releasing AWG application code or updated shared WordPress code to its runtime environment. Deployment is distinct from generating a preview and from provisioning a new production author website.


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
Python / Django 5.2 LTS

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

- AWG landing and marketing pages are public-facing.
- The onboarding form and website-generation flow are public. An end user can generate a website before creating an account. See [Product decisions](DECISIONS.md#users-can-generate-a-website-before-creating-an-account).
- Account creation, authentication, and associating a generated website with an account happen after generation and will be implemented as separate features.
- Future account-management and administrative functionality must require authentication and appropriate authorization.
- Public endpoints are limited to the product flows that explicitly require them; internal management and provisioning endpoints are not exposed to unauthenticated users.

### Integrations

- **Newsletter:** Kit (ConvertKit) — v1.
- **BookFunnel, StoryOrigin, BetaBooks, BetaReader.io, Plottr:** Solve later.
- **Substack:** Solve later.
- **Billing / Client Management:** Solve later. Users get a 7-day free trial after site creation; payment required after that to keep the site live. See [Product decisions](DECISIONS.md#users-get-a-7-day-free-trial).
- **Analytics & Feedback:** Solve later.
- **Email Hosting:** Solve later.

---

## Current Milestone Onboarding Form — Inputs

For a specific feature, [FEATURES.md](FEATURES.md) is authoritative. The current
React onboarding wizard collects one answer at a time for a brand-new site. It
does not ask for an existing WordPress site, WordPress credentials, hosting,
DNS, or migration information.

### Client Identity
- Author name (as it appears publicly)
- Author email address

### Site Identity
- Website name
- Site tagline / author bio one-liner
- Author short bio (paragraph, shown in About section)
- Author long bio (optional, for full About page)

### Genre & Branding
- Genre(s) — multi-select or free text
- Primary brand color (hex)
- Secondary brand color (hex)

### Social & Marketing
- Newsletter signup link or Kit form ID
- Social media links (Twitter/X, Instagram, Facebook, TikTok, YouTube — all optional)

Book entries, headshots, and template selection are added by later Milestone 1
features.

## Aspirational Production Onboarding Inputs

Future production provisioning may additionally collect:

- WordPress admin username and password for the newly created site
- Author headshot and book portfolio
- Divi template selection
- Domain name (for Cloudways app configuration and Cloudflare DNS record)
- Confirmation that nameservers point to Cloudflare

---

## Future Production Flow: Intake to Live Site

> This flow is aspirational and is not the current Milestone 1 implementation.
> Milestone 1 generates standard, non-ecommerce author websites only. After generation,
> each site is persisted under a unique ID and can be visited at
> `/sites/<site_id>` inside AWG. Ecommerce generation is deferred.

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
- Ecommerce support (dedicated server routing, ecommerce flag on form) — see F008/T001 in FEATURES.md

---

## Open Questions / Decisions Deferred

- v2 deployment spec: what exactly should propagate to client site databases on deploy?
- Client self-service form: security model, access control, whether to build at all
- Email hosting provider (Google Workspace reseller, Zoho, Fastmail, other?)
- Billing/invoicing integration
- Maintenance workflow (WP-CLI update scripts, ManageWP, hosting-native, other?)
