"""Unit tests for atomically persisting the onboarding aggregate."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from models.onboarding import OnboardingForm
from onboarding.models import (
    Author,
    AuthorGenre,
    Book,
    BookCategory,
    BookGenre,
    BookReview,
    BookSubgenre,
)
from onboarding.services import persist_onboarding, sync_genre_catalog


GENRE_TREE = {
    "Fiction": {
        "Science Fiction": ["Cyberpunk", "Space Opera"],
    },
    "Nonfiction": {
        "Biography & Memoir": ["Biography", "Memoir"],
    },
}


@pytest.fixture(autouse=True)
def catalog():
    sync_genre_catalog(GENRE_TREE)


@pytest.fixture(autouse=True)
def isolated_media_root(settings):
    with TemporaryDirectory(prefix="awg-test-media-") as directory:
        settings.MEDIA_ROOT = Path(directory)
        yield


def complete_form(**overrides):
    data = {
        "author_name": "Jane Doe",
        "author_email": "contact@example.com",
        "site_domain": "janedoe.com",
        "site_tagline": "Thrillers after dark.",
        "author_bio_short": "Jane writes technological thrillers.",
        "author_bio_long": "Jane has written stories for more than a decade.",
        "genres": ["Fiction", "Science Fiction", "Cyberpunk"],
        "primary_color": "#123456",
        "secondary_color": "#abcdef",
        "newsletter_link": "kit-form-123",
        "social_links": {
            "twitter": "https://x.com/janedoe",
            "goodreads": "https://goodreads.com/janedoe",
        },
        "books": [
            {
                "title": "The Midnight Code",
                "cover_image_key": "book_0_cover_image",
                "description": "A technological thriller.",
                "buy_links": ["https://example.com/buy"],
                "category": "Fiction",
                "genre": "Science Fiction",
                "subgenre": "Cyberpunk",
                "series_type": "standalone",
            }
        ],
    }
    data.update(overrides)
    return OnboardingForm.model_validate(data, context={"genre_tree": GENRE_TREE})


def uploads():
    return {
        "book_0_cover_image": SimpleUploadedFile(
            "cover.png",
            b"image bytes",
            content_type="image/png",
        )
    }


@pytest.mark.django_db
def test_persist_onboarding_saves_author_book_and_normalized_relations():
    author = persist_onboarding(complete_form(), uploads())

    author.refresh_from_db()
    book = author.books.select_related(
        "genre__category",
        "subgenre",
    ).get()
    assert author.name == "Jane Doe"
    assert author.contact_email == "contact@example.com"
    assert author.bio_short == "Jane writes technological thrillers."
    assert author.primary_color == "#123456"
    assert author.social_twitter == "https://x.com/janedoe"
    assert book.author == author
    assert book.onboarding_position == 1
    assert book.genre.name == "Science Fiction"
    assert book.genre.category.name == "Fiction"
    assert book.subgenre.name == "Cyberpunk"
    assert book.series_id is None


@pytest.mark.django_db
def test_persist_onboarding_saves_optional_author_fields_as_blank_strings():
    form = complete_form(
        site_tagline=None,
        author_bio_short=None,
        author_bio_long=None,
        primary_color=None,
        secondary_color=None,
        newsletter_link=None,
        social_links={},
    )

    author = persist_onboarding(form, uploads())
    author.refresh_from_db()

    assert author.site_tagline == ""
    assert author.bio_short == ""
    assert author.bio_long == ""
    assert author.primary_color == ""
    assert author.secondary_color == ""
    assert author.newsletter_link == ""
    assert author.social_twitter == ""
    assert author.social_goodreads == ""


@pytest.mark.django_db
def test_persist_onboarding_preserves_selection_order_across_lookup_levels():
    form = complete_form(
        genres=["Cyberpunk", "Fiction", "Science Fiction", "Cyberpunk"]
    )

    author = persist_onboarding(form, uploads())

    positions = {
        "category": list(
            author.authorcategory_set.values_list("display_position", flat=True)
        ),
        "genre": list(
            author.authorgenre_set.values_list("display_position", flat=True)
        ),
        "subgenre": list(
            author.authorsubgenre_set.values_list("display_position", flat=True)
        ),
    }
    assert positions == {
        "category": [2],
        "genre": [3],
        "subgenre": [1],
    }


@pytest.mark.django_db(transaction=True)
def test_persist_onboarding_rolls_back_author_and_books_when_selection_fails():
    with patch.object(
        AuthorGenre.objects,
        "create",
        side_effect=RuntimeError("selection write failed"),
    ):
        with pytest.raises(RuntimeError, match="selection write failed"):
            persist_onboarding(complete_form(), uploads())

    assert Author.objects.count() == 0
    assert Book.objects.count() == 0


@pytest.mark.django_db
def test_lookup_rows_are_real_foreign_keys_not_repeated_book_strings():
    persist_onboarding(complete_form(), uploads())
    book = Book.objects.get()

    assert BookCategory.objects.filter(name="Fiction").count() == 1
    assert BookGenre.objects.filter(name="Science Fiction").count() == 1
    assert BookSubgenre.objects.filter(name="Cyberpunk").count() == 1
    assert book.genre_id is not None
    assert book.subgenre_id is not None


@pytest.mark.django_db
def test_book_can_persist_without_a_subgenre():
    book_data = complete_form().books[0].model_dump(mode="json")
    book_data["subgenre"] = None

    author = persist_onboarding(
        complete_form(books=[book_data]),
        uploads(),
    )

    assert author.books.get().subgenre_id is None


@pytest.mark.django_db
def test_editorial_and_other_reviews_persist_to_one_review_table():
    form = complete_form(
        books=[
            {
                **complete_form().books[0].model_dump(mode="json"),
                "editorial_reviews": [
                    {
                        "reviewer_name": "Kirkus",
                        "quotation": "A sharp debut.",
                        "original_review_url": "https://example.com/editorial",
                        "stars": 5,
                        "is_starred_review": True,
                    }
                ],
                "other_reviews": [
                    {
                        "reviewer_name": "Reader One",
                        "credentials": "Author of The Shining",
                        "quotation": "Excellent.",
                        "original_review_url": "https://example.com/reader",
                        "stars": 4,
                        "photo_key": "book_0_other_review_0_photo",
                    }
                ],
            }
        ]
    )
    files = uploads()
    files["book_0_other_review_0_photo"] = SimpleUploadedFile(
        "reader.png",
        b"reader image",
        content_type="image/png",
    )

    author = persist_onboarding(form, files)
    reviews = list(
        BookReview.objects.filter(book__author=author).order_by(
            "-is_editorial",
            "display_position",
        )
    )

    assert len(reviews) == 2
    assert reviews[0].is_editorial is True
    assert reviews[0].reviewer_name == "Kirkus"
    assert reviews[0].credentials is None
    assert reviews[0].is_starred_review is True
    assert reviews[0].photo_path == ""
    assert reviews[1].is_editorial is False
    assert reviews[1].credentials == "Author of The Shining"
    assert reviews[1].photo_path
    assert reviews[1].stars == 4
    assert [review.display_position for review in reviews] == [1, 1]
