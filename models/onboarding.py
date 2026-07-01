"""Validated data contracts for author onboarding."""

from typing import Any

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, EmailStr, Field, field_validator


class OnboardingBaseModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class BookEntry(OnboardingBaseModel):
    title: str = Field(min_length=1)
    cover_image: str | None = None
    description: str | None = None
    buy_links: list[AnyHttpUrl] = Field(default_factory=list)

    @field_validator("title")
    @classmethod
    def reject_blank_title(cls, value: str) -> str:
        if not value:
            raise ValueError("Book title is required.")
        return value


class SocialLinks(OnboardingBaseModel):
    twitter: AnyHttpUrl | None = None
    instagram: AnyHttpUrl | None = None
    facebook: AnyHttpUrl | None = None
    tiktok: AnyHttpUrl | None = None
    youtube: AnyHttpUrl | None = None

    @field_validator("*", mode="before")
    @classmethod
    def normalize_blank_url(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.strip():
            return None
        return value


class OnboardingForm(OnboardingBaseModel):
    author_name: str = Field(min_length=1)
    author_email: EmailStr
    website_name: str = Field(min_length=1)
    site_tagline: str | None = None
    author_bio_short: str | None = None
    author_bio_long: str | None = None
    genres: list[str] = Field(default_factory=list)
    primary_color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    secondary_color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    newsletter_link: str | None = None
    social_links: SocialLinks = Field(default_factory=SocialLinks)
    # Book portfolio: zero or more books; each entry is validated by BookEntry
    books: list[BookEntry] = Field(default_factory=list)

    @field_validator("author_name", "website_name")
    @classmethod
    def reject_blank_required_text(cls, value: str) -> str:
        if not value:
            raise ValueError("This field is required.")
        return value

    @field_validator(
        "site_tagline",
        "author_bio_short",
        "author_bio_long",
        "newsletter_link",
        mode="before",
    )
    @classmethod
    def normalize_blank_optional_text(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("genres", mode="before")
    @classmethod
    def normalize_genres(cls, value: Any) -> Any:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("Genres must be a list.")
        return [genre.strip() for genre in value if isinstance(genre, str) and genre.strip()]

    @field_validator("books", mode="before")
    @classmethod
    def normalize_books(cls, value: Any) -> Any:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("Books must be a list.")
        return value
