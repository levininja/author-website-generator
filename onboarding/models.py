"""Semantic database models for authors, books, genres, and series."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import ClassVar

from django.db import models


def _randomized_name(original_name: str) -> str:
    return f"{uuid.uuid4().hex}{Path(original_name).suffix.lower()}"


def author_headshot_path(instance: Author, filename: str) -> str:
    """Return the storage path for an author's uploaded headshot."""
    return f"authors/{instance.pk}/headshot/{_randomized_name(filename)}"


def book_cover_path(instance: Book, filename: str) -> str:
    """Return the storage path for a book cover upload."""
    return (
        f"authors/{instance.author_id}/books/{instance.pk}/cover/"
        f"{_randomized_name(filename)}"
    )


def sample_chapter_path(instance: Book, filename: str) -> str:
    """Return the storage path for a book sample chapter upload."""
    return (
        f"authors/{instance.author_id}/books/{instance.pk}/sample/"
        f"{_randomized_name(filename)}"
    )


def reviewer_photo_path(instance: BookReview, filename: str) -> str:
    """Return the storage path for a reviewer photo upload."""
    return (
        f"authors/{instance.book.author_id}/books/{instance.book_id}/"
        f"reviews/{instance.pk}/{_randomized_name(filename)}"
    )


def award_icon_path(instance: BookAward, filename: str) -> str:
    """Return the storage path for an award icon upload."""
    return (
        f"authors/{instance.book.author_id}/books/{instance.book_id}/"
        f"awards/{instance.pk}/{_randomized_name(filename)}"
    )


class BookCategory(models.Model):
    """Top-level book classification such as Fiction or Nonfiction."""

    name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = "genre_category"
        ordering: ClassVar = ["name"]


class BookGenre(models.Model):
    """Genre option nested under a top-level book category."""

    category = models.ForeignKey(
        BookCategory,
        on_delete=models.PROTECT,
        related_name="genres",
    )
    name = models.CharField(max_length=255)

    class Meta:
        db_table = "genre"
        ordering: ClassVar = ["category__name", "name"]
        constraints: ClassVar = [
            models.UniqueConstraint(
                fields=["category", "name"],
                name="unique_genre_per_category",
            )
        ]


class BookSubgenre(models.Model):
    """Subgenre option nested under a book genre."""

    genre = models.ForeignKey(
        BookGenre,
        on_delete=models.PROTECT,
        related_name="subgenres",
    )
    name = models.CharField(max_length=255)

    class Meta:
        db_table = "genre_subgenre"
        ordering: ClassVar = ["genre__name", "name"]
        constraints: ClassVar = [
            models.UniqueConstraint(
                fields=["genre", "name"],
                name="unique_subgenre_per_genre",
            )
        ]


class Author(models.Model):
    """Persisted author profile submitted through onboarding."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    contact_email = models.EmailField()
    site_domain = models.CharField(max_length=253)
    site_tagline = models.CharField(max_length=255, blank=True)
    bio_short = models.TextField(blank=True)
    bio_long = models.TextField(blank=True)
    primary_color = models.CharField(max_length=7, blank=True)
    secondary_color = models.CharField(max_length=7, blank=True)
    newsletter_link = models.CharField(max_length=2048, blank=True)
    selected_template = models.CharField(max_length=100, blank=True)
    social_twitter = models.URLField(max_length=2048, blank=True)
    social_instagram = models.URLField(max_length=2048, blank=True)
    social_facebook = models.URLField(max_length=2048, blank=True)
    social_tiktok = models.URLField(max_length=2048, blank=True)
    social_youtube = models.URLField(max_length=2048, blank=True)
    social_goodreads = models.URLField(max_length=2048, blank=True)
    headshot = models.FileField(
        upload_to=author_headshot_path,
        blank=True,
        max_length=500,
    )
    selected_categories = models.ManyToManyField(
        BookCategory,
        through="AuthorCategory",
        related_name="authors",
    )
    selected_genres = models.ManyToManyField(
        BookGenre,
        through="AuthorGenre",
        related_name="authors",
    )
    selected_subgenres = models.ManyToManyField(
        BookSubgenre,
        through="AuthorSubgenre",
        related_name="authors",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "author"


class AuthorCategory(models.Model):
    """Ordered category selection for an author."""

    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    category = models.ForeignKey(BookCategory, on_delete=models.PROTECT)
    display_position = models.PositiveIntegerField()

    class Meta:
        db_table = "author_category"
        ordering: ClassVar = ["display_position"]
        constraints: ClassVar = [
            models.UniqueConstraint(
                fields=["author", "category"],
                name="unique_author_category",
            ),
            models.UniqueConstraint(
                fields=["author", "display_position"],
                name="unique_author_category_position",
            ),
        ]


class AuthorGenre(models.Model):
    """Ordered genre selection for an author."""

    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    genre = models.ForeignKey(BookGenre, on_delete=models.PROTECT)
    display_position = models.PositiveIntegerField()

    class Meta:
        db_table = "author_genre"
        ordering: ClassVar = ["display_position"]
        constraints: ClassVar = [
            models.UniqueConstraint(
                fields=["author", "genre"],
                name="unique_author_genre",
            ),
            models.UniqueConstraint(
                fields=["author", "display_position"],
                name="unique_author_genre_position",
            ),
        ]


class AuthorSubgenre(models.Model):
    """Ordered subgenre selection for an author."""

    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    subgenre = models.ForeignKey(BookSubgenre, on_delete=models.PROTECT)
    display_position = models.PositiveIntegerField()

    class Meta:
        db_table = "author_subgenre"
        ordering: ClassVar = ["display_position"]
        constraints: ClassVar = [
            models.UniqueConstraint(
                fields=["author", "subgenre"],
                name="unique_author_subgenre",
            ),
            models.UniqueConstraint(
                fields=["author", "display_position"],
                name="unique_author_subgenre_position",
            ),
        ]


class Series(models.Model):
    """Book series owned by one author."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name="series",
    )
    name = models.CharField(max_length=255)
    total_books = models.PositiveIntegerField()
    is_complete = models.BooleanField(default=False)

    class Meta:
        db_table = "book_series"
        ordering: ClassVar = ["name"]
        constraints: ClassVar = [
            models.UniqueConstraint(
                fields=["author", "name"],
                name="unique_series_name_per_author",
            )
        ]


class Book(models.Model):
    """Persisted book submitted for an author."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name="books",
    )
    onboarding_position = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    cover_image = models.FileField(upload_to=book_cover_path, max_length=500)
    description = models.TextField()
    buy_links = models.JSONField(default=list)
    genre = models.ForeignKey(
        BookGenre,
        on_delete=models.PROTECT,
        related_name="books",
    )
    subgenre = models.ForeignKey(
        BookSubgenre,
        on_delete=models.PROTECT,
        related_name="books",
        null=True,
        blank=True,
    )
    series = models.ForeignKey(
        Series,
        on_delete=models.SET_NULL,
        related_name="books",
        null=True,
        blank=True,
    )
    number_in_series = models.PositiveIntegerField(null=True, blank=True)
    perfect_for = models.TextField(blank=True)
    enjoy_if = models.TextField(blank=True)
    sample_chapter_path = models.FileField(
        upload_to=sample_chapter_path,
        blank=True,
        max_length=500,
    )
    sample_chapter_name = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "book"
        ordering: ClassVar = ["onboarding_position"]
        constraints: ClassVar = [
            models.UniqueConstraint(
                fields=["author", "onboarding_position"],
                name="unique_book_onboarding_position_per_author",
            ),
            models.CheckConstraint(
                condition=models.Q(onboarding_position__gte=1),
                name="book_onboarding_position_gte_1",
            ),
        ]


class BookReview(models.Model):
    """Persisted editorial or reader review for a book."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    display_position = models.PositiveIntegerField()
    is_editorial = models.BooleanField(default=False)
    reviewer_name = models.CharField(max_length=255)
    credentials = models.CharField(max_length=255, null=True, blank=True)
    quotation = models.TextField()
    original_review_url = models.URLField(
        max_length=2048,
        null=True,
        blank=True,
    )
    photo_path = models.FileField(
        upload_to=reviewer_photo_path,
        max_length=500,
        null=True,
        blank=True,
    )
    stars = models.PositiveSmallIntegerField(null=True, blank=True)
    is_starred_review = models.BooleanField(default=False)

    class Meta:
        db_table = "book_review"
        ordering: ClassVar = ["display_position"]


class BookAward(models.Model):
    """Persisted award badge for a book."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="awards",
    )
    display_position = models.PositiveIntegerField()
    name = models.CharField(max_length=255)
    icon_path = models.FileField(upload_to=award_icon_path, max_length=500)

    class Meta:
        db_table = "book_award"
        ordering: ClassVar = ["display_position"]


class GenerationJob(models.Model):
    """Tracks the state of one website generation pipeline run for an author."""

    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_COMPLETE = "complete"
    STATUS_FAILED = "failed"
    STATUS_CHOICES: ClassVar = [
        (STATUS_PENDING, "Pending"),
        (STATUS_RUNNING, "Running"),
        (STATUS_COMPLETE, "Complete"),
        (STATUS_FAILED, "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name="generation_jobs",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "generation_job"
