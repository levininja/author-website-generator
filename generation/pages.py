"""Generate WordPress pages and book CPT records for an author's site via WP-CLI."""

import json
from typing import Callable, Optional, Sequence

from generation.subprocess_runner import default_capture_runner, default_runner

WP_CLI = "/usr/local/bin/wp"


def _wp_flags(site_path: str) -> list[str]:
    return [f"--path={site_path}", "--allow-root"]


def _create_page(capture, site_path: str, title: str, content: str) -> str:
    """Create a WordPress page and return its post ID (as a string)."""
    return capture([
        WP_CLI, "post", "create",
        "--post_type=page",
        f"--post_title={title}",
        f"--post_content={content}",
        "--post_status=publish",
        "--porcelain",
        *_wp_flags(site_path),
    ]).strip()


def _create_book_cpt(capture, site_path: str, book: dict) -> str:
    """Create an awg_book CPT record and return its post ID."""
    return capture([
        WP_CLI, "post", "create",
        "--post_type=awg_book",
        f"--post_title={book['title']}",
        f"--post_content={book.get('description', '')}",
        "--post_status=publish",
        "--porcelain",
        *_wp_flags(site_path),
    ]).strip()


def _set_meta(run, site_path: str, post_id: str, key: str, value: str) -> None:
    run([WP_CLI, "post", "meta", "update", post_id, key, value, *_wp_flags(site_path)])


def _set_book_meta(run, site_path: str, post_id: str, book: dict) -> None:
    """Populate all registered meta fields on a book CPT record."""
    series = book.get("series")
    subgenre = book.get("subgenre")

    simple_fields: dict[str, Optional[str]] = {
        "_awg_cover_image": book.get("cover_image_url"),
        "_awg_genre": book.get("genre", {}).get("name"),
        "_awg_category": book.get("category", {}).get("name"),
        "_awg_perfect_for": book.get("perfect_for") or None,
        "_awg_enjoy_if": book.get("enjoy_if") or None,
        "_awg_sample_chapter_url": book.get("sample_chapter_url"),
        "_awg_sample_chapter_name": book.get("sample_chapter_name") or None,
        "_awg_onboarding_position": str(book.get("onboarding_position", 1)),
        "_awg_is_standalone": "0" if series else "1",
    }

    if subgenre:
        simple_fields["_awg_subgenre"] = subgenre["name"]

    if series:
        simple_fields["_awg_series_name"] = series["name"]
        simple_fields["_awg_number_in_series"] = str(book.get("number_in_series", ""))
        simple_fields["_awg_series_total_books"] = str(series["total_books"])
        simple_fields["_awg_series_is_complete"] = "1" if series["is_complete"] else "0"

    for key, value in simple_fields.items():
        if value is not None:
            _set_meta(run, site_path, post_id, key, value)

    # JSON collection fields are always written (empty list → "[]")
    for key, value in [
        ("_awg_buy_links", book.get("buy_links", [])),
        ("_awg_editorial_reviews", book.get("editorial_reviews", [])),
        ("_awg_reader_reviews", book.get("other_reviews", [])),
        ("_awg_awards", book.get("awards", [])),
    ]:
        _set_meta(run, site_path, post_id, key, json.dumps(value))


def _home_page_content(author: dict) -> str:
    primary = author.get("primary_color", "")
    secondary = author.get("secondary_color", "")
    genres = ", ".join(author.get("genres", []))
    newsletter = author.get("newsletter_link", "")
    social_links = author.get("social_links", {})
    template = author.get("selected_template", "Classic")

    social_html = "".join(
        f'<a href="{url}">{name}</a> ' for name, url in social_links.items()
    )

    return (
        f'<div class="color-swatches">'
        f'<span class="swatch" style="background:{primary}"></span>'
        f'<span class="swatch" style="background:{secondary}"></span>'
        f"</div>"
        f'<p class="genres">{genres}</p>'
        f'<p class="newsletter"><a href="{newsletter}">Newsletter</a></p>'
        f'<div class="social-links">{social_html}</div>'
        f"<!-- Template: {template} -->"
    )


def _about_page_content(author: dict) -> str:
    bio_short = author.get("bio_short", "")
    bio_long = author.get("bio_long", "")
    headshot_url = author.get("headshot_url")

    headshot_html = f'<img src="{headshot_url}" alt="Author headshot" />' if headshot_url else ""
    bio_long_html = f"<p>{bio_long}</p>" if bio_long else ""

    return f"{headshot_html}<p>{bio_short}</p>{bio_long_html}"


def _books_page_content() -> str:
    return '<div class="books-listing"></div>'


def _contact_page_content(author: dict) -> str:
    name = author.get("name", "")
    email = author.get("contact_email", "")
    return f'<p>{name}</p><p><a href="mailto:{email}">{email}</a></p>'


def _book_detail_page_content() -> str:
    return '<div class="book-detail"></div>'


def generate_pages(
    site_path: str,
    serialized_author: dict,
    serialized_books: list,
    runner: Optional[Callable[[Sequence[str]], None]] = None,
    capture_runner: Optional[Callable[[Sequence[str]], str]] = None,
) -> None:
    """Create all author pages and book CPT records in the WordPress site at site_path."""
    run = runner or default_runner
    capture = capture_runner or default_capture_runner

    home_id = _create_page(capture, site_path, "Home", _home_page_content(serialized_author))
    _create_page(capture, site_path, "About", _about_page_content(serialized_author))
    _create_page(capture, site_path, "Books", _books_page_content())
    _create_page(capture, site_path, "Contact", _contact_page_content(serialized_author))
    _create_page(capture, site_path, "Book Detail", _book_detail_page_content())

    run([WP_CLI, "option", "update", "page_on_front", home_id, *_wp_flags(site_path)])
    run([WP_CLI, "option", "update", "show_on_front", "page", *_wp_flags(site_path)])

    for book in serialized_books:
        book_id = _create_book_cpt(capture, site_path, book)
        _set_book_meta(run, site_path, book_id, book)
