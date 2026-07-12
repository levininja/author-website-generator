"""Tests for generation/header_footer.py.

All WP-CLI calls are mocked; no real WP install required.
"""

from unittest.mock import MagicMock

SITE_PATH = "/tmp/test-wp-site"

NAV_PAGES = [
    ("Home", "/"),
    ("About", "/about/"),
    ("Books", "/books/"),
    ("Contact", "/contact/"),
]

SOCIAL_LINKS_FULL = {
    "twitter": "https://twitter.com/author",
    "instagram": "https://instagram.com/author",
    "facebook": "https://facebook.com/author",
    "tiktok": "https://tiktok.com/@author",
    "youtube": "https://youtube.com/author",
    "goodreads": "https://goodreads.com/author",
}

SOCIAL_LINKS_PARTIAL = {
    "twitter": "https://twitter.com/author",
    "goodreads": "https://goodreads.com/author",
}


# ---------------------------------------------------------------------------
# Helpers (mirror the pattern used in test_divi_setup.py)
# ---------------------------------------------------------------------------

def _make_runner():
    return MagicMock(return_value=None)


def _make_capture_runner(return_value="10\n"):
    return MagicMock(return_value=return_value)


def _called_args(mock) -> list[list[str]]:
    return [c.args[0] for c in mock.call_args_list]


def _any_call_contains(calls: list[list[str]], *tokens: str) -> bool:
    for call in calls:
        joined = " ".join(call)
        if all(t in joined for t in tokens):
            return True
    return False


# ---------------------------------------------------------------------------
# generate_nav_menu — menu creation
# ---------------------------------------------------------------------------

def test_create_nav_menu_calls_menu_create():
    from generation.header_footer import generate_nav_menu
    capture = _make_capture_runner("10\n")
    runner = _make_runner()
    generate_nav_menu(SITE_PATH, runner=runner, capture_runner=capture)
    calls = _called_args(capture)
    assert _any_call_contains(calls, "menu", "create")


def test_create_nav_menu_uses_menu_id_from_capture_in_subsequent_calls():
    from generation.header_footer import generate_nav_menu
    capture = _make_capture_runner("42\n")
    runner = _make_runner()
    generate_nav_menu(SITE_PATH, runner=runner, capture_runner=capture)
    run_calls = _called_args(runner)
    # All menu item add and menu location assign calls must reference the returned menu ID
    item_calls = [c for c in run_calls if "menu" in c and ("add" in c or "assign" in c)]
    assert len(item_calls) > 0
    for call in item_calls:
        assert "42" in call, f"Expected menu ID '42' in call: {call}"


def test_create_nav_menu_adds_home_item():
    from generation.header_footer import generate_nav_menu
    capture = _make_capture_runner("10\n")
    runner = _make_runner()
    generate_nav_menu(SITE_PATH, runner=runner, capture_runner=capture)
    run_calls = _called_args(runner)
    assert _any_call_contains(run_calls, "menu", "item", "Home")


def test_create_nav_menu_adds_about_item():
    from generation.header_footer import generate_nav_menu
    capture = _make_capture_runner("10\n")
    runner = _make_runner()
    generate_nav_menu(SITE_PATH, runner=runner, capture_runner=capture)
    run_calls = _called_args(runner)
    assert _any_call_contains(run_calls, "menu", "item", "About")


def test_create_nav_menu_adds_books_item():
    from generation.header_footer import generate_nav_menu
    capture = _make_capture_runner("10\n")
    runner = _make_runner()
    generate_nav_menu(SITE_PATH, runner=runner, capture_runner=capture)
    run_calls = _called_args(runner)
    assert _any_call_contains(run_calls, "menu", "item", "Books")


def test_create_nav_menu_adds_contact_item():
    from generation.header_footer import generate_nav_menu
    capture = _make_capture_runner("10\n")
    runner = _make_runner()
    generate_nav_menu(SITE_PATH, runner=runner, capture_runner=capture)
    run_calls = _called_args(runner)
    assert _any_call_contains(run_calls, "menu", "item", "Contact")


def test_create_nav_menu_adds_exactly_four_items():
    from generation.header_footer import generate_nav_menu
    capture = _make_capture_runner("10\n")
    runner = _make_runner()
    generate_nav_menu(SITE_PATH, runner=runner, capture_runner=capture)
    run_calls = _called_args(runner)
    item_add_calls = [c for c in run_calls if "menu" in c and "item" in c and "add-custom" in c]
    assert len(item_add_calls) == 4


def test_create_nav_menu_assigns_to_divi_primary_location():
    from generation.header_footer import generate_nav_menu
    capture = _make_capture_runner("10\n")
    runner = _make_runner()
    generate_nav_menu(SITE_PATH, runner=runner, capture_runner=capture)
    run_calls = _called_args(runner)
    assert _any_call_contains(run_calls, "menu", "location", "assign")


def test_create_nav_menu_passes_site_path_to_all_calls():
    from generation.header_footer import generate_nav_menu
    capture = _make_capture_runner("10\n")
    runner = _make_runner()
    generate_nav_menu(SITE_PATH, runner=runner, capture_runner=capture)
    for cmd in _called_args(capture) + _called_args(runner):
        assert any(SITE_PATH in arg for arg in cmd), f"Missing site path in: {cmd}"


def test_create_nav_menu_uses_wpcli_binary():
    from generation.header_footer import WP_CLI, generate_nav_menu
    capture = _make_capture_runner("10\n")
    runner = _make_runner()
    generate_nav_menu(SITE_PATH, runner=runner, capture_runner=capture)
    for cmd in _called_args(capture) + _called_args(runner):
        assert cmd[0] == WP_CLI, f"Expected WP_CLI as first arg, got: {cmd[0]}"


# ---------------------------------------------------------------------------
# generate_footer_social_links — footer social icons
# ---------------------------------------------------------------------------

def test_footer_social_sets_twitter_option():
    from generation.header_footer import generate_footer_social_links
    runner = _make_runner()
    generate_footer_social_links(
        SITE_PATH, {"twitter": "https://twitter.com/author"}, runner=runner
    )
    calls = _called_args(runner)
    assert _any_call_contains(calls, "twitter", "https://twitter.com/author")


def test_footer_social_sets_instagram_option():
    from generation.header_footer import generate_footer_social_links
    runner = _make_runner()
    generate_footer_social_links(
        SITE_PATH, {"instagram": "https://instagram.com/author"}, runner=runner
    )
    calls = _called_args(runner)
    assert _any_call_contains(calls, "instagram", "https://instagram.com/author")


def test_footer_social_sets_facebook_option():
    from generation.header_footer import generate_footer_social_links
    runner = _make_runner()
    generate_footer_social_links(
        SITE_PATH, {"facebook": "https://facebook.com/author"}, runner=runner
    )
    calls = _called_args(runner)
    assert _any_call_contains(calls, "facebook", "https://facebook.com/author")


def test_footer_social_sets_tiktok_option():
    from generation.header_footer import generate_footer_social_links
    runner = _make_runner()
    generate_footer_social_links(
        SITE_PATH, {"tiktok": "https://tiktok.com/@author"}, runner=runner
    )
    calls = _called_args(runner)
    assert _any_call_contains(calls, "tiktok", "https://tiktok.com/@author")


def test_footer_social_sets_youtube_option():
    from generation.header_footer import generate_footer_social_links
    runner = _make_runner()
    generate_footer_social_links(
        SITE_PATH, {"youtube": "https://youtube.com/author"}, runner=runner
    )
    calls = _called_args(runner)
    assert _any_call_contains(calls, "youtube", "https://youtube.com/author")


def test_footer_social_sets_goodreads_option():
    from generation.header_footer import generate_footer_social_links
    runner = _make_runner()
    generate_footer_social_links(
        SITE_PATH, {"goodreads": "https://goodreads.com/author"}, runner=runner
    )
    calls = _called_args(runner)
    assert _any_call_contains(calls, "goodreads", "https://goodreads.com/author")


def test_footer_social_with_no_links_makes_no_calls():
    from generation.header_footer import generate_footer_social_links
    runner = _make_runner()
    generate_footer_social_links(SITE_PATH, {}, runner=runner)
    assert runner.call_count == 0


def test_footer_social_partial_links_only_sets_present_ones():
    from generation.header_footer import generate_footer_social_links
    runner = _make_runner()
    generate_footer_social_links(SITE_PATH, SOCIAL_LINKS_PARTIAL, runner=runner)
    assert runner.call_count == len(SOCIAL_LINKS_PARTIAL)
    calls = _called_args(runner)
    assert _any_call_contains(calls, "twitter")
    assert _any_call_contains(calls, "goodreads")
    assert not _any_call_contains(calls, "instagram")
    assert not _any_call_contains(calls, "facebook")


def test_footer_social_all_six_links_makes_six_calls():
    from generation.header_footer import generate_footer_social_links
    runner = _make_runner()
    generate_footer_social_links(SITE_PATH, SOCIAL_LINKS_FULL, runner=runner)
    assert runner.call_count == 6


def test_footer_social_passes_site_path_to_all_calls():
    from generation.header_footer import generate_footer_social_links
    runner = _make_runner()
    generate_footer_social_links(SITE_PATH, SOCIAL_LINKS_PARTIAL, runner=runner)
    for cmd in _called_args(runner):
        assert any(SITE_PATH in arg for arg in cmd), f"Missing site path in: {cmd}"


def test_footer_social_uses_wpcli_binary():
    from generation.header_footer import WP_CLI, generate_footer_social_links
    runner = _make_runner()
    generate_footer_social_links(SITE_PATH, SOCIAL_LINKS_PARTIAL, runner=runner)
    for cmd in _called_args(runner):
        assert cmd[0] == WP_CLI, f"Expected WP_CLI as first arg, got: {cmd[0]}"


# ---------------------------------------------------------------------------
# setup_header_footer — orchestration
# ---------------------------------------------------------------------------

def test_setup_header_footer_creates_nav_menu():
    from generation.header_footer import setup_header_footer
    capture = _make_capture_runner("10\n")
    runner = _make_runner()
    setup_header_footer(SITE_PATH, {"social_links": {}}, runner=runner, capture_runner=capture)
    all_calls = _called_args(capture) + _called_args(runner)
    assert _any_call_contains(all_calls, "menu", "create")


def test_setup_header_footer_assigns_nav_location():
    from generation.header_footer import setup_header_footer
    capture = _make_capture_runner("10\n")
    runner = _make_runner()
    setup_header_footer(SITE_PATH, {"social_links": {}}, runner=runner, capture_runner=capture)
    run_calls = _called_args(runner)
    assert _any_call_contains(run_calls, "menu", "location", "assign")


def test_setup_header_footer_sets_social_links_when_present():
    from generation.header_footer import setup_header_footer
    capture = _make_capture_runner("10\n")
    runner = _make_runner()
    setup_header_footer(
        SITE_PATH,
        {"social_links": {"twitter": "https://twitter.com/author"}},
        runner=runner,
        capture_runner=capture,
    )
    run_calls = _called_args(runner)
    assert _any_call_contains(run_calls, "twitter")


def test_setup_header_footer_skips_social_when_empty():
    from generation.header_footer import setup_header_footer
    capture = _make_capture_runner("10\n")
    runner = _make_runner()
    setup_header_footer(SITE_PATH, {"social_links": {}}, runner=runner, capture_runner=capture)
    run_calls = _called_args(runner)
    # Should only contain menu-related calls (items + location assign), no social option patches
    social_calls = [
        c for c in run_calls
        if any(k in " ".join(c) for k in (
            "twitter", "instagram", "facebook", "tiktok", "youtube", "goodreads"
        ))
    ]
    assert social_calls == []


def test_setup_header_footer_with_no_social_links_key_uses_empty_dict():
    from generation.header_footer import setup_header_footer
    capture = _make_capture_runner("10\n")
    runner = _make_runner()
    # serialized_author without a social_links key — must not raise
    setup_header_footer(SITE_PATH, {}, runner=runner, capture_runner=capture)
    run_calls = _called_args(runner)
    social_calls = [
        c for c in run_calls
        if any(k in " ".join(c) for k in (
            "twitter", "instagram", "facebook", "tiktok", "youtube", "goodreads"
        ))
    ]
    assert social_calls == []
