# Author Website Generator — Product Decisions

Decision: We do not use decision numbers in this file.

Related documents: [README](README.md) · [Product spec](SPEC.md) · [Feature list](FEATURES.md) · [Provisioning pipeline](PIPELINE.md)

This file records the product's strategic decisions and their primary rationale.


## replace_author_id is unauthenticated by design for v1

`POST /onboarding` accepts a `replace_author_id` field that overwrites an existing author submission with new data. This parameter is not authenticated: any caller with a UUID can overwrite the record it identifies. We have accepted this risk for v1 for the following reasons:

1. Author UUIDs are only revealed to the submitter in the onboarding response and review URL — a bad actor would need the victim to share their UUID with them.
2. The motivation to do so is essentially nonexistent: overwriting someone else's onboarding data provides no meaningful benefit to an attacker.
3. Even if it occurred, the impact is low: no financial data, credentials, or PII beyond author contact info is involved, and the victim can simply resubmit.

When authentication is added to AWG, `replace_author_id` must be constrained to the authenticated user's own records. At that point this decision is superseded and should be removed.

---

## Users can generate a website before creating an account

AWG landing pages, onboarding, and website generation are available without an account or payment. This lets users experience the product's core value with minimal initial friction; account creation can happen afterward.

---

## Users get a 7-day free trial

The trial starts when the site is created, and payment is required after 7 days to keep it live. This lets authors evaluate and share the finished site before committing to payment.

---

## Standard sites share a server; ecommerce sites do not

Standard author websites are separate WordPress applications on one shared Cloudways server. Each ecommerce website gets a dedicated server because its resource usage and security exposure are less predictable.

---

## The ecommerce demo uses ecommerce infrastructure

The ecommerce demo is hosted on its own dedicated server with type `ecommerce`. Matching production infrastructure makes its provisioning tests representative.

---

## v1 supports new WordPress sites only

v1 does not import content or configuration from existing WordPress, Divi, or hosting setups. Limiting the initial scope avoids the variability of migrations.

---

## There are no growth deadlines

The goal is to earn the first dollar as soon as practical without setting revenue deadlines. This avoids premature scaling based on assumed growth.

---

## Ecommerce is excluded from v1

Ecommerce support is deferred until the standard-site pipeline is stable because it adds security, liability, and infrastructure complexity.

---

## AWG does not store or process credit card details

Stripe collects and retains payment details; AWG stores only the references and customer data required to provide the service. This reduces security exposure and compliance scope.

---

## Initial marketing targets existing WordPress users

Initial marketing targets authors who are already comfortable with WordPress because they face less adoption friction.

---

## Marketing uses testimonials and live examples

The marketing site uses testimonials and links to live examples to establish trust in a new service.

---

## AWG uses Django and React

AWG uses Python/Django 5.2 LTS for backend validation, persistence,
authentication, security, and generation orchestration. React owns the
interactive frontend flows where shared client-side state matters:

1. Onboard the user by collecting the information needed to build an author website.
2. Generate the website from the submitted information and communicate the result.

Django provides a long-term-supported backend foundation, while React is
appropriate for the wizard and generation-result experience. React-based
generated-site preview remains undecided.

Onboarding and generation are separate React apps mounted into Django-rendered
pages. AWG still has one canonical website and one Python/Django server at
runtime; the React apps are not separate deployed websites or backend services.

Local development may run each React app through its own Vite dev server for
hot module reloading, such as one port for onboarding and one port for
generation. These Vite servers are developer tooling only. The Django-mounted
pages remain the integration source of truth for production bundle loading,
CSRF, cookies, media URLs, and API behavior.

The generation app should support direct development against a saved Website
brief by accepting a brief identifier in the URL and loading the real persisted
data through Django APIs. This lets developers work on generation without
repeating the onboarding survey while keeping the generation flow grounded in
real AWG data.

Onboarding uses a wizard that asks one question at a time and retains answers
when the user navigates backward. Completing the survey atomically persists the
validated author and books before showing a read-only review. The review reloads
the author and book resources from the database to verify persistence; its Back
button returns to the survey, and its Generate button calls the generation
endpoint. Website generation is a later feature.

Related answers may share one wizard page when separating them would make the
workflow less usable. Brand colors and social profiles are grouped pages.
Genres are seeded from the required three-level `genres.json` catalog into
normalized category, genre, and subgenre tables rooted at Fiction and
Nonfiction. Runtime author and book selections use those database tables as the
shared taxonomy.

---

## User accounts use a custom model with UUID primary keys

AWG uses `accounts.User` with a random UUID v4 primary key. Defining the custom model before other models reference users avoids a difficult later migration, while UUIDs provide stable, non-sequential identifiers without embedding PII.

---

## Visual styles use one base child theme plus Design Systems

AWG uses one shared Divi child theme for every generated website and delivers
visual variation through version-controlled Design System folders. The base
child theme owns shared PHP, the Books custom post type, accessibility,
typography, responsive, and performance defaults. Each Design System owns the
`manifest.json`, Theme Builder exports, page layout exports, preview
assets/templates, and metadata needed to apply a distinct author-facing style
programmatically.

This keeps Divi and PHP maintenance centralized while allowing the style
library to grow from a small alpha set to many genre-specific and
genre-agnostic options.

---

## Theme Builder JSONs deliver global design

Divi Theme Builder exports are the primary mechanism for shared headers,
footers, and single-book templates. This keeps global structure consistent
across generated sites while allowing each Design System to define its own
visual treatment.

---

## Layout JSONs deliver pre-built pages

Design Systems include Divi layout exports for standard pages such as Home,
About, Books, and Contact. Generated sites start from complete page structures
instead of blank templates, then AWG fills them with submitted author, book,
branding, and marketing data.

---

## Onboarding previews use One-Page Static Templates

AWG does not create or host a full WordPress demo site for every visual style
during onboarding. Style selection uses lightweight One-Page Static Templates
that can reflect the selected Design System, brand colors, and available
onboarding copy.

This keeps onboarding fast and cheap while still giving authors enough visual
feedback to choose a style before full generation.

---

## Books are generated as a WordPress custom post type

Generated WordPress sites represent books as structured content, not just
static page sections. The base child theme registers a Books custom post type
so archives, single-book templates, metadata, and future book-specific
automation can share one consistent content model.

---

## WordPress custom code stays modular

AWG custom WordPress code lives in an AWG must-use plugin or the shared Divi
child theme. WordPress core, Divi core, and third-party plugins are not modified
directly, so updates do not overwrite AWG code.

---

## AWG does not use Phoenix Super Theme as its foundation

AWG's generated websites are based on the shared AWG Divi child theme, not
Phoenix Super Theme. Avoiding that dependency reduces licensing uncertainty and
long-term maintenance risk.

---

## Generated sites are separate WordPress installs, not Multisite

Every production author website is its own WordPress installation. This keeps
sites portable and avoids coupling client ownership to a shared Multisite
network.

---

## Cloudways is the primary production host

Cloudways is the primary hosting provider for generated WordPress sites, with
Liquid Web as a fallback. Production provisioning targets Cloudways first.

---

## Clients own their domains

Authors purchase and own their domains. AWG may manage DNS records during
provisioning, but the domain remains client-owned so the generated site remains
portable.

---

## Standard DNS uses Cloudflare

Standard production DNS uses Cloudflare's free tier per client. Cloudflare
provides API automation for records plus CDN, SSL, and DDoS protections.

---

## Only the example site has staging

AWG keeps one shared staging environment for the example site. Individual
client staging environments are deferred because the underlying code is shared
and client differences are primarily content and selected Design System.

---

## Deployments do not overwrite client databases

In v1, deployments replace backend PHP code for all sites on the target server
and replace the database only for the example site. Client site databases are
not touched by deployments.

---

## Provisioning uses WP-CLI over SSH

Production WordPress setup and configuration are scripted with WP-CLI over SSH
instead of manual dashboard work. This makes provisioning repeatable and easier
to validate.

---

## DNS must resolve before SSL provisioning

SSL provisioning runs only after DNS points the domain to the target server.
Let's Encrypt validation fails if the domain does not resolve first.

---

## Uploaded media uses Django FileField storage

Database models use Django `FileField` values as durable references to uploaded
images and PDFs. In local development, Django stores the bytes beneath the
repository's ignored `media/` directory and serves them from `/media/`. In
production, the same fields use Cloudflare R2 as the storage backend and a
normal Cloudflare CDN custom domain for retrieval. Database records store
storage object keys rather than environment-specific URLs, so the data model
and application logic remain the same across environments.

Uploaded objects use generated paths and randomized filenames rather than
user-controlled storage paths. R2 credentials and bucket configuration are
environment variables and are never committed.

---

## Database tables use semantic names

AWG deliberately overrides Django's default `<app_label>_<model_name>` table
naming convention. Application ownership is an implementation detail and does
not define the business meaning of stored data, so tables use explicit,
domain-oriented names such as `author`, `book`, `book_series`, `genre`,
`author_billing`, and `author_shipping`.

Every AWG domain model in the onboarding data model declares its table name
explicitly through `Meta.db_table`. Related tables use the owning domain as a
prefix, such as `book_award`, `book_review`, and `author_genre`. This
produces clearer raw SQL and keeps database names stable if Django app
boundaries change. Django framework and authentication tables retain their
framework-managed names.
