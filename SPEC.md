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
- **Design System:** A version-controlled visual style package used by the generator. A Design System contains metadata, Divi Theme Builder exports, page layout exports, preview assets/templates, and genre/style tags for the onboarding UI.
- **One-Page Static Template (OPST):** A lightweight static preview used during onboarding to show the top of a homepage with the selected Design System, user colors, and available onboarding copy. OPST previews are not WordPress installs.
- **Base child theme:** The single Divi child theme applied to every generated author website. It provides shared PHP, quality defaults, and author-specific structures such as the Books custom post type while leaving most visual styling to the selected Design System.
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
- Allows the user to choose from many Design Systems and passes that choice into the generator.

### Managed Infrastructure & Backend Automation

- **Complete Technical Maintenance:** Ongoing troubleshooting, mobile responsiveness optimization, and core technical SEO management. *(Solve later — not in v1)*
- **Infrastructure Management:** Fully handled email hosting, DNS administration, and secure team login management. *(DNS in v1; email hosting and client login management — solve later)*

---

## Technical Architecture
### Core Platform & Tech Stack of This Project
Python / Django 5.2 LTS backend with React frontend flows. See
[Product decisions](DECISIONS.md#awg-uses-django-and-react).

### Core Platform & Tech Stack of Websites we will Generate

- **Content Management System:** WordPress.
- **Theme/Builder:** Divi Builder for standardized, formulaic front-end design.
  - **Licensing:** Start with a normal (single-site) Divi license for POC on one site. When scaling to multiple sites, upgrade to a developer license. *(Reminder: prompt Levi to upgrade when multi-site scaling begins.)*
- **Development Environment:** VS Code for coding and local environment management.
- **Custom Code:** All PHP modifications live in either:
  - A custom **must-use plugin (mu-plugin)** specific to this system, OR
  - A custom **Divi child theme**
  - See [Product decisions](DECISIONS.md#wordpress-custom-code-stays-modular).
- **Base child theme:** Every generated site uses one shared Divi child theme. See [Product decisions](DECISIONS.md#visual-styles-use-one-base-child-theme-plus-design-systems).
- **Design Systems Library:** Visual variation is delivered through version-controlled Design System folders. See [Product decisions](DECISIONS.md#visual-styles-use-one-base-child-theme-plus-design-systems).
- **Generated pages:** The generator creates key pages such as Home, About, Books, and Contact from the selected Design System's exported layout JSONs. See [Product decisions](DECISIONS.md#layout-jsons-deliver-pre-built-pages).
- **Books content model:** Generated WordPress sites model books as a custom post type. See [Product decisions](DECISIONS.md#books-are-generated-as-a-wordpress-custom-post-type).

### Infrastructure & Hosting of Websites we will Generate

- **Primary Hosting Provider:** Cloudways (A plan). Fallback: Liquid Web (B plan). See [Product decisions](DECISIONS.md#cloudways-is-the-primary-production-host).
- **NO WordPress Multisite.** Every client gets a separate WordPress install. See [Product decisions](DECISIONS.md#generated-sites-are-separate-wordpress-installs-not-multisite).
- **Server Architecture:**
  - All non-ecommerce author websites share **one server**.
  - Each ecommerce author website gets its **own dedicated server**.
  - The example/demo site lives on the shared non-ecommerce server.
  - The ecommerce example/demo site lives on its own separate server.
- **Config file:** A config file will track all servers (shared non-ecommerce server, ecommerce example server, and each ecommerce client server).
- **Staging:** One shared staging environment for the example site only. See [Product decisions](DECISIONS.md#only-the-example-site-has-staging).

### Domain & DNS

- **Clients purchase and own their own domains.** See [Product decisions](DECISIONS.md#clients-own-their-domains).
- DNS transfers during onboarding can be done by Levi manually for now; later, give the user a UI for this
- **Standard DNS: Cloudflare (free tier, per client).** See [Product decisions](DECISIONS.md#standard-dns-uses-cloudflare).
- Process: client moves nameservers to Cloudflare; Levi creates/manages the A record pointing their domain to the Cloudways server.

### Source Control & Deployment

- **Source Control:** GitHub manages configurations and site templates.
- **Git integration:** Cloudways has a built-in Git integration. Each server/app is configured to pull from a specific branch (`production`). When a deployment is triggered, the Cloudways API fetches the latest commit from the `production` branch and deploys it.
- **Deployment model:**
  - **v1 (implement now):** A deployment replaces the backend PHP code (mu-plugin + child theme) for **all sites** on the server. It replaces the database only for the **example site**. See [Product decisions](DECISIONS.md#deployments-do-not-overwrite-client-databases).
  - **v2 (document, do not implement):** *(TBD — Levi to define. Likely: per-client database seeding or update propagation for structural/schema changes.)*
- **CI/CD:** GitHub Actions automates deployment and ongoing maintenance, replacing manual contractor builds. Automated testing is integrated into the pipeline to ensure sites remain stable and scalable.
- **Client Autonomy:** Architecture mandates true site portability. Clients retain full domain ownership. The system is a managed service, not a proprietary locked-in platform.

### Automation & Orchestration

- **Workflow Engine:** OpenClaw handles orchestration.
- **AI Integration:** Multi-agent orchestration (OpenClaw framework, Claude, ChatGPT/Codex) handles complex automated workflows, hooking into site generation and maintenance tasks.
- **WP-CLI:** Used to generate and configure WordPress sites automatically over SSH. See [Product decisions](DECISIONS.md#provisioning-uses-wp-cli-over-ssh).

### Preview Architecture

- During onboarding, AWG uses OPST previews rather than creating full WordPress demo sites for each visual style. See [Product decisions](DECISIONS.md#onboarding-previews-use-one-page-static-templates).
- After generation, `/sites/<site_id>` can provide a more complete AWG-hosted preview of the generated website package. That preview remains distinct from a production WordPress deployment.

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
- Contact email address used as the destination for reader contact-form messages

### Site Identity
- Site domain (purchased or aspirational)
- Site tagline / author bio one-liner
- Author short bio (paragraph, shown in About section)
- Author long bio (optional, for full About page)

### Genre & Branding
- Genre(s) selected through autocomplete backed by the three-level
  `genres.json` hierarchy
- Primary and secondary brand colors selected together
- Design System selected from the available style library

### Book Portfolio
- At least one book is required
- Required per book: title, cover, description, buy link, category, genre,
  subgenre, and standalone/series information
- Optional per book: editorial reviews, endorsements, reader review excerpts,
  awards, reader-fit copy, and sample chapter PDF

### Social & Marketing
- Newsletter signup link or Kit form ID
- Social media links (Twitter/X, Instagram, Facebook, TikTok, YouTube,
  Goodreads — all optional and collected together)

Headshots and Design System selection are added by later Milestone 1 features.

## Aspirational Production Onboarding Inputs

Future production provisioning may additionally collect:

- WordPress admin username and password for the newly created site
- Author headshot and book portfolio
- Design System selection
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
           Starter kit = base Divi child theme + mu-plugin + standard plugin list
        ↓
[ Step 3 ] WP-CLI → install WordPress core
        ↓
[ Step 4 ] WP-CLI → import starter database
           (Design System Theme Builder exports and standard pages: Home, About, Books, Contact)
        ↓
[ Step 5 ] WP-CLI → set all client-specific values
           (site name, tagline, author bio, colors, logo/headshot, social links,
            Kit newsletter form, Books custom post type entries, selected Design System)
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
| 2 | Clone starter kit | `steps_wordpress.py` | SSH into server, clone base Divi child theme + mu-plugin + plugin list repo into new app folder | Fails loudly on SSH auth error; requires deploy key on GitHub repo |
| 3 | Install WordPress core | `steps_wordpress.py` | WP-CLI `core install` | Idempotency guard: skips if WP already installed |
| 4 | Import starter database | `steps_wordpress.py` | WP-CLI DB import — selected Design System Theme Builder exports and standard pages (Home, About, Books, Contact) | Skipped if Step 3 was skipped (WP already installed) |
| 5 | Configure site | `steps_wordpress.py` | WP-CLI writes all client-specific values: site name, tagline, bio, colors, logo/headshot, social links, Kit newsletter form, Books custom post type entries, selected Design System | Validates written values back via `wp option get`; fails loudly on mismatch |
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
