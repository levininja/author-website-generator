# Author Website Generator

A managed website service for authors. Users can submit the public onboarding form and generate an author website before creating an account or providing payment information.

Related documents: [Product spec](SPEC.md) · [Feature list](FEATURES.md) · [Product decisions](DECISIONS.md) · [Provisioning pipeline](PIPELINE.md)

## Setup

**1. Create and activate the virtual environment**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Once activated, all Python commands (`ruff`, `pytest`, `python manage.py`, etc.) use the project's isolated environment. Activate once per terminal session.

**2. Install dependencies**
```bash
pip install -r requirements-dev.txt
npm install
```

`requirements-dev.txt` includes everything in `requirements.txt` plus dev tools (pytest, Ruff). Use `requirements.txt` alone for production deployments.

**3. Configure environment**
```bash
cp .env.example .env
```
Edit `.env` and set:
- `DJANGO_SECRET_KEY` — a long random string
- `DJANGO_DEBUG` — `true` for local development, `false` in production
- `DJANGO_ALLOWED_HOSTS` — comma-separated hostnames (e.g. `localhost,127.0.0.1`)

Local uploads are stored in the ignored `media/` directory. Production uses
Cloudflare R2 when `R2_BUCKET_NAME` and the other `R2_*` variables documented
in `.env.example` are configured; `R2_CUSTOM_DOMAIN` is the normal Cloudflare
CDN hostname used to retrieve stored media.

**4. Run migrations**
```bash
python manage.py migrate
```

**5. Run**
```bash
npm run build:frontend
python manage.py runserver
```

The app runs on `http://localhost:8000` by default. Navigate to `/onboard` to open the form. No login is required.

**6. (Optional) Start the background worker**

The generation pipeline runs in a background thread spawned by Django, so no separate worker process is needed for local development.

**7. (Optional) Preview a generated site**

After submitting the onboarding form and triggering generation, the generated WordPress site is automatically served on a local PHP server. You can also start it manually:

```bash
# Serve the hosted site on http://localhost:8080
php -S localhost:8080 -t hosted-site/
```

The generation pipeline starts and manages this server automatically. The `hosted-site/` directory is created and updated each time a site is generated. Keep this command running in a separate terminal to browse the live preview at `http://localhost:8080`.

For React hot module reloading during frontend work, keep Django running as the
API server and start the relevant Vite dev server in another terminal:

```bash
npm run dev:onboarding    # http://127.0.0.1:3000
npm run dev:generation    # http://127.0.0.1:3001
```

The Vite dev servers proxy API requests to Django at `http://127.0.0.1:8000`,
so Django must be running first. The generation app loads a saved Website brief
by URL query parameter:

```text
http://127.0.0.1:3001/?brief=<website_brief_id>
```

Use the Django-mounted generation page as the integration check for production
bundle loading, CSRF, cookies, media URLs, and template bootstrapping:

```text
http://localhost:8000/website-briefs/<website_brief_id>/generate
```

Create a Website brief by completing `/onboard` once. The saved brief ID is the
`author_id` returned by the onboarding submission and used in the generated
author resource URLs.

### Genre catalog

`onboarding/static/genres.json` is the source used by the genre-catalog data
migration. Its three levels are `Fiction`/`Nonfiction`, genre, and subgenre.
Runtime onboarding reads the normalized `genre_category`, `genre`, and
`genre_subgenre` tables through `GET /genres`; it does not read the JSON file.
Future catalog changes require a new data migration so deployed databases
receive the same deterministic update.

## Stylesheets

SCSS is the stylesheet source of truth. Never edit generated CSS directly.

Build CSS once:
```bash
npm run scss
```

Automatically rebuild CSS while editing SCSS:
```bash
npm run scss:watch
```

Keep the watcher running in a separate terminal alongside Django's development server. Generated CSS is committed so Django can serve it without requiring Sass at runtime.

## Project documentation

- [Product spec](SPEC.md) — defines the product, technical architecture, onboarding inputs, and v1 scope.
- [Feature list](FEATURES.md) — tracks prioritized, backlog, and completed features, tasks, and research.
- [Product decisions](DECISIONS.md) — records the strategic decisions and rationale guiding v1.
- [Provisioning pipeline](PIPELINE.md) — documents the ordered site-provisioning workflow and preflight checks.

## Running tests
```bash
pytest
npm run test:frontend
```

## Linting and formatting

This project uses [Ruff](https://docs.astral.sh/ruff/) for Python linting and formatting. It is included in `requirements-dev.txt`.

Note: be sure to activate the virtual environment with `source .venv/bin/activate` first.

Check for violations:
```bash
ruff check .
```

Auto-fix violations that Ruff can resolve automatically:
```bash
ruff check --fix .
```

Format all Python files:
```bash
ruff format .
```

These commands assume the virtualenv is active (step 1 of setup). See `CODING_STANDARDS.md` for the full conventions.

See [CODING_STANDARDS.md](CODING_STANDARDS.md) for the full coding conventions. The remaining unfixed violations are type hints and docstrings — these are added as files are touched rather than in a single pass. New code must be fully annotated and documented.

## Project structure
```
manage.py               Django management entry point
generator/              Django project package
  settings.py           Environment-backed settings
  urls.py               Root URL configuration
  wsgi.py / asgi.py     WSGI and ASGI entrypoints
accounts/               Custom user model (UUID primary key)
  models.py             User extends AbstractUser with UUIDField pk
  migrations/           Database migrations
onboarding/             Public onboarding app
  models.py             Semantic author, book, series, genre, and content tables
  services.py           Atomic onboarding persistence, cleanup, and resource serialization
  views.py              Onboarding orchestration, author/book reads, and no-op generation
  urls.py               URL patterns for this app
  migrations/           Submission and book persistence schema
  templates/onboarding/ Django-namespaced HTML templates
  static/onboarding/    Django-namespaced SCSS, generated CSS, and JS
  static/generation/    Generated generation-app bundle served by Django
config/
  config.example.yaml   Tracked server-inventory template
  config.yaml           Local server inventory (ignored by Git)
  loader.py             YAML loader with Pydantic validation
models/
  config_models.py      Pydantic models: WebsiteServer, AppConfig, ServerType
  onboarding.py         Pydantic onboarding and social-link models
frontend/onboarding/    React onboarding wizard source and component tests
frontend/generation/    React generation app source and component tests
tests/
  conftest.py           Shared pytest fixtures
  unit/                 Unit tests
package.json            React build/test and Sass build/watch commands
AGENTS.md               Repository-specific coding instructions
```
