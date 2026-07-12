from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("onboarding", "0006_add_generation_job"),
    ]

    operations = [
        migrations.AddField(
            model_name="generationjob",
            name="preview_url",
            field=models.URLField(blank=True, max_length=2048, null=True),
        ),
    ]
