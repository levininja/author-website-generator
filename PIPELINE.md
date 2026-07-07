# Author Website Generator — Provisioning Pipeline

Related documents: [README](README.md) · [Product spec](SPEC.md) · [Feature list](FEATURES.md) · [Product decisions](DECISIONS.md)

- **Step 1:** Cloudways API → create new application on the shared non-ecommerce server
- **Step 2:** SSH → clone starter kit repo into new app folder (starter kit = base Divi child theme + mu-plugin + standard plugin list)
- **Step 3:** WP-CLI → install WordPress core
- **Step 4:** WP-CLI → import selected Design System exports (Theme Builder templates, page layouts, standard pages: Home, About, Books, Contact)
- **Step 5:** WP-CLI → set all client-specific values (site name, tagline, author bio, colors, headshot, social links, Kit newsletter form, Books custom post type entries, selected Design System)
- **Step 6:** Cloudflare API → create A record pointing client domain to server IP
- **Step 7 (DNS wait):** Poll Cloudflare's `1.1.1.1` DNS-over-HTTPS until domain resolves to correct server IP; configurable timeout, default 10 minutes; show "Waiting for DNS propagation" label in UI during wait
- **Step 8:** Cloudways API → attach client's domain to the new app + provision SSL
- **Step 9:** Email → send client WordPress admin URL and credentials (see F006)
- **Step 10:** Show success with site URL (see F007)

> **Sequencing note — correction from original spec:** SSL provisioning (Step 8) must come after DNS resolves (Steps 6+7). The original spec had SSL before DNS, which causes Let's Encrypt to fail because the domain doesn't yet resolve to the server. Corrected order: 1 → 2 → 3 → 4 → 5 → 6 → 7(DNS wait) → 8 → 9. The Onboarding Flow diagram in SPEC.md must be updated to reflect this when the step is implemented.

**Preflight check (runs before Step 1, not a numbered provisioning step):**
- Verify SSH connectivity to the server
- Verify WP-CLI is installed and callable on the server
- Verify GitHub SSH access (`ssh -T git@github.com` returns exit code 1 with "successfully authenticated" in stderr — this is GitHub's expected behavior, not an error)
- Verify the selected Design System manifest and exports are present before provisioning begins
- If any preflight check fails, abort the entire job before any Cloudways app is created — prevents orphaned apps that need manual cleanup
- Surface a specific error message identifying which preflight check failed
