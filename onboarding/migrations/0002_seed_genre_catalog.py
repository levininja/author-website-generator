import base64
import gzip
import json

from django.db import migrations


GENRE_CATALOG_GZIP_BASE64 = (
    "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"
)


def seed_genre_catalog(apps, schema_editor):
    BookCategory = apps.get_model("onboarding", "BookCategory")
    BookGenre = apps.get_model("onboarding", "BookGenre")
    BookSubgenre = apps.get_model("onboarding", "BookSubgenre")
    catalog = json.loads(
        gzip.decompress(base64.b64decode(GENRE_CATALOG_GZIP_BASE64))
    )

    for category_name, genres in catalog.items():
        category = BookCategory.objects.create(name=category_name)
        for genre_name, subgenres in genres.items():
            genre = BookGenre.objects.create(
                category=category,
                name=genre_name,
            )
            BookSubgenre.objects.bulk_create(
                [
                    BookSubgenre(genre=genre, name=subgenre_name)
                    for subgenre_name in subgenres
                ]
            )


def clear_genre_catalog(apps, schema_editor):
    apps.get_model("onboarding", "BookSubgenre").objects.all().delete()
    apps.get_model("onboarding", "BookGenre").objects.all().delete()
    apps.get_model("onboarding", "BookCategory").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("onboarding", "0001_semantic_domain_schema"),
    ]

    operations = [
        migrations.RunPython(seed_genre_catalog, clear_genre_catalog),
    ]
