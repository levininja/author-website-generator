# Repository Instructions

## Linting and formatting

Ruff is installed inside `.venv` and is **not** on the system PATH. Always use the venv-prefixed commands:

```bash
.venv/bin/ruff check .           # check for violations
.venv/bin/ruff check --fix .     # auto-fix what Ruff can
.venv/bin/ruff format .          # format all Python files
```

Run `ruff check .` after every edit to Python files. All violations must be resolved before committing. See `CODING_STANDARDS.md` for the full conventions.

## Stylesheets

- SCSS files are the stylesheet source of truth. Always edit `.scss` files; never edit generated `.css` files directly.
- After changing SCSS, run `npm run scss` to compile CSS.
- During active stylesheet development, run `npm run scss:watch` to automatically recompile CSS when an SCSS file changes.
- Commit the generated CSS with its corresponding SCSS source so Django can serve the current compiled asset.
