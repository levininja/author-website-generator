"""Validated data contracts for author onboarding."""

import re
from typing import Any, Literal, Self
from urllib.parse import urlsplit

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)

GenreTree = dict[str, dict[str, list[str]]]

DIVI_TEMPLATES = [
    "Classic",
]

DOMAIN_PATTERN = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z]{2,63}$",
    re.IGNORECASE,
)


def validate_genre_tree(value: Any) -> GenreTree:
    """Validate and return the three-level genre catalog contract."""
    if not isinstance(value, dict) or set(value) != {"Fiction", "Nonfiction"}:
        raise ValueError("Genre catalog must contain Fiction and Nonfiction roots.")

    for category, genres in value.items():
        if not isinstance(genres, dict) or not genres:
            raise ValueError(f"{category} must contain one or more genres.")
        for genre, subgenres in genres.items():
            if not isinstance(genre, str) or not genre.strip():
                raise ValueError("Genre names must be non-empty strings.")
            if (
                not isinstance(subgenres, list)
                or not subgenres
                or any(not isinstance(item, str) or not item.strip() for item in subgenres)
            ):
                raise ValueError(
                    f"{category} > {genre} must contain one or more subgenres."
                )
    return value


def all_genre_names(tree: GenreTree) -> set[str]:
    """Return every category, genre, and subgenre name in a genre tree."""
    names = set(tree)
    for genres in tree.values():
        names.update(genres)
        for subgenres in genres.values():
            names.update(subgenres)
    return names


def normalize_web_url(value: Any) -> Any:
    """Normalize user-entered web addresses into absolute HTTP URLs."""
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if not stripped:
        return stripped
    candidate = (
        stripped
        if re.match(r"^[a-z][a-z0-9+.-]*://", stripped, re.IGNORECASE)
        else f"https://{stripped}"
    )
    parsed = urlsplit(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Enter a valid web address such as example.com.")
    if not DOMAIN_PATTERN.fullmatch(parsed.hostname):
        raise ValueError(
            "Web addresses must contain a public domain suffix such as "
            ".com, .net, or .org."
        )
    return candidate


class OnboardingBaseModel(BaseModel):
    """Base model for onboarding payloads with stripped string inputs."""

    model_config = ConfigDict(str_strip_whitespace=True)


class BookReview(OnboardingBaseModel):
    """Submitted review or endorsement for a book."""

    reviewer_name: str = Field(min_length=1)
    credentials: str | None = None
    quotation: str = Field(min_length=1)
    original_review_url: AnyHttpUrl | None = None
    photo_key: str | None = None
    stars: int | None = Field(default=None, ge=1, le=5)
    is_starred_review: bool = False

    @field_validator("original_review_url", mode="before")
    @classmethod
    def normalize_review_url(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.strip():
            return None
        return normalize_web_url(value)

    @field_validator(
        "credentials",
        "photo_key",
        mode="before",
    )
    @classmethod
    def normalize_blank_optional_value(cls, value: Any) -> Any:
        return None if isinstance(value, str) and not value.strip() else value


class Award(OnboardingBaseModel):
    """Submitted award badge for a book."""

    name: str = Field(min_length=1)
    icon_key: str = Field(min_length=1)


class BookEntry(OnboardingBaseModel):
    """Submitted book metadata and related marketing content."""

    title: str = Field(min_length=1)
    cover_image_key: str = Field(min_length=1)
    description: str = Field(min_length=1)
    buy_links: list[AnyHttpUrl] = Field(min_length=1)
    category: str = Field(min_length=1)
    genre: str = Field(min_length=1)
    subgenre: str | None = None
    series_type: Literal["standalone", "series"]
    series_name: str | None = None
    book_number: int | None = Field(default=None, ge=1)
    series_length: int | None = Field(default=None, ge=1)
    series_is_complete: bool = False
    editorial_reviews: list[BookReview] = Field(default_factory=list)
    other_reviews: list[BookReview] = Field(default_factory=list)
    awards: list[Award] = Field(default_factory=list)
    perfect_for: str | None = None
    enjoy_if: str | None = None
    sample_chapter_key: str | None = None

    @field_validator("buy_links", mode="before")
    @classmethod
    def normalize_buy_links(cls, value: Any) -> Any:
        if not isinstance(value, list):
            return value
        return [normalize_web_url(link) for link in value]

    @field_validator(
        "series_name",
        "subgenre",
        "perfect_for",
        "enjoy_if",
        "sample_chapter_key",
        mode="before",
    )
    @classmethod
    def normalize_blank_optional_text(cls, value: Any) -> Any:
        return None if isinstance(value, str) and not value.strip() else value

    @model_validator(mode="after")
    def validate_genre_and_series(self, info: ValidationInfo) -> Self:
        if any(review.credentials for review in self.editorial_reviews):
            raise ValueError(
                "Editorial reviews identify a publication and cannot include "
                "individual credentials."
            )

        tree = (info.context or {}).get("genre_tree")
        if tree is not None:
            try:
                subgenres = tree[self.category][self.genre]
            except (KeyError, TypeError) as exc:
                raise ValueError("Book category and genre must exist in the catalog.") from exc
            if self.subgenre is not None and self.subgenre not in subgenres:
                raise ValueError("Book subgenre must belong to the selected genre.")

        if self.series_type == "series":
            if (
                not self.series_name
                or self.book_number is None
                or self.series_length is None
            ):
                raise ValueError(
                    "Series books require a series name, book number, and total books."
                )
            if self.book_number > self.series_length:
                raise ValueError("Book number cannot exceed total books in the series.")
        return self


class SocialLinks(OnboardingBaseModel):
    """Submitted author social profile URLs."""

    twitter: AnyHttpUrl | None = None
    instagram: AnyHttpUrl | None = None
    facebook: AnyHttpUrl | None = None
    tiktok: AnyHttpUrl | None = None
    youtube: AnyHttpUrl | None = None
    goodreads: AnyHttpUrl | None = None

    @field_validator("*", mode="before")
    @classmethod
    def normalize_blank_url(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.strip():
            return None
        return normalize_web_url(value)


class OnboardingForm(OnboardingBaseModel):
    """Complete validated author onboarding submission."""

    author_name: str = Field(min_length=1)
    author_email: EmailStr
    site_domain: str = Field(min_length=1)
    site_tagline: str | None = None
    author_bio_short: str | None = None
    author_bio_long: str | None = None
    genres: list[str] = Field(min_length=1)
    primary_color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    secondary_color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    newsletter_link: str | None = None
    author_headshot_key: str | None = None
    selected_template: str | None = None
    social_links: SocialLinks = Field(default_factory=SocialLinks)
    books: list[BookEntry] = Field(min_length=1)

    @field_validator("site_domain")
    @classmethod
    def validate_site_domain(cls, value: str) -> str:
        normalized = value.lower()
        if not DOMAIN_PATTERN.fullmatch(normalized):
            raise ValueError("Enter a bare domain name without a protocol or path.")
        return normalized

    @field_validator(
        "site_tagline",
        "author_bio_short",
        "author_bio_long",
        "newsletter_link",
        "author_headshot_key",
        "selected_template",
        mode="before",
    )
    @classmethod
    def normalize_blank_optional_text(cls, value: Any) -> Any:
        return None if isinstance(value, str) and not value.strip() else value

    @field_validator("selected_template", mode="after")
    @classmethod
    def validate_selected_template(cls, value: str | None) -> str | None:
        if value is not None and value not in DIVI_TEMPLATES:
            raise ValueError(f"Unknown template: {value!r}.")
        return value

    @field_validator("newsletter_link", mode="after")
    @classmethod
    def normalize_newsletter_url(cls, value: str | None) -> str | None:
        if value and ("." in value or "://" in value):
            return str(normalize_web_url(value))
        return value

    @field_validator("genres")
    @classmethod
    def validate_author_genres(
        cls, value: list[str], info: ValidationInfo
    ) -> list[str]:
        tree = (info.context or {}).get("genre_tree")
        if tree is not None:
            allowed = all_genre_names(tree)
            invalid = [genre for genre in value if genre not in allowed]
            if invalid:
                raise ValueError(f"Unknown genre selection: {invalid[0]}.")
        return list(dict.fromkeys(value))
