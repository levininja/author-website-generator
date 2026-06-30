# Author Website Generator

A managed website service for authors. Users can submit the public onboarding form and generate an author website before creating an account or providing payment information.

Related documents: [Product spec](SPEC.md) · [Feature list](FEATURES.md) · [Product decisions](DECISIONS.md) · [Provisioning pipeline](PIPELINE.md)

## Setup

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Configure environment**
```bash
cp .env.example .env
```
Edit `.env` and set:
- `DJANGO_SECRET_KEY` — a long random string
- `DJANGO_DEBUG` — `true` for local development, `false` in production
- `DJANGO_ALLOWED_HOSTS` — comma-separated hostnames (e.g. `localhost,127.0.0.1`)

**3. Run migrations**
```bash
python manage.py migrate
```

**4. Run**
```bash
python manage.py runserver
```

The app runs on `http://localhost:8000` by default. Navigate to `/onboard` to open the form. No login is required.

## Project documentation

- [Product spec](SPEC.md) — defines the product, technical architecture, onboarding inputs, and v1 scope.
- [Feature list](FEATURES.md) — tracks prioritized, backlog, and completed features, tasks, and research.
- [Product decisions](DECISIONS.md) — records the strategic decisions and rationale guiding v1.
- [Provisioning pipeline](PIPELINE.md) — documents the ordered site-provisioning workflow and preflight checks.

## Running tests
```bash
pytest
```

## Project structure
```
manage.py               Django management entry point
awg/                    Django project package
  settings.py           Environment-backed settings
  urls.py               Root URL configuration
  wsgi.py / asgi.py     WSGI and ASGI entrypoints
accounts/               Custom user model (UUID primary key)
  models.py             User extends AbstractUser with UUIDField pk
  migrations/           Database migrations
onboarding/             Public onboarding app
  views.py              GET /onboard, POST /generate (stub), / redirect
  urls.py               URL patterns for this app
  templates/onboarding/ Django-namespaced HTML templates
  static/onboarding/    Django-namespaced CSS and JS
config/
  config.example.yaml   Tracked server-inventory template
  config.yaml           Local server inventory (ignored by Git)
  loader.py             YAML loader with Pydantic validation
models/
  config_models.py      Pydantic models: WebsiteServer, AppConfig, ServerType
tests/
  conftest.py           Shared pytest fixtures
  unit/                 Unit tests
```
