"""Tests for generation/books_cpt.py — no WordPress install required; tests inspect written file content."""

import pytest
from pathlib import Path

MU_PLUGIN_REL = "wp-content/mu-plugins/awg-books.php"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_plugin(site_path: Path) -> str:
    return (site_path / MU_PLUGIN_REL).read_text()


def _block_around_key(content: str, meta_key: str, radius: int = 200) -> str:
    """Return a substring of content centered on meta_key, radius chars each side."""
    idx = content.index(meta_key)
    return content[max(0, idx - radius) : idx + radius]


# ---------------------------------------------------------------------------
# File creation and path
# ---------------------------------------------------------------------------

def test_creates_plugin_file_at_correct_path(tmp_path):
    from generation.books_cpt import write_books_cpt
    write_books_cpt(str(tmp_path))
    assert (tmp_path / MU_PLUGIN_REL).exists()


def test_creates_mu_plugins_dir_when_missing(tmp_path):
    from generation.books_cpt import write_books_cpt
    site = tmp_path / "fresh-site"
    site.mkdir()
    assert not (site / "wp-content" / "mu-plugins").exists()
    write_books_cpt(str(site))
    assert (site / "wp-content" / "mu-plugins").is_dir()


def test_plugin_file_starts_with_php_open_tag(tmp_path):
    from generation.books_cpt import write_books_cpt
    write_books_cpt(str(tmp_path))
    assert _read_plugin(tmp_path).startswith("<?php")


def test_write_is_idempotent(tmp_path):
    from generation.books_cpt import write_books_cpt
    write_books_cpt(str(tmp_path))
    first = _read_plugin(tmp_path)
    write_books_cpt(str(tmp_path))
    second = _read_plugin(tmp_path)
    assert first == second


# ---------------------------------------------------------------------------
# CPT registration
# ---------------------------------------------------------------------------

def test_registers_awg_book_post_type(tmp_path):
    from generation.books_cpt import write_books_cpt
    write_books_cpt(str(tmp_path))
    content = _read_plugin(tmp_path)
    assert "register_post_type" in content
    assert "awg_book" in content


# ---------------------------------------------------------------------------
# Post meta — all keys present
# ---------------------------------------------------------------------------

ALL_META_KEYS = [
    "_awg_cover_image",
    "_awg_genre",
    "_awg_subgenre",
    "_awg_category",
    "_awg_series_name",
    "_awg_perfect_for",
    "_awg_enjoy_if",
    "_awg_sample_chapter_url",
    "_awg_sample_chapter_name",
    "_awg_onboarding_position",
    "_awg_number_in_series",
    "_awg_series_total_books",
    "_awg_is_standalone",
    "_awg_series_is_complete",
    "_awg_buy_links",
    "_awg_editorial_reviews",
    "_awg_reader_reviews",
    "_awg_awards",
]


@pytest.mark.parametrize("meta_key", ALL_META_KEYS)
def test_meta_key_is_registered(tmp_path, meta_key):
    from generation.books_cpt import write_books_cpt
    write_books_cpt(str(tmp_path))
    content = _read_plugin(tmp_path)
    assert "register_post_meta" in content
    assert meta_key in content


# ---------------------------------------------------------------------------
# Post meta — field types
# ---------------------------------------------------------------------------

STRING_FIELDS = [
    "_awg_cover_image",
    "_awg_genre",
    "_awg_subgenre",
    "_awg_category",
    "_awg_series_name",
    "_awg_perfect_for",
    "_awg_enjoy_if",
    "_awg_sample_chapter_url",
    "_awg_sample_chapter_name",
]

INTEGER_FIELDS = [
    "_awg_onboarding_position",
    "_awg_number_in_series",
    "_awg_series_total_books",
]

BOOLEAN_FIELDS = [
    "_awg_is_standalone",
    "_awg_series_is_complete",
]

# JSON collections are stored as serialized string values.
JSON_AS_STRING_FIELDS = [
    "_awg_buy_links",
    "_awg_editorial_reviews",
    "_awg_reader_reviews",
    "_awg_awards",
]


@pytest.mark.parametrize("meta_key", STRING_FIELDS)
def test_string_fields_are_typed_as_string(tmp_path, meta_key):
    from generation.books_cpt import write_books_cpt
    write_books_cpt(str(tmp_path))
    content = _read_plugin(tmp_path)
    block = _block_around_key(content, meta_key)
    assert "'string'" in block or '"string"' in block


@pytest.mark.parametrize("meta_key", INTEGER_FIELDS)
def test_integer_fields_are_typed_as_integer(tmp_path, meta_key):
    from generation.books_cpt import write_books_cpt
    write_books_cpt(str(tmp_path))
    content = _read_plugin(tmp_path)
    block = _block_around_key(content, meta_key)
    assert "'integer'" in block or '"integer"' in block


@pytest.mark.parametrize("meta_key", BOOLEAN_FIELDS)
def test_boolean_fields_are_typed_as_boolean(tmp_path, meta_key):
    from generation.books_cpt import write_books_cpt
    write_books_cpt(str(tmp_path))
    content = _read_plugin(tmp_path)
    block = _block_around_key(content, meta_key)
    assert "'boolean'" in block or '"boolean"' in block


@pytest.mark.parametrize("meta_key", JSON_AS_STRING_FIELDS)
def test_json_collection_fields_are_typed_as_string(tmp_path, meta_key):
    from generation.books_cpt import write_books_cpt
    write_books_cpt(str(tmp_path))
    content = _read_plugin(tmp_path)
    block = _block_around_key(content, meta_key)
    assert "'string'" in block or '"string"' in block
