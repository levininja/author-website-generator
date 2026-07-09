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

# 5 pages are always created; one ID per book is appended
_PAGE_IDS = ["101", "102", "103", "104", "105"]


def _run_generate(author=None, books=None):
    """Invoke generate_pages with mocked runners; return (runner, capture_runner)."""
    from generation.pages import generate_pages

    if author is None:
        author = AUTHOR
    if books is None:
        books = [BOOK]

    capture_ids = _PAGE_IDS + [str(200 + i) for i in range(1, len(books) + 1)]
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


def test_book_detail_page_created():
    _, capture_runner = _run_generate()
    titles = [_page_title_arg(c) for c in _page_create_calls(capture_runner)]
    assert any("Book Detail" in t for t in titles)


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
