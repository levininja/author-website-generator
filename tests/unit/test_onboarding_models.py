"""Unit tests for onboarding form validation."""

import pytest
from pydantic import ValidationError

from models.onboarding import BookEntry, OnboardingForm, SocialLinks


def minimal_form_data(**overrides):
    data = {
        "author_name": "Jane Doe",
        "author_email": "jane@example.com",
        "website_name": "Jane Doe Books",
    }
    data.update(overrides)
    return data


def test_minimal_valid_input_passes_with_optional_fields_omitted():
    form = OnboardingForm.model_validate(minimal_form_data())

    assert form.author_name == "Jane Doe"
    assert form.author_email == "jane@example.com"
    assert form.website_name == "Jane Doe Books"
    assert form.genres == []
    assert form.social_links == SocialLinks()


def test_complete_valid_input_passes():
    form = OnboardingForm.model_validate(
        minimal_form_data(
            site_tagline="Stories from beyond the stars",
            author_bio_short="Jane writes speculative fiction.",
            author_bio_long="Jane has written stories for more than twenty years.",
            genres=["Science Fiction", "Fantasy"],
            primary_color="#123ABC",
            secondary_color="#abcdef",
            newsletter_link="kit-form-123",
            social_links={
                "twitter": "https://x.com/janedoe",
                "instagram": "https://instagram.com/janedoe",
                "facebook": "https://facebook.com/janedoe",
                "tiktok": "https://tiktok.com/@janedoe",
                "youtube": "https://youtube.com/@janedoe",
            },
        )
    )

    assert form.genres == ["Science Fiction", "Fantasy"]
    assert form.primary_color == "#123ABC"
    assert str(form.social_links.twitter) == "https://x.com/janedoe"


@pytest.mark.parametrize("field", ["author_name", "author_email", "website_name"])
def test_required_fields_are_enforced_when_missing(field):
    data = minimal_form_data()
    del data[field]

    with pytest.raises(ValidationError) as exc_info:
        OnboardingForm.model_validate(data)

    assert field in str(exc_info.value)


@pytest.mark.parametrize("field", ["author_name", "website_name"])
def test_required_text_fields_reject_whitespace(field):
    with pytest.raises(ValidationError):
        OnboardingForm.model_validate(minimal_form_data(**{field: "   "}))


@pytest.mark.parametrize("email", ["not-an-email", "jane@", "@example.com"])
def test_author_email_must_be_valid(email):
    with pytest.raises(ValidationError):
        OnboardingForm.model_validate(minimal_form_data(author_email=email))


@pytest.mark.parametrize("color", ["#000000", "#ffffff", "#ABCDEF", "#12abEF"])
def test_hex_colors_accept_exactly_six_hex_digits(color):
    form = OnboardingForm.model_validate(minimal_form_data(primary_color=color))

    assert form.primary_color == color


@pytest.mark.parametrize(
    "color",
    ["123456", "#12345", "#1234567", "#GGGGGG", "", "transparent"],
)
def test_invalid_hex_colors_are_rejected(color):
    with pytest.raises(ValidationError):
        OnboardingForm.model_validate(minimal_form_data(primary_color=color))


@pytest.mark.parametrize(
    "field",
    ["twitter", "instagram", "facebook", "tiktok", "youtube"],
)
def test_social_links_accept_http_and_https_urls(field):
    links = SocialLinks.model_validate({field: "https://example.com/author"})

    assert str(getattr(links, field)) == "https://example.com/author"


@pytest.mark.parametrize(
    "url",
    ["example.com/author", "ftp://example.com/author", "javascript:alert(1)", "not a url"],
)
def test_social_links_reject_non_http_urls(url):
    with pytest.raises(ValidationError):
        SocialLinks.model_validate({"twitter": url})


def test_blank_optional_urls_are_treated_as_omitted():
    links = SocialLinks.model_validate({"twitter": ""})

    assert links.twitter is None


def test_genres_are_trimmed_and_blank_entries_removed():
    form = OnboardingForm.model_validate(
        minimal_form_data(genres=[" Fantasy ", "", "  ", "Mystery"])
    )

    assert form.genres == ["Fantasy", "Mystery"]


def test_book_entry_supports_future_book_data_without_becoming_required():
    book = BookEntry.model_validate(
        {
            "title": "The Midnight Code",
            "description": "A technological thriller.",
            "buy_links": ["https://example.com/books/midnight-code"],
        }
    )

    assert book.title == "The Midnight Code"
    assert str(book.buy_links[0]) == "https://example.com/books/midnight-code"


def test_book_entry_requires_a_non_blank_title():
    with pytest.raises(ValidationError):
        BookEntry.model_validate({"title": " "})


# ── OnboardingForm: books field ───────────────────────────────────────────────


def test_onboarding_form_defaults_to_empty_books_list():
    form = OnboardingForm.model_validate(minimal_form_data())

    assert form.books == []


def test_onboarding_form_accepts_one_or_more_books():
    form = OnboardingForm.model_validate(
        minimal_form_data(
            books=[
                {
                    "title": "The Midnight Code",
                    "description": "A technological thriller.",
                    "buy_links": ["https://example.com/midnight"],
                },
                {
                    "title": "Ghost Signal",
                    "buy_links": [],
                },
            ]
        )
    )

    assert len(form.books) == 2
    assert form.books[0].title == "The Midnight Code"
    assert form.books[1].title == "Ghost Signal"


def test_onboarding_form_rejects_book_with_blank_title():
    with pytest.raises(ValidationError) as exc_info:
        OnboardingForm.model_validate(
            minimal_form_data(books=[{"title": "  "}])
        )

    assert "books" in str(exc_info.value)


def test_onboarding_form_rejects_books_that_is_not_a_list():
    with pytest.raises(ValidationError):
        OnboardingForm.model_validate(minimal_form_data(books="one book"))


def test_onboarding_form_treats_null_books_as_empty_list():
    form = OnboardingForm.model_validate(minimal_form_data(books=None))

    assert form.books == []
