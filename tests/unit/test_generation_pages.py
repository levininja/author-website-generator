"""Tests for generation/pages.py — all WP-CLI calls are mocked; no real WP install required."""

import json
import pytest
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

SITE_PATH = "/tmp/test-wp-site"


def _make_runner():
    return MagicMock(return_value=None)


def _called_args(mock) -> list[list[str]]:
    return [c.args[0] for c in mock.call_args_list]


def _meta_calls(runner) -> dict:
    """Return {meta_key: value} for all wp post meta update calls to runner."""
    result = {}
    for args_list in _called_args(runner):
        if (
            len(args_list) >= 7
            and args_list[1] == "post"
            and args_list[2] == "meta"
            and args_list[3] == "update"
        ):
            result[args_list[5]] = args_list[6]
    return result


def _option_calls(runner) -> dict:
    """Return {option_key: value} for all wp option update calls to runner."""
    result = {}
    for args_list in _called_args(runner):
        if (
            len(args_list) >= 5
            and args_list[1] == "option"
            and args_list[2] == "update"
        ):
            result[args_list[3]] = args_list[4]
    return result


def _page_create_calls(capture_runner) -> list[list[str]]:
    return [a for a in _called_args(capture_runner) if "--post_type=page" in a]


def _book_cpt_create_calls(capture_runner) -> list[list[str]]:
    return [a for a in _called_args(capture_runner) if "--post_type=awg_book" in a]


def _page_content_arg(call: list[str]) -> str:
    """Extract the value of the --post_content= arg from a create call."""
    for arg in call:
        if arg.startswith("--post_content="):
            return arg[len("--post_content="):]
    return ""


def _page_title_arg(call: list[str]) -> str:
    for arg in call:
        if arg.startswith("--post_title="):
            return arg[len("--post_title="):]
    return ""


def _page_name_arg(call: list[str]) -> str:
    for arg in call:
        if arg.startswith("--post_name="):
            return arg[len("--post_name="):]
    return ""


def _book_detail_page_calls(capture_runner) -> list[list[str]]:
    """Return page create calls that carry --post_name= (i.e. per-book detail pages)."""
    return [
        a for a in _page_create_calls(capture_runner)
        if any(arg.startswith("--post_name=") for arg in a)
    ]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

AUTHOR = {
    "id": "1",
    "name": "Jane Doe",
    "contact_email": "jane@example.com",
    "site_domain": "janedoe.com",
    "site_tagline": "Writes stories",
    "bio_short": "Jane Doe is an author.",
    "bio_long": "Jane Doe has been writing for 20 years.",
    "genres": ["Fiction", "Thriller"],
    "primary_color": "#FF0000",
    "secondary_color": "#0000FF",
    "newsletter_link": "https://newsletter.janedoe.com",
    "selected_template": "Classic",
    "headshot_url": "/media/headshot.jpg",
    "social_links": {
        "twitter": "https://twitter.com/janedoe",
        "instagram": "https://instagram.com/janedoe",
    },
}

BOOK = {
    "id": "10",
    "author_id": "1",
    "onboarding_position": 1,
    "title": "The Dark Forest",
    "cover_image_url": "/media/cover.jpg",
    "description": "A thrilling novel.",
    "buy_links": ["https://amazon.com/book1", "https://bookshop.org/book1"],
    "category": {"id": 1, "name": "Fiction"},
    "genre": {"id": 2, "name": "Thriller"},
    "subgenre": {"id": 3, "name": "Psychological Thriller"},
    "series": {
        "id": "5",
        "name": "The Forest Series",
        "total_books": 3,
        "is_complete": False,
    },
    "number_in_series": 1,
    "editorial_reviews": [
        {
            "reviewer_name": "The Times",
            "credentials": "Staff Reviewer",
            "quotation": "A masterpiece.",
            "original_review_url": "https://times.com/review1",
            "photo_url": None,
            "stars": 5,
            "is_starred_review": True,
        }
    ],
    "other_reviews": [
        {
            "reviewer_name": "BookLover99",
            "credentials": None,
            "quotation": "Loved it!",
            "original_review_url": None,
            "photo_url": None,
            "stars": 5,
            "is_starred_review": False,
        }
    ],
    "awards": [{"name": "Best Thriller 2024", "icon_url": "/media/award.png"}],
    "perfect_for": "Fans of dark fiction",
    "enjoy_if": "You liked Gone Girl",
    "sample_chapter_url": "/books/10/sample-chapter",
    "sample_chapter_name": "chapter1.pdf",
}

STANDALONE_BOOK = {
    "id": "11",
    "author_id": "1",
    "onboarding_position": 1,
    "title": "Standalone Novel",
    "cover_image_url": "/media/standalone-cover.jpg",
    "description": "A standalone book.",
    "buy_links": [],
    "category": {"id": 1, "name": "Fiction"},
    "genre": {"id": 2, "name": "Literary Fiction"},
    "subgenre": None,
    "series": None,
    "number_in_series": None,
    "editorial_reviews": [],
    "other_reviews": [],
    "awards": [],
    "perfect_for": "",
    "enjoy_if": "",
    "sample_chapter_url": None,
    "sample_chapter_name": "",
}

# 4 static pages (Home, About, Books, Contact); per-book detail pages and CPT records follow
_STATIC_PAGE_IDS = ["101", "102", "103", "104"]


def _run_generate(author=None, books=None):
    """Invoke generate_pages with mocked runners; return (runner, capture_runner)."""
    from generation.pages import generate_pages

    if author is None:
        author = AUTHOR
    if books is None:
        books = [BOOK]

    n = len(books)
    # IDs: 4 static pages, then N per-book detail page IDs, then N book CPT IDs
    book_detail_ids = [str(200 + i) for i in range(n)]
    book_cpt_ids = [str(300 + i) for i in range(n)]
    capture_ids = _STATIC_PAGE_IDS + book_detail_ids + book_cpt_ids

    runner = _make_runner()
    capture_runner = MagicMock(side_effect=capture_ids)

    generate_pages(
        site_path=SITE_PATH,
        serialized_author=author,
        serialized_books=books,
        runner=runner,
        capture_runner=capture_runner,
    )
    return runner, capture_runner


# ---------------------------------------------------------------------------
# Page creation — count and type
# ---------------------------------------------------------------------------

def test_five_pages_created_for_author_site():
    _, capture_runner = _run_generate()
    assert len(_page_create_calls(capture_runner)) == 5


def test_all_pages_created_with_publish_status():
    _, capture_runner = _run_generate()
    for call in _page_create_calls(capture_runner):
        assert "--post_status=publish" in call


def test_pages_created_with_porcelain_flag():
    _, capture_runner = _run_generate()
    for call in _page_create_calls(capture_runner):
        assert "--porcelain" in call


def test_home_page_created():
    _, capture_runner = _run_generate()
    titles = [_page_title_arg(c) for c in _page_create_calls(capture_runner)]
    assert "Home" in titles


def test_about_page_created():
    _, capture_runner = _run_generate()
    titles = [_page_title_arg(c) for c in _page_create_calls(capture_runner)]
    assert "About" in titles


def test_books_page_created():
    _, capture_runner = _run_generate()
    titles = [_page_title_arg(c) for c in _page_create_calls(capture_runner)]
    assert "Books" in titles


def test_contact_page_created():
    _, capture_runner = _run_generate()
    titles = [_page_title_arg(c) for c in _page_create_calls(capture_runner)]
    assert "Contact" in titles


def test_no_generic_book_detail_page_created():
    _, capture_runner = _run_generate()
    titles = [_page_title_arg(c) for c in _page_create_calls(capture_runner)]
    assert "Book Detail" not in titles


# ---------------------------------------------------------------------------
# Home page content
# ---------------------------------------------------------------------------

def _home_call(capture_runner):
    return next(c for c in _page_create_calls(capture_runner) if _page_title_arg(c) == "Home")


def test_home_page_content_includes_primary_color():
    _, capture_runner = _run_generate()
    content = _page_content_arg(_home_call(capture_runner))
    assert "#FF0000" in content


def test_home_page_content_includes_secondary_color():
    _, capture_runner = _run_generate()
    content = _page_content_arg(_home_call(capture_runner))
    assert "#0000FF" in content


def test_home_page_content_includes_genres():
    _, capture_runner = _run_generate()
    content = _page_content_arg(_home_call(capture_runner))
    assert "Fiction" in content
    assert "Thriller" in content


def test_home_page_content_includes_newsletter_link():
    _, capture_runner = _run_generate()
    content = _page_content_arg(_home_call(capture_runner))
    assert "https://newsletter.janedoe.com" in content


def test_home_page_content_includes_social_links():
    _, capture_runner = _run_generate()
    content = _page_content_arg(_home_call(capture_runner))
    assert "https://twitter.com/janedoe" in content


def test_home_page_content_includes_template_name():
    _, capture_runner = _run_generate()
    content = _page_content_arg(_home_call(capture_runner))
    assert "Classic" in content


# ---------------------------------------------------------------------------
# About page content
# ---------------------------------------------------------------------------

def _about_call(capture_runner):
    return next(c for c in _page_create_calls(capture_runner) if _page_title_arg(c) == "About")


def test_about_page_content_includes_bio_short():
    _, capture_runner = _run_generate()
    content = _page_content_arg(_about_call(capture_runner))
    assert "Jane Doe is an author." in content


def test_about_page_content_includes_bio_long_when_present():
    _, capture_runner = _run_generate()
    content = _page_content_arg(_about_call(capture_runner))
    assert "Jane Doe has been writing for 20 years." in content


def test_about_page_content_includes_headshot_img_tag():
    _, capture_runner = _run_generate()
    content = _page_content_arg(_about_call(capture_runner))
    assert "/media/headshot.jpg" in content
    assert "<img" in content


def test_about_page_omits_headshot_img_tag_when_headshot_url_is_none():
    author = {**AUTHOR, "headshot_url": None}
    _, capture_runner = _run_generate(author=author)
    content = _page_content_arg(_about_call(capture_runner))
    assert "<img" not in content


def test_about_page_omits_bio_long_when_empty():
    author = {**AUTHOR, "bio_long": ""}
    _, capture_runner = _run_generate(author=author)
    content = _page_content_arg(_about_call(capture_runner))
    # bio_long is empty string; should not produce a noisy extra paragraph
    assert content.count("<p>") <= 1


# ---------------------------------------------------------------------------
# Contact page content
# ---------------------------------------------------------------------------

def _contact_call(capture_runner):
    return next(c for c in _page_create_calls(capture_runner) if _page_title_arg(c) == "Contact")


def test_contact_page_content_includes_author_name():
    _, capture_runner = _run_generate()
    content = _page_content_arg(_contact_call(capture_runner))
    assert "Jane Doe" in content


def test_contact_page_content_includes_contact_email():
    _, capture_runner = _run_generate()
    content = _page_content_arg(_contact_call(capture_runner))
    assert "jane@example.com" in content


# ---------------------------------------------------------------------------
# Front page setup
# ---------------------------------------------------------------------------

def test_home_page_id_passed_to_page_on_front_option():
    runner, capture_runner = _run_generate()
    # Capture runner returns "101" for the first call (Home page)
    options = _option_calls(runner)
    assert options.get("page_on_front") == "101"


def test_show_on_front_set_to_page():
    runner, _ = _run_generate()
    options = _option_calls(runner)
    assert options.get("show_on_front") == "page"


# ---------------------------------------------------------------------------
# Book CPT creation
# ---------------------------------------------------------------------------

def test_one_cpt_record_created_per_book():
    _, capture_runner = _run_generate(books=[BOOK])
    assert len(_book_cpt_create_calls(capture_runner)) == 1


def test_cpt_records_created_for_each_book_in_list():
    _, capture_runner = _run_generate(books=[BOOK, STANDALONE_BOOK])
    assert len(_book_cpt_create_calls(capture_runner)) == 2


def test_book_cpt_uses_book_title_as_post_title():
    _, capture_runner = _run_generate()
    cpt_call = _book_cpt_create_calls(capture_runner)[0]
    assert "--post_title=The Dark Forest" in cpt_call


def test_book_cpt_created_with_publish_status():
    _, capture_runner = _run_generate()
    cpt_call = _book_cpt_create_calls(capture_runner)[0]
    assert "--post_status=publish" in cpt_call


def test_book_cpt_created_with_porcelain_flag():
    _, capture_runner = _run_generate()
    cpt_call = _book_cpt_create_calls(capture_runner)[0]
    assert "--porcelain" in cpt_call


# ---------------------------------------------------------------------------
# Book meta — string fields
# ---------------------------------------------------------------------------

def test_book_meta_cover_image_set():
    runner, _ = _run_generate()
    meta = _meta_calls(runner)
    assert meta.get("_awg_cover_image") == "/media/cover.jpg"


def test_book_meta_genre_set():
    runner, _ = _run_generate()
    meta = _meta_calls(runner)
    assert meta.get("_awg_genre") == "Thriller"


def test_book_meta_subgenre_set_when_present():
    runner, _ = _run_generate()
    meta = _meta_calls(runner)
    assert meta.get("_awg_subgenre") == "Psychological Thriller"


def test_book_meta_category_set():
    runner, _ = _run_generate()
    meta = _meta_calls(runner)
    assert meta.get("_awg_category") == "Fiction"


def test_book_meta_perfect_for_set():
    runner, _ = _run_generate()
    meta = _meta_calls(runner)
    assert meta.get("_awg_perfect_for") == "Fans of dark fiction"


def test_book_meta_enjoy_if_set():
    runner, _ = _run_generate()
    meta = _meta_calls(runner)
    assert meta.get("_awg_enjoy_if") == "You liked Gone Girl"


def test_book_meta_sample_chapter_url_set_when_present():
    runner, _ = _run_generate()
    meta = _meta_calls(runner)
    assert meta.get("_awg_sample_chapter_url") == "/books/10/sample-chapter"


def test_book_meta_sample_chapter_name_set():
    runner, _ = _run_generate()
    meta = _meta_calls(runner)
    assert meta.get("_awg_sample_chapter_name") == "chapter1.pdf"


# ---------------------------------------------------------------------------
# Book meta — integer fields
# ---------------------------------------------------------------------------

def test_book_meta_onboarding_position_set():
    runner, _ = _run_generate()
    meta = _meta_calls(runner)
    assert meta.get("_awg_onboarding_position") == "1"


def test_book_meta_number_in_series_set_when_in_series():
    runner, _ = _run_generate()
    meta = _meta_calls(runner)
    assert meta.get("_awg_number_in_series") == "1"


def test_book_meta_series_total_books_set_when_in_series():
    runner, _ = _run_generate()
    meta = _meta_calls(runner)
    assert meta.get("_awg_series_total_books") == "3"


# ---------------------------------------------------------------------------
# Book meta — boolean fields
# ---------------------------------------------------------------------------

def test_book_meta_is_not_standalone_when_book_is_in_series():
    runner, _ = _run_generate()
    meta = _meta_calls(runner)
    assert meta.get("_awg_is_standalone") == "0"


def test_book_meta_series_is_not_complete():
    runner, _ = _run_generate()
    meta = _meta_calls(runner)
    assert meta.get("_awg_series_is_complete") == "0"


def test_book_meta_series_is_complete_when_flag_is_true():
    book = {**BOOK, "series": {**BOOK["series"], "is_complete": True}}
    runner, _ = _run_generate(books=[book])
    meta = _meta_calls(runner)
    assert meta.get("_awg_series_is_complete") == "1"


def test_book_meta_is_standalone_when_no_series():
    runner, _ = _run_generate(books=[STANDALONE_BOOK])
    meta = _meta_calls(runner)
    assert meta.get("_awg_is_standalone") == "1"


# ---------------------------------------------------------------------------
# Book meta — series name
# ---------------------------------------------------------------------------

def test_book_meta_series_name_set_when_in_series():
    runner, _ = _run_generate()
    meta = _meta_calls(runner)
    assert meta.get("_awg_series_name") == "The Forest Series"


# ---------------------------------------------------------------------------
# Book meta — JSON collection fields
# ---------------------------------------------------------------------------

def test_book_meta_buy_links_stored_as_json_string():
    runner, _ = _run_generate()
    meta = _meta_calls(runner)
    raw = meta.get("_awg_buy_links")
    assert raw is not None
    parsed = json.loads(raw)
    assert "https://amazon.com/book1" in parsed


def test_book_meta_editorial_reviews_stored_as_json_string():
    runner, _ = _run_generate()
    meta = _meta_calls(runner)
    raw = meta.get("_awg_editorial_reviews")
    assert raw is not None
    parsed = json.loads(raw)
    assert len(parsed) == 1
    assert parsed[0]["reviewer_name"] == "The Times"


def test_book_meta_reader_reviews_stored_as_json_string():
    runner, _ = _run_generate()
    meta = _meta_calls(runner)
    raw = meta.get("_awg_reader_reviews")
    assert raw is not None
    parsed = json.loads(raw)
    assert len(parsed) == 1
    assert parsed[0]["reviewer_name"] == "BookLover99"


def test_book_meta_awards_stored_as_json_string():
    runner, _ = _run_generate()
    meta = _meta_calls(runner)
    raw = meta.get("_awg_awards")
    assert raw is not None
    parsed = json.loads(raw)
    assert len(parsed) == 1
    assert parsed[0]["name"] == "Best Thriller 2024"


# ---------------------------------------------------------------------------
# Optional field handling — no crash when fields absent
# ---------------------------------------------------------------------------

def test_no_crash_when_subgenre_is_none():
    runner, _ = _run_generate(books=[STANDALONE_BOOK])
    meta = _meta_calls(runner)
    assert "_awg_subgenre" not in meta


def test_no_crash_when_series_is_none():
    runner, _ = _run_generate(books=[STANDALONE_BOOK])
    meta = _meta_calls(runner)
    assert "_awg_series_name" not in meta
    assert "_awg_number_in_series" not in meta
    assert "_awg_series_total_books" not in meta
    assert "_awg_series_is_complete" not in meta


def test_no_crash_when_headshot_url_is_none():
    author = {**AUTHOR, "headshot_url": None}
    _run_generate(author=author)  # must not raise


def test_no_crash_when_sample_chapter_url_is_none():
    runner, _ = _run_generate(books=[STANDALONE_BOOK])
    meta = _meta_calls(runner)
    assert "_awg_sample_chapter_url" not in meta


def test_no_crash_when_books_list_is_empty():
    runner, capture_runner = _run_generate(books=[])
    assert len(_book_cpt_create_calls(capture_runner)) == 0


def test_empty_buy_links_stored_as_empty_json_array():
    runner, _ = _run_generate(books=[STANDALONE_BOOK])
    meta = _meta_calls(runner)
    raw = meta.get("_awg_buy_links")
    assert raw is not None
    assert json.loads(raw) == []


# ---------------------------------------------------------------------------
# WP-CLI compliance — path and allow-root on every call
# ---------------------------------------------------------------------------

def test_all_capture_runner_calls_include_site_path():
    _, capture_runner = _run_generate()
    for args_list in _called_args(capture_runner):
        assert any(SITE_PATH in arg for arg in args_list), (
            f"Missing --path in capture_runner call: {args_list}"
        )


def test_all_runner_calls_include_site_path():
    runner, _ = _run_generate()
    for args_list in _called_args(runner):
        assert any(SITE_PATH in arg for arg in args_list), (
            f"Missing --path in runner call: {args_list}"
        )


def test_all_capture_runner_calls_include_allow_root():
    _, capture_runner = _run_generate()
    for args_list in _called_args(capture_runner):
        assert "--allow-root" in args_list, (
            f"Missing --allow-root in capture_runner call: {args_list}"
        )


def test_all_runner_calls_include_allow_root():
    runner, _ = _run_generate()
    for args_list in _called_args(runner):
        assert "--allow-root" in args_list, (
            f"Missing --allow-root in runner call: {args_list}"
        )


def test_all_wp_cli_calls_use_wp_cli_binary():
    from generation.pages import WP_CLI
    runner, capture_runner = _run_generate()
    for args_list in _called_args(runner) + _called_args(capture_runner):
        assert args_list[0] == WP_CLI, (
            f"First arg should be WP_CLI path, got: {args_list[0]}"
        )


# ---------------------------------------------------------------------------
# F027 — slug generation (pure function, no WP-CLI)
# ---------------------------------------------------------------------------

def test_slugify_title_basic_case():
    from generation.pages import slugify_title
    assert slugify_title("The Dark Forest") == "the-dark-forest"


def test_slugify_title_with_apostrophe_punctuation():
    from generation.pages import slugify_title
    assert slugify_title("The Dragon's Eye") == "the-dragons-eye"


def test_slugify_title_with_numbers():
    from generation.pages import slugify_title
    assert slugify_title("Book 2: Return") == "book-2-return"


def test_slugify_title_all_punctuation_produces_fallback():
    from generation.pages import slugify_title
    assert slugify_title("!!!") == "book"


def test_slugify_title_consecutive_spaces_collapse_to_single_hyphen():
    from generation.pages import slugify_title
    assert slugify_title("Hello   World") == "hello-world"


def test_slugify_title_leading_and_trailing_hyphens_stripped():
    from generation.pages import slugify_title
    # A title that starts/ends with punctuation should not produce leading/trailing hyphens
    result = slugify_title("!Hello World!")
    assert not result.startswith("-")
    assert not result.endswith("-")


# ---------------------------------------------------------------------------
# F027 — slug collision handling
# ---------------------------------------------------------------------------

def test_slug_collision_two_books_same_base_slug():
    from generation.pages import _assign_slugs
    books = [{"title": "Fire"}, {"title": "Fire!"}]
    slugs = [slug for _, slug in _assign_slugs(books)]
    assert slugs == ["fire", "fire-2"]


def test_slug_collision_three_books_same_base_slug():
    from generation.pages import _assign_slugs
    books = [{"title": "Fire"}, {"title": "Fire!"}, {"title": "Fire!!"}]
    slugs = [slug for _, slug in _assign_slugs(books)]
    assert slugs == ["fire", "fire-2", "fire-3"]


def test_slug_collision_only_on_third_book():
    from generation.pages import _assign_slugs
    books = [{"title": "Fire"}, {"title": "Water"}, {"title": "Fire!"}]
    slugs = [slug for _, slug in _assign_slugs(books)]
    assert slugs == ["fire", "water", "fire-2"]


def test_slug_no_collision_distinct_titles():
    from generation.pages import _assign_slugs
    books = [{"title": "Alpha"}, {"title": "Beta"}]
    slugs = [slug for _, slug in _assign_slugs(books)]
    assert slugs == ["alpha", "beta"]


# ---------------------------------------------------------------------------
# F027 — per-book detail pages
# ---------------------------------------------------------------------------

def test_one_detail_page_created_per_book():
    _, capture_runner = _run_generate(books=[BOOK])
    assert len(_book_detail_page_calls(capture_runner)) == 1


def test_two_detail_pages_created_for_two_books():
    _, capture_runner = _run_generate(books=[BOOK, STANDALONE_BOOK])
    assert len(_book_detail_page_calls(capture_runner)) == 2


def test_zero_detail_pages_created_when_no_books():
    _, capture_runner = _run_generate(books=[])
    assert len(_book_detail_page_calls(capture_runner)) == 0


def test_book_detail_page_title_matches_book_title():
    _, capture_runner = _run_generate(books=[BOOK])
    detail_call = _book_detail_page_calls(capture_runner)[0]
    assert _page_title_arg(detail_call) == "The Dark Forest"


def test_book_detail_page_uses_slug_derived_from_title():
    _, capture_runner = _run_generate(books=[BOOK])
    detail_call = _book_detail_page_calls(capture_runner)[0]
    assert _page_name_arg(detail_call) == "the-dark-forest"


def test_book_detail_page_content_has_book_detail_div():
    _, capture_runner = _run_generate(books=[BOOK])
    detail_call = _book_detail_page_calls(capture_runner)[0]
    assert '<div class="book-detail">' in _page_content_arg(detail_call)


def test_book_detail_pages_created_with_publish_status():
    _, capture_runner = _run_generate(books=[BOOK])
    for call in _book_detail_page_calls(capture_runner):
        assert "--post_status=publish" in call


def test_book_detail_pages_created_with_porcelain_flag():
    _, capture_runner = _run_generate(books=[BOOK])
    for call in _book_detail_page_calls(capture_runner):
        assert "--porcelain" in call


def test_book_detail_page_second_book_uses_collision_slug():
    books = [{"title": "Fire", **{k: v for k, v in STANDALONE_BOOK.items() if k != "title"}},
             {"title": "Fire!", **{k: v for k, v in STANDALONE_BOOK.items() if k != "title"}}]
    _, capture_runner = _run_generate(books=books)
    detail_calls = _book_detail_page_calls(capture_runner)
    assert _page_name_arg(detail_calls[0]) == "fire"
    assert _page_name_arg(detail_calls[1]) == "fire-2"


# ---------------------------------------------------------------------------
# F027 — Books listing page links
# ---------------------------------------------------------------------------

def _books_call(capture_runner):
    return next(c for c in _page_create_calls(capture_runner) if _page_title_arg(c) == "Books")


def test_books_listing_page_link_format():
    _, capture_runner = _run_generate(books=[BOOK])
    content = _page_content_arg(_books_call(capture_runner))
    assert '<a href="/the-dark-forest/">The Dark Forest</a>' in content


def test_books_listing_page_contains_links_to_all_books():
    _, capture_runner = _run_generate(books=[BOOK, STANDALONE_BOOK])
    content = _page_content_arg(_books_call(capture_runner))
    assert '<a href="/the-dark-forest/">The Dark Forest</a>' in content
    assert '<a href="/standalone-novel/">Standalone Novel</a>' in content


def test_books_listing_page_wrapped_in_ul():
    _, capture_runner = _run_generate(books=[BOOK])
    content = _page_content_arg(_books_call(capture_runner))
    assert content.startswith("<ul>")
    assert content.endswith("</ul>")


def test_books_listing_page_items_wrapped_in_li():
    _, capture_runner = _run_generate(books=[BOOK])
    content = _page_content_arg(_books_call(capture_runner))
    assert "<li>" in content


def test_empty_books_list_listing_page_still_created():
    _, capture_runner = _run_generate(books=[])
    titles = [_page_title_arg(c) for c in _page_create_calls(capture_runner)]
    assert "Books" in titles


def test_empty_books_list_listing_page_has_empty_ul():
    _, capture_runner = _run_generate(books=[])
    content = _page_content_arg(_books_call(capture_runner))
    assert "<ul>" in content
    assert "<li>" not in content
