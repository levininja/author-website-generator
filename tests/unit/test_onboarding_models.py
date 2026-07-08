"""Unit tests for onboarding form validation."""

import pytest
from pydantic import ValidationError

from models.onboarding import OnboardingForm, SocialLinks, validate_genre_tree


GENRE_TREE = {
    "Fiction": {
        "Science Fiction": ["Cyberpunk", "Space Opera"],
        "Fantasy": ["Epic Fantasy", "Urban Fantasy"],
    },
    "Nonfiction": {
        "Biography & Memoir": ["Biography", "Memoir"],
    },
}


def minimal_book(**overrides):
    data = {
        "title": "The Midnight Code",
        "cover_image_key": "book_0_cover_image",
        "description": "A technological thriller.",
        "buy_links": ["https://example.com/books/midnight-code"],
        "category": "Fiction",
        "genre": "Science Fiction",
        "subgenre": "Cyberpunk",
        "series_type": "standalone",
    }
    data.update(overrides)
    return data


def minimal_form_data(**overrides):
    data = {
        "author_name": "Jane Doe",
        "author_email": "contact@example.com",
        "site_domain": "janedoe.com",
        "genres": ["Fiction", "Science Fiction", "Cyberpunk"],
        "books": [minimal_book()],
    }
    data.update(overrides)
    return data


def validate_form(data):
    return OnboardingForm.model_validate(data, context={"genre_tree": GENRE_TREE})


def test_minimal_valid_input_passes_with_optional_fields_omitted():
    form = validate_form(minimal_form_data())

    assert form.author_name == "Jane Doe"
    assert form.author_email == "contact@example.com"
    assert form.site_domain == "janedoe.com"
    assert form.books[0].series_type == "standalone"
    assert form.social_links == SocialLinks()


@pytest.mark.parametrize(
    "field",
    ["author_name", "author_email", "site_domain", "genres", "books"],
)
def test_required_form_fields_are_enforced(field):
    data = minimal_form_data()
    del data[field]

    with pytest.raises(ValidationError) as exc_info:
        validate_form(data)

    assert field in str(exc_info.value)


@pytest.mark.parametrize(
    "domain",
    [
        "https://janedoe.com",
        "janedoe.com/books",
        "localhost",
        "-janedoe.com",
        "janedoe",
        "jane doe.com",
    ],
)
def test_site_domain_rejects_urls_paths_and_invalid_hostnames(domain):
    with pytest.raises(ValidationError):
        validate_form(minimal_form_data(site_domain=domain))


@pytest.mark.parametrize(
    ("domain", "normalized"),
    [
        ("JaneDoe.COM", "janedoe.com"),
        ("www.janedoe.co.uk", "www.janedoe.co.uk"),
        ("author-books.io", "author-books.io"),
    ],
)
def test_site_domain_accepts_and_normalizes_bare_domains(domain, normalized):
    form = validate_form(minimal_form_data(site_domain=domain))

    assert form.site_domain == normalized


def test_genre_tree_requires_three_levels_rooted_in_fiction_and_non_fiction():
    assert validate_genre_tree(GENRE_TREE) == GENRE_TREE

    with pytest.raises(ValueError):
        validate_genre_tree({"Fiction": {"Fantasy": ["Epic Fantasy"]}})

    with pytest.raises(ValueError):
        validate_genre_tree(
            {
                "Fiction": {"Fantasy": "Epic Fantasy"},
                "Nonfiction": {"History": ["Military History"]},
            }
        )


def test_author_genres_must_exist_at_any_level_of_the_catalog():
    form = validate_form(
        minimal_form_data(genres=["Nonfiction", "Biography & Memoir", "Memoir"])
    )
    assert form.genres == ["Nonfiction", "Biography & Memoir", "Memoir"]

    with pytest.raises(ValidationError):
        validate_form(minimal_form_data(genres=["Classics"]))


def test_at_least_one_author_genre_and_one_book_are_required():
    with pytest.raises(ValidationError):
        validate_form(minimal_form_data(genres=[]))

    with pytest.raises(ValidationError):
        validate_form(minimal_form_data(books=[]))


@pytest.mark.parametrize(
    "field",
    [
        "title",
        "cover_image_key",
        "description",
        "buy_links",
        "category",
        "genre",
        "series_type",
    ],
)
def test_book_core_fields_are_required(field):
    book = minimal_book()
    del book[field]

    with pytest.raises(ValidationError) as exc_info:
        validate_form(minimal_form_data(books=[book]))

    assert field in str(exc_info.value)


def test_book_genre_path_must_exist_in_catalog():
    with pytest.raises(ValidationError):
        validate_form(
            minimal_form_data(
                books=[minimal_book(genre="Fantasy", subgenre="Cyberpunk")]
            )
        )


def test_book_subgenre_is_optional():
    form = validate_form(minimal_form_data(books=[minimal_book(subgenre=None)]))

    assert form.books[0].subgenre is None


def test_series_book_requires_name_number_and_total():
    with pytest.raises(ValidationError):
        validate_form(
            minimal_form_data(books=[minimal_book(series_type="series")])
        )

    form = validate_form(
        minimal_form_data(
            books=[
                minimal_book(
                    series_type="series",
                    series_name="The Signal Cycle",
                    book_number=2,
                    series_length=4,
                    series_is_complete=True,
                )
            ]
        )
    )

    assert form.books[0].series_name == "The Signal Cycle"
    assert form.books[0].book_number == 2
    assert form.books[0].series_is_complete is True


def test_series_book_number_cannot_exceed_series_length():
    with pytest.raises(ValidationError):
        validate_form(
            minimal_form_data(
                books=[
                    minimal_book(
                        series_type="series",
                        series_name="The Signal Cycle",
                        book_number=5,
                        series_length=4,
                    )
                ]
            )
        )


def test_complete_optional_book_content_is_accepted():
    form = validate_form(
        minimal_form_data(
            books=[
                minimal_book(
                    editorial_reviews=[
                        {
                            "reviewer_name": "Kirkus Reviews",
                            "quotation": "A propulsive read.",
                            "original_review_url": "https://example.com/review",
                            "stars": 5,
                            "is_starred_review": True,
                            "photo_key": "book_0_editorial_review_0_photo",
                        }
                    ],
                    other_reviews=[
                        {
                            "reviewer_name": "Reader One",
                            "credentials": "Author of The Shining",
                            "quotation": "I could not put it down.",
                            "original_review_url": "https://example.com/reader-review",
                            "stars": 4,
                            "photo_key": "book_0_other_review_0_photo",
                        }
                    ],
                    awards=[
                        {
                            "name": "Best Debut",
                            "icon_key": "book_0_award_0_icon",
                        }
                    ],
                    perfect_for="Readers who enjoy near-future mysteries.",
                    enjoy_if="You like clever protagonists and found family.",
                    sample_chapter_key="book_0_sample_chapter",
                )
            ]
        )
    )

    assert form.books[0].editorial_reviews[0].stars == 5
    assert form.books[0].editorial_reviews[0].is_starred_review is True
    assert form.books[0].other_reviews[0].stars == 4
    assert (
        form.books[0].other_reviews[0].credentials
        == "Author of The Shining"
    )
    assert form.books[0].awards[0].name == "Best Debut"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("editorial_reviews", [{"reviewer_name": "", "quotation": "Good."}]),
        ("other_reviews", [{"reviewer_name": "A. Writer", "quotation": ""}]),
        (
            "other_reviews",
            [
                {
                    "stars": 0,
                    "photo_key": "photo",
                    "reviewer_name": "Reader",
                    "quotation": "Good.",
                }
            ],
        ),
        ("awards", [{"name": "Best Debut", "icon_key": ""}]),
    ],
)
def test_incomplete_optional_nested_items_are_rejected(field, value):
    with pytest.raises(ValidationError):
        validate_form(minimal_form_data(books=[minimal_book(**{field: value})]))


def test_editorial_reviews_reject_individual_credentials():
    with pytest.raises(ValidationError, match="Editorial reviews"):
        validate_form(
            minimal_form_data(
                books=[
                    minimal_book(
                        editorial_reviews=[
                            {
                                "reviewer_name": "Kirkus Reviews",
                                "credentials": "Staff reviewer",
                                "quotation": "A sharp debut.",
                            }
                        ]
                    )
                ]
            )
        )


def test_goodreads_accepts_http_url_and_rejects_non_url():
    links = SocialLinks.model_validate(
        {"goodreads": "https://www.goodreads.com/author/show/123"}
    )
    assert str(links.goodreads) == "https://www.goodreads.com/author/show/123"
    with pytest.raises(ValidationError):
        SocialLinks.model_validate({"goodreads": "not a domain"})


def test_bare_domain_links_are_normalized_to_https():
    form = validate_form(
        minimal_form_data(
            books=[
                minimal_book(
                    buy_links=["amazon.com/book"],
                    editorial_reviews=[
                        {
                            "reviewer_name": "Kirkus Reviews",
                            "quotation": "Excellent.",
                            "original_review_url": "kirkusreviews.com/review",
                        }
                    ],
                )
            ],
            social_links={"goodreads": "goodreads.com/author/123"},
        )
    )

    assert str(form.books[0].buy_links[0]) == "https://amazon.com/book"
    assert (
        str(form.books[0].editorial_reviews[0].original_review_url)
        == "https://kirkusreviews.com/review"
    )
    assert str(form.social_links.goodreads) == "https://goodreads.com/author/123"


@pytest.mark.parametrize("value", ["amazon", "not a domain", "https://localhost"])
def test_links_without_public_domain_suffix_are_rejected(value):
    with pytest.raises(ValidationError):
        validate_form(
            minimal_form_data(books=[minimal_book(buy_links=[value])])
        )

@pytest.mark.parametrize("color", ["#000000", "#ffffff", "#ABCDEF", "#12abEF"])
def test_hex_colors_accept_exactly_six_hex_digits(color):
    form = validate_form(minimal_form_data(primary_color=color))
    assert form.primary_color == color


@pytest.mark.parametrize("color", ["123456", "#12345", "#GGGGGG", "transparent"])
def test_invalid_hex_colors_are_rejected(color):
    with pytest.raises(ValidationError):
        validate_form(minimal_form_data(primary_color=color))


def test_author_headshot_key_is_optional():
    form = validate_form(minimal_form_data())
    assert form.author_headshot_key is None


def test_blank_author_headshot_key_normalizes_to_none():
    form = validate_form(minimal_form_data(author_headshot_key=""))
    assert form.author_headshot_key is None

    form = validate_form(minimal_form_data(author_headshot_key="   "))
    assert form.author_headshot_key is None


def test_author_headshot_key_is_stored_when_provided():
    form = validate_form(minimal_form_data(author_headshot_key="author_headshot"))
    assert form.author_headshot_key == "author_headshot"


def test_selected_template_is_optional():
    form = validate_form(minimal_form_data())
    assert form.selected_template is None


def test_blank_selected_template_normalizes_to_none():
    form = validate_form(minimal_form_data(selected_template=""))
    assert form.selected_template is None

    form = validate_form(minimal_form_data(selected_template="   "))
    assert form.selected_template is None


def test_valid_template_name_is_accepted():
    form = validate_form(minimal_form_data(selected_template="Classic"))
    assert form.selected_template == "Classic"


def test_old_template_names_are_rejected():
    for name in ["Classic Author", "Modern Minimalist", "Bold & Bright",
                 "Cozy Romance", "Thriller Dark", "Literary Fiction"]:
        with pytest.raises(ValidationError):
            validate_form(minimal_form_data(selected_template=name))


def test_invalid_template_name_is_rejected():
    with pytest.raises(ValidationError):
        validate_form(minimal_form_data(selected_template="NonExistent Template"))
