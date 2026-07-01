# Repository Instructions

## Stylesheets

- SCSS files are the stylesheet source of truth. Always edit `.scss` files; never edit generated `.css` files directly.
- After changing SCSS, run `npm run scss` to compile CSS.
- During active stylesheet development, run `npm run scss:watch` to automatically recompile CSS when an SCSS file changes.
- Commit the generated CSS with its corresponding SCSS source so Django can serve the current compiled asset.
