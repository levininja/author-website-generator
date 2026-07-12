"""Generate WordPress nav menu and footer social links for an author's site via WP-CLI."""

from collections.abc import Callable, Sequence

from generation.subprocess_runner import default_capture_runner, default_runner

WP_CLI = "/usr/local/bin/wp"

# Divi registers this theme location for the primary navigation header menu.
# Placeholder name pending R001 (Divi option-key research).
DIVI_PRIMARY_MENU_LOCATION = "primary-menu"

# Divi stores footer social icon URLs in the et_divi option under these sub-keys.
# Keys are placeholder names pending R001 (Divi option-key research).
DIVI_OPTION_KEY = "et_divi"
SOCIAL_OPTION_KEYS = {
    "twitter": "social_twitter",
    "instagram": "social_instagram",
    "facebook": "social_facebook",
    "tiktok": "social_tiktok",
    "youtube": "social_youtube",
    "goodreads": "social_goodreads",
}

# The four top-level nav pages and their canonical URL slugs.
NAV_PAGES = [
    ("Home", "/"),
    ("About", "/about/"),
    ("Books", "/books/"),
    ("Contact", "/contact/"),
]


def _wp_flags(site_path: str) -> list[str]:
    return [f"--path={site_path}", "--allow-root"]


def generate_nav_menu(
    site_path: str,
    runner: Callable[[Sequence[str]], None] | None = None,
    capture_runner: Callable[[Sequence[str]], str] | None = None,
) -> None:
    """Create a WordPress nav menu with Home/About/Books/Contact.

    Assigns it to Divi's primary-menu location. WP-CLI's `menu create` returns
    the new menu ID via --porcelain; that ID is then referenced by every
    subsequent `menu item add-custom` and `menu location assign` call.
    """
    run = runner or default_runner
    capture = capture_runner or default_capture_runner

    menu_id = capture([
        WP_CLI, "menu", "create", "Main Menu",
        "--porcelain",
        *_wp_flags(site_path),
    ]).strip()

    for title, url in NAV_PAGES:
        run([
            WP_CLI, "menu", "item", "add-custom", menu_id,
            title, url,
            *_wp_flags(site_path),
        ])

    run([
        WP_CLI, "menu", "location", "assign", menu_id,
        DIVI_PRIMARY_MENU_LOCATION,
        *_wp_flags(site_path),
    ])


def generate_footer_social_links(
    site_path: str,
    social_links: dict,
    runner: Callable[[Sequence[str]], None] | None = None,
) -> None:
    """Write each social link URL into the et_divi option so Divi renders footer icons.

    social_links must contain only keys with truthy values (as produced by
    serialize_author); missing/empty platforms are simply absent and skipped here.
    If social_links is empty, no WP-CLI calls are made and the footer is valid
    with no social icons.
    """
    run = runner or default_runner

    for platform, url in social_links.items():
        option_sub_key = SOCIAL_OPTION_KEYS.get(platform, f"social_{platform}")
        run([
            WP_CLI, "option", "patch", "update", DIVI_OPTION_KEY,
            option_sub_key, url,
            *_wp_flags(site_path),
        ])


def setup_header_footer(
    site_path: str,
    serialized_author: dict,
    runner: Callable[[Sequence[str]], None] | None = None,
    capture_runner: Callable[[Sequence[str]], str] | None = None,
) -> None:
    """Create the nav menu and configure footer social links for the given author.

    Reads social_links from serialized_author; the key is optional and defaults
    to an empty dict so authors with no socials still get a valid footer.
    """
    generate_nav_menu(site_path, runner=runner, capture_runner=capture_runner)
    generate_footer_social_links(
        site_path,
        serialized_author.get("social_links", {}),
        runner=runner,
    )
