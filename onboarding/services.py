"""Persistence and serialization for the author onboarding aggregate."""

from pathlib import Path

from django.db import transaction

from models.onboarding import OnboardingForm
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


def _optional_text(value):
    return str(value) if value is not None else ""


def _original_basename(upload):
    if upload is None:
        return ""
    return Path(str(upload.name).replace("\\", "/")).name[:255]


def _track_file(field, saved_files):
    if field and field.name:
        saved_files.append((field.storage, field.name))


def _assign_upload(instance, field_name, upload, saved_files):
    if upload is None:
        return
    field = getattr(instance, field_name)
    field.save(upload.name, upload, save=False)
    _track_file(field, saved_files)


def _delete_files(saved_files):
    for storage, name in reversed(saved_files):
        local_path = None
        try:
            local_path = Path(storage.path(name))
        except (AttributeError, NotImplementedError):
            pass
        try:
            storage.delete(name)
        except Exception:
            pass
        if local_path is not None:
            root = Path(storage.location)
            parent = local_path.parent
            while parent != root:
                try:
                    parent.rmdir()
                except OSError:
                    break
                parent = parent.parent


def _author_files(author):
    fields = []
    _track_file(author.headshot, fields)
    for book in author.books.all():
        _track_file(book.cover_image, fields)
        _track_file(book.sample_chapter_path, fields)
        for review in book.reviews.all():
            _track_file(review.photo_path, fields)
        for award in book.awards.all():
            _track_file(award.icon_path, fields)
    return fields


@transaction.atomic
def sync_genre_catalog(tree):
    """Replace the lookup catalog with one validated three-level tree."""
    BookSubgenre.objects.all().delete()
    BookGenre.objects.all().delete()
    BookCategory.objects.all().delete()
    for category_name, genres in tree.items():
        category = BookCategory.objects.create(name=category_name)
        for genre_name, subgenres in genres.items():
            genre = BookGenre.objects.create(category=category, name=genre_name)
            BookSubgenre.objects.bulk_create(
                [
                    BookSubgenre(genre=genre, name=subgenre_name)
                    for subgenre_name in subgenres
                ]
            )


def genre_tree_from_database():
    tree = {}
    categories = BookCategory.objects.prefetch_related("genres__subgenres")
    for category in categories:
        tree[category.name] = {
            genre.name: [subgenre.name for subgenre in genre.subgenres.all()]
            for genre in category.genres.all()
        }
    return tree


def _persist_author_selections(author, selections):
    for position, name in enumerate(selections, start=1):
        category = BookCategory.objects.filter(name=name).first()
        if category is not None:
            AuthorCategory.objects.create(
                author=author,
                category=category,
                display_position=position,
            )
            continue
        genre = BookGenre.objects.filter(name=name).first()
        if genre is not None:
            AuthorGenre.objects.create(
                author=author,
                genre=genre,
                display_position=position,
            )
            continue
        subgenre = BookSubgenre.objects.filter(name=name).first()
        if subgenre is not None:
            AuthorSubgenre.objects.create(
                author=author,
                subgenre=subgenre,
                display_position=position,
            )
            continue
        raise ValueError(f"Unknown genre selection: {name}.")


def persist_onboarding(form, files, replace_author=None):
    """Atomically persist one author and all onboarding-owned book data."""
    saved_files = []
    try:
        with transaction.atomic():
            social = form.social_links
            author = Author(
                name=form.author_name,
                contact_email=str(form.author_email),
                site_domain=form.site_domain,
                site_tagline=_optional_text(form.site_tagline),
                bio_short=_optional_text(form.author_bio_short),
                bio_long=_optional_text(form.author_bio_long),
                primary_color=_optional_text(form.primary_color),
                secondary_color=_optional_text(form.secondary_color),
                newsletter_link=_optional_text(form.newsletter_link),
                social_twitter=_optional_text(social.twitter),
                social_instagram=_optional_text(social.instagram),
                social_facebook=_optional_text(social.facebook),
                social_tiktok=_optional_text(social.tiktok),
                social_youtube=_optional_text(social.youtube),
                social_goodreads=_optional_text(social.goodreads),
            )
            _assign_upload(
                author,
                "headshot",
                (
                    files.get(form.author_headshot_key)
                    if form.author_headshot_key
                    else None
                ),
                saved_files,
            )
            author.save()
            _persist_author_selections(author, form.genres)

            series_by_name = {}
            for onboarding_position, book_data in enumerate(form.books, start=1):
                genre = BookGenre.objects.get(
                    category__name=book_data.category,
                    name=book_data.genre,
                )
                subgenre = (
                    BookSubgenre.objects.get(
                        genre=genre,
                        name=book_data.subgenre,
                    )
                    if book_data.subgenre
                    else None
                )
                series = None
                if book_data.series_type == "series":
                    series = series_by_name.get(book_data.series_name)
                    if series is None:
                        series = Series.objects.create(
                            author=author,
                            name=book_data.series_name,
                            total_books=book_data.series_length,
                            is_complete=book_data.series_is_complete,
                        )
                        series_by_name[book_data.series_name] = series
                    elif series.total_books != book_data.series_length:
                        raise ValueError(
                            "Books in the same series must use the same total."
                        )
                    elif series.is_complete != book_data.series_is_complete:
                        raise ValueError(
                            "Books in the same series must use the same completion status."
                        )

                book = Book(
                    author=author,
                    onboarding_position=onboarding_position,
                    title=book_data.title,
                    description=book_data.description,
                    buy_links=[str(link) for link in book_data.buy_links],
                    genre=genre,
                    subgenre=subgenre,
                    series=series,
                    number_in_series=book_data.book_number,
                    perfect_for=_optional_text(book_data.perfect_for),
                    enjoy_if=_optional_text(book_data.enjoy_if),
                )
                _assign_upload(
                    book,
                    "cover_image",
                    files[book_data.cover_image_key],
                    saved_files,
                )
                sample_upload = (
                    files.get(book_data.sample_chapter_key)
                    if book_data.sample_chapter_key
                    else None
                )
                _assign_upload(
                    book,
                    "sample_chapter_path",
                    sample_upload,
                    saved_files,
                )
                book.sample_chapter_name = _original_basename(sample_upload)
                book.save()

                for position, review in enumerate(
                    book_data.editorial_reviews,
                    start=1,
                ):
                    saved_review = BookReview(
                        book=book,
                        display_position=position,
                        is_editorial=True,
                        reviewer_name=review.reviewer_name,
                        credentials=None,
                        quotation=review.quotation,
                        original_review_url=(
                            _optional_text(review.original_review_url) or None
                        ),
                        stars=review.stars,
                        is_starred_review=review.is_starred_review,
                    )
                    if review.photo_key:
                        _assign_upload(
                            saved_review,
                            "photo_path",
                            files.get(review.photo_key),
                            saved_files,
                        )
                    saved_review.save()

                for position, review in enumerate(
                    book_data.other_reviews,
                    start=1,
                ):
                    saved_review = BookReview(
                        book=book,
                        display_position=position,
                        is_editorial=False,
                        reviewer_name=review.reviewer_name,
                        credentials=_optional_text(review.credentials) or None,
                        quotation=review.quotation,
                        original_review_url=(
                            _optional_text(review.original_review_url) or None
                        ),
                        stars=review.stars,
                        is_starred_review=review.is_starred_review,
                    )
                    if review.photo_key:
                        _assign_upload(
                            saved_review,
                            "photo_path",
                            files.get(review.photo_key),
                            saved_files,
                        )
                    saved_review.save()

                for position, award in enumerate(book_data.awards, start=1):
                    saved_award = BookAward(
                        book=book,
                        display_position=position,
                        name=award.name,
                    )
                    _assign_upload(
                        saved_award,
                        "icon_path",
                        files[award.icon_key],
                        saved_files,
                    )
                    saved_award.save()
    except Exception:
        _delete_files(saved_files)
        raise

    if replace_author is not None and replace_author.pk != author.pk:
        old_files = _author_files(replace_author)
        replace_author.delete()
        _delete_files(old_files)

    return author


def _file_url(field):
    return field.url if field and field.name else None


def _author_genre_selections(author):
    selections = [
        (item.display_position, item.category.name)
        for item in author.authorcategory_set.select_related("category")
    ]
    selections.extend(
        (item.display_position, item.genre.name)
        for item in author.authorgenre_set.select_related("genre")
    )
    selections.extend(
        (item.display_position, item.subgenre.name)
        for item in author.authorsubgenre_set.select_related("subgenre")
    )
    return [name for _, name in sorted(selections)]


def serialize_author(author):
    return {
        "id": str(author.pk),
        "name": author.name,
        "contact_email": author.contact_email,
        "site_domain": author.site_domain,
        "site_tagline": author.site_tagline,
        "bio_short": author.bio_short,
        "bio_long": author.bio_long,
        "genres": _author_genre_selections(author),
        "primary_color": author.primary_color,
        "secondary_color": author.secondary_color,
        "newsletter_link": author.newsletter_link,
        "headshot_url": _file_url(author.headshot),
        "social_links": {
            name: value
            for name, value in {
                "twitter": author.social_twitter,
                "instagram": author.social_instagram,
                "facebook": author.social_facebook,
                "tiktok": author.social_tiktok,
                "youtube": author.social_youtube,
                "goodreads": author.social_goodreads,
            }.items()
            if value
        },
    }


def serialize_book(book):
    return {
        "id": str(book.pk),
        "author_id": str(book.author_id),
        "onboarding_position": book.onboarding_position,
        "title": book.title,
        "cover_image_url": _file_url(book.cover_image),
        "description": book.description,
        "buy_links": book.buy_links,
        "category": {
            "id": book.genre.category_id,
            "name": book.genre.category.name,
        },
        "genre": {"id": book.genre_id, "name": book.genre.name},
        "subgenre": (
            {"id": book.subgenre_id, "name": book.subgenre.name}
            if book.subgenre_id
            else None
        ),
        "series": (
            {
                "id": str(book.series_id),
                "name": book.series.name,
                "total_books": book.series.total_books,
                "is_complete": book.series.is_complete,
            }
            if book.series_id
            else None
        ),
        "number_in_series": book.number_in_series,
        "editorial_reviews": [
            {
                "reviewer_name": review.reviewer_name,
                "credentials": review.credentials,
                "quotation": review.quotation,
                "original_review_url": review.original_review_url,
                "photo_url": _file_url(review.photo_path),
                "stars": review.stars,
                "is_starred_review": review.is_starred_review,
            }
            for review in book.reviews.all()
            if review.is_editorial
        ],
        "other_reviews": [
            {
                "reviewer_name": review.reviewer_name,
                "credentials": review.credentials,
                "quotation": review.quotation,
                "original_review_url": review.original_review_url,
                "photo_url": _file_url(review.photo_path),
                "stars": review.stars,
                "is_starred_review": review.is_starred_review,
            }
            for review in book.reviews.all()
            if not review.is_editorial
        ],
        "awards": [
            {"name": award.name, "icon_url": _file_url(award.icon_path)}
            for award in book.awards.all()
        ],
        "perfect_for": book.perfect_for,
        "enjoy_if": book.enjoy_if,
        "sample_chapter_url": (
            f"/books/{book.pk}/sample-chapter"
            if book.sample_chapter_path
            else None
        ),
        "sample_chapter_name": book.sample_chapter_name,
    }
