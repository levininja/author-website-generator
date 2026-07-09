# Author Website Generator — Coding Standards

These standards apply to all Python code in this repository. They prioritize readability, maintainability, and conventional Python that any experienced developer will recognize. Where possible, rules are enforced automatically by tooling so they don't rely on discipline or memory.

Related documents: [README](README.md) · [Product decisions](DECISIONS.md)

---

## Tooling

### Ruff

[Ruff](https://docs.astral.sh/ruff/) is the single tool for formatting and linting. It replaces Black (formatter), flake8 (linter), and isort (import sorter). Configuration lives in `pyproject.toml`.

Run the formatter:
```bash
ruff format .
```

Run the linter:
```bash
ruff check .
```

Fix auto-correctable lint violations:
```bash
ruff check --fix .
```

Configure your editor to run `ruff format` on save. This eliminates formatting noise from PRs and removes style from code review entirely.

---

## Formatting

### Line length: 100 characters

Maximum line length is 100 characters. Django's patterns tend toward verbosity — model field definitions, URL configurations, and serializer declarations benefit from the extra room. Ruff enforces this automatically.

### String quotes: double quotes

All strings use double quotes. This is Ruff's default and matches JSON, HTML, and most adjacent languages a web developer works with.

```python
# correct
name = "Elara Voss"
error = "Email address is already in use."

# wrong
name = 'Elara Voss'
```

---

## Imports

Imports are grouped into three sections, separated by a blank line, in this order:

1. Standard library
2. Third-party packages
3. Local / project modules

```python
# 1. Standard library
import json
import os
from typing import Any

# 2. Third-party
from django.db import models
from pydantic import BaseModel

# 3. Local
from onboarding.models import Author
from .services import create_author
```

Ruff enforces this order automatically. Never mix groups or skip blank lines between them.

---

## Type Hints

All functions and methods require type annotations on every parameter and return value. No exceptions.

```python
# correct
def create_author(name: str, email: str) -> Author:
    ...

def delete_author(author_id: UUID) -> None:
    ...

# wrong — missing return type, missing parameter type
def create_author(name, email):
    ...
```

**Rules:**
- Always annotate `-> None` for functions that return nothing. Omitting it is ambiguous.
- Use `str | None` (Python 3.10+ union syntax) rather than `Optional[str]`.
- Use `from __future__ import annotations` at the top of files if you need forward references.
- For Django model instances, use the model class directly (`Author`, not `Any`).
- Pydantic models are already typed by definition — no extra work needed there.

Ruff enforces this via the `ANN` rule set.

---

## Naming Conventions

Standard PEP 8 throughout:

| Thing | Style | Example |
|---|---|---|
| Variables | `snake_case` | `author_name` |
| Functions | `snake_case` | `create_author` |
| Classes | `PascalCase` | `AuthorService` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_BOOK_COUNT` |
| Private helpers | `_leading_underscore` | `_normalize_email` |
| Django model fields | `snake_case` | `contact_email` |
| Django app directories | `snake_case` | `onboarding/` |

### Function and service naming: verb-first

Functions and service methods are named verb-first — they read as instructions describing what they do.

```python
# correct
def create_author(...)
def get_book_by_id(...)
def validate_email(...)
def delete_draft_authors(...)

# wrong — noun-first
def author_create(...)
def book_get(...)
```

This matches Django's own conventions and reads naturally in call sites.

---

## Docstrings

Docstrings are scaled to complexity. The bar is: *can a mid-level Python developer read the function signature and immediately understand intent, inputs, and output without prose?* If yes, a one-liner is enough. If no, use the full Google style.

### Simple / self-evident functions — one line

```python
def get_author_by_id(author_id: UUID) -> Author:
    """Return the Author with the given ID, or raise AuthorNotFound."""
```

### Complex functions — Google style

Use Google-style docstrings for functions with non-obvious behavior, multiple parameters, important return values, or error conditions.

```python
def create_author_from_submission(data: OnboardingSubmission) -> Author:
    """Atomically persist a new author and their submitted books.

    Validates that the email is not already in use, creates the Author
    record, and associates all submitted books in a single transaction.
    Partial failures roll back the entire submission.

    Args:
        data: Validated onboarding submission containing author and book fields.

    Returns:
        The newly created Author instance with related books accessible.

    Raises:
        DuplicateEmailError: If an author with this email already exists.
        ValidationError: If any book data fails model-level validation.
    """
```

**Sections to include as applicable:** `Args`, `Returns`, `Raises`. Omit sections that don't apply — don't write `Returns: None` for void functions.

---

## Exception Handling

### Custom exception classes

Project-specific exceptions live in a top-level `exceptions.py`. Services raise typed exceptions; views catch them and translate to HTTP responses. This keeps the service layer completely HTTP-ignorant.

```python
# exceptions.py
class AWGError(Exception):
    """Base class for all AWG application errors."""

class AuthorNotFound(AWGError):
    """Raised when an author lookup finds no matching record."""

class DuplicateEmailError(AWGError):
    """Raised when an email address is already registered to an author."""
```

```python
# services.py
from exceptions import DuplicateEmailError

def create_author(name: str, email: str) -> Author:
    if Author.objects.filter(email=email).exists():
        raise DuplicateEmailError(email)
    ...
```

```python
# views.py
from exceptions import DuplicateEmailError

def author_create_view(request: HttpRequest) -> JsonResponse:
    try:
        author = create_author(name, email)
    except DuplicateEmailError:
        return JsonResponse({"error": "Email already in use."}, status=409)
    ...
```

### Django's built-in exceptions

Django's own exceptions (`Http404`, `PermissionDenied`) are still appropriate where they are the natural fit — URL resolution and authentication/authorization. Don't replace those with custom classes.

### Never catch bare `Exception`

Always catch the most specific exception type available. Bare `except Exception` hides bugs.

```python
# correct
except DuplicateEmailError:
    ...

# wrong
except Exception:
    ...
```

---

## Django Architecture

### Thin models, fat services

Models are pure data containers. Services hold all business logic.

**Models contain:**
- Field definitions
- `Meta` class (table name, ordering, constraints)
- `__str__` method
- Simple computed properties (no DB queries, no side effects)

**Models do not contain:**
- Validation logic beyond field-level constraints
- Cross-model operations
- Anything that calls another service or model

**Services contain:**
- All business logic
- Atomic transactions (`with transaction.atomic()`)
- Cross-model coordination
- External integrations

**Views contain:**
- Request parsing
- One service call
- Response construction

A view that contains business logic is a bug waiting to be discovered.

```python
# correct — thin view
def author_submit_view(request: HttpRequest) -> JsonResponse:
    data = OnboardingSubmission(**json.loads(request.body))
    author = create_author_from_submission(data)
    return JsonResponse({"author_id": str(author.id)}, status=201)

# wrong — fat view
def author_submit_view(request: HttpRequest) -> JsonResponse:
    data = json.loads(request.body)
    if Author.objects.filter(email=data["email"]).exists():
        return JsonResponse({"error": "..."}, status=409)
    author = Author.objects.create(...)
    for book in data["books"]:
        Book.objects.create(author=author, ...)
    return JsonResponse({"author_id": str(author.id)}, status=201)
```

---

## Tests

### File structure mirrors source

Every source file has a corresponding test file at the same relative path under `tests/unit/`.

```
onboarding/services.py        →  tests/unit/onboarding/test_services.py
onboarding/views.py           →  tests/unit/onboarding/test_views.py
accounts/models.py            →  tests/unit/accounts/test_models.py
```

When you create a new source file, create its test file at the same time.

### Test function naming: verbose and descriptive

Test names follow `test_<thing>_<condition>_<expected_outcome>`. A failing test name in CI should read as a plain-English description of what broke.

```python
# correct
def test_create_author_duplicate_email_raises_duplicate_email_error():
def test_create_author_valid_input_returns_author_instance():
def test_get_author_by_id_missing_id_raises_author_not_found():

# wrong — too vague
def test_create_author():
def test_error_case():
```

### Unit tests stay unit tests

Unit tests test one function in isolation. They do not test the full request/response stack — that's an integration test. Use mocks or fakes for external dependencies (database, storage, external APIs) where the goal is to test logic, not persistence.

---

## Code Comments

Comments explain *why*, not *what*. Code already shows what it does — a comment restating it is noise.

```python
# wrong — restates the code
# Check if the email already exists
if Author.objects.filter(email=email).exists():
    raise DuplicateEmailError(email)

# correct — explains a non-obvious constraint
# Emails are normalized to lowercase before storage; compare case-insensitively
# to avoid phantom duplicates from capitalization differences.
if Author.objects.filter(email__iexact=email).exists():
    raise DuplicateEmailError(email)
```

Comment when:
- The code is counter-intuitive or has a non-obvious constraint
- A deliberate choice was made that a reader might question ("why not X?")
- A Django or library quirk requires a workaround

Don't comment when:
- The code is simple and readable on its own
- The docstring already explains it
- The type annotations make the intent clear
