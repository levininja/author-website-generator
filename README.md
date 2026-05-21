# Author Website Generator

Internal tool for provisioning author WordPress sites from a single onboarding form.

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
- `APP_USERNAME` — login username for the form
- `APP_PASSWORD` — login password for the form
- `SECRET_KEY` — a long random string (used to sign sessions)

**3. Run**
```bash
python app.py
```

The app runs on `http://localhost:5000` by default. Navigate to `/login` to sign in.

## Running tests
```bash
pytest
```

## Project structure
```
app.py              Flask app — routes and auth logic
templates/          Jinja2 HTML templates
  login.html        Login page
  onboard.html      Onboarding form
static/
  style.css         Shared styles
  onboard.js        Form interactivity (tags, book rows, submission)
tests/
  conftest.py       Pytest fixtures
  test_auth.py      Auth and route tests
```
