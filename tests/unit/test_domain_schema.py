"""Tests for the semantic author, book, genre, and series schema."""

import pytest
from django.db import IntegrityError, connection, transaction

from onboarding.models import (
    Author,
    AuthorCategory,
    AuthorGenre,
    AuthorSubgenre,
    Book,
    BookAward,
    BookCategory,
    BookGenre,
    BookReview,
    BookSubgenre,
    Series,
)
from onboarding.services import sync_genre_catalog

pytestmark = pytest.mark.django_db


GENRE_TREE = {
    "Fiction": {
        "Science Fiction": ["Cyberpunk", "Space Opera"],
    },
    "Nonfiction": {
        "Biography & Memoir": ["Biography", "Memoir"],
    },
}


def create_author():
    return Author.objects.create(
        name="Jane Doe",
        contact_email="contact@example.com",
        site_domain="janedoe.com",
    )


def create_genre_path():
    category = BookCategory.objects.get(name="Fiction")
    genre = BookGenre.objects.get(category=category, name="Science Fiction")
    subgenre = BookSubgenre.objects.get(genre=genre, name="Cyberpunk")
    return category, genre, subgenre


def test_domain_models_use_semantic_table_names():
    assert Author._meta.db_table == "author"
    assert AuthorCategory._meta.db_table == "author_category"
    assert AuthorGenre._meta.db_table == "author_genre"
    assert AuthorSubgenre._meta.db_table == "author_subgenre"
    assert BookCategory._meta.db_table == "genre_category"
    assert BookGenre._meta.db_table == "genre"
    assert BookSubgenre._meta.db_table == "genre_subgenre"
    assert Series._meta.db_table == "book_series"
    assert Book._meta.db_table == "book"
    assert BookReview._meta.db_table == "book_review"
    assert BookAward._meta.db_table == "book_award"


def test_obsolete_submission_and_prefixed_book_tables_are_removed():
    tables = set(connection.introspection.table_names())

    assert "onboarding_onboardingsubmission" not in tables
    assert "onboarding_onboardinggenre" not in tables
    assert "onboarding_book" not in tables
    assert {
        "author",
        "book",
        "book_series",
        "genre",
        "genre_subgenre",
        "book_review",
    } <= tables
    assert {
        "book_editorial_review",
        "book_endorsement",
        "book_review_excerpt",
    }.isdisjoint(tables)


def test_genre_catalog_is_normalized_into_three_related_tables():
    sync_genre_catalog(GENRE_TREE)

    cyberpunk = BookSubgenre.objects.select_related("genre__category").get(
        name="Cyberpunk"
    )
    assert cyberpunk.genre.name == "Science Fiction"
    assert cyberpunk.genre.category.name == "Fiction"
    assert BookCategory.objects.count() == 2
    assert BookGenre.objects.count() == 2
    assert BookSubgenre.objects.count() == 4


def test_author_can_select_items_at_every_genre_hierarchy_level():
    author = create_author()
    category, genre, subgenre = create_genre_path()

    AuthorCategory.objects.create(
        author=author,
        category=category,
        display_position=1,
    )
    AuthorGenre.objects.create(author=author, genre=genre, display_position=2)
    AuthorSubgenre.objects.create(
        author=author,
        subgenre=subgenre,
        display_position=3,
    )

    assert list(author.selected_categories.values_list("name", flat=True)) == [
        "Fiction"
    ]
    assert list(author.selected_genres.values_list("name", flat=True)) == [
        "Science Fiction"
    ]
    assert list(author.selected_subgenres.values_list("name", flat=True)) == [
        "Cyberpunk"
    ]


def test_book_references_author_genre_subgenre_and_optional_series():
    author = create_author()
    _, genre, subgenre = create_genre_path()
    series = Series.objects.create(
        author=author,
        name="The Signal Cycle",
        total_books=4,
        is_complete=True,
    )

    book = Book.objects.create(
        author=author,
        onboarding_position=1,
        title="The Midnight Code",
        cover_image="covers/test.png",
        description="A technological thriller.",
        buy_links=["https://example.com/buy"],
        genre=genre,
        subgenre=subgenre,
        series=series,
        number_in_series=2,
    )

    assert book.author == author
    assert book.genre_id == genre.pk
    assert book.subgenre_id == subgenre.pk
    assert book.genre.category.name == "Fiction"
    assert book.series == series
    assert book.series.total_books == 4
    assert book.series.is_complete is True
    assert not hasattr(book, "submission_id")
    assert not hasattr(book, "position")
    assert not hasattr(book, "category")
    assert not hasattr(book, "series_name")
    assert not hasattr(book, "series_length")
    assert not hasattr(book, "book_number")
    assert not hasattr(book, "sample_chapter")
    assert not hasattr(book, "sample_chapter_original_name")


def test_requested_display_and_file_column_names_are_used():
    for model in (
        AuthorCategory,
        AuthorGenre,
        AuthorSubgenre,
        BookAward,
        BookReview,
    ):
        field_names = {field.name for field in model._meta.fields}
        assert "display_position" in field_names
        assert "position" not in field_names

    award_fields = {field.name for field in BookAward._meta.fields}
    assert "icon_path" in award_fields
    assert "icon" not in award_fields

    book_fields = {field.name for field in Book._meta.fields}
    assert {"number_in_series", "sample_chapter_name", "sample_chapter_path"} <= (
        book_fields
    )
    assert Book._meta.get_field("subgenre").null is True


def test_book_review_combines_editorial_and_other_review_fields():
    field_names = {field.name for field in BookReview._meta.fields}

    assert {
        "book",
        "display_position",
        "is_editorial",
        "reviewer_name",
        "credentials",
        "quotation",
        "original_review_url",
        "photo_path",
        "stars",
        "is_starred_review",
    } <= field_names
    assert BookReview._meta.get_field("credentials").null is True
    assert BookReview._meta.get_field("original_review_url").null is True
    assert BookReview._meta.get_field("photo_path").null is True
    assert BookReview._meta.get_field("stars").null is True
    assert BookReview._meta.get_field("is_starred_review").default is False


def test_standalone_book_has_no_series_and_positions_are_one_based():
    author = create_author()
    _, genre, subgenre = create_genre_path()
    valid = Book.objects.create(
        author=author,
        onboarding_position=1,
        title="Standalone",
        cover_image="covers/test.png",
        description="Standalone description.",
        buy_links=["https://example.com/buy"],
        genre=genre,
        subgenre=subgenre,
    )
    assert valid.series_id is None

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Book.objects.create(
                author=author,
                onboarding_position=0,
                title="Invalid position",
                cover_image="covers/test-2.png",
                description="Invalid.",
                buy_links=["https://example.com/buy"],
                genre=genre,
                subgenre=subgenre,
            )
