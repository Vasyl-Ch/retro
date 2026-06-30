from django.db import migrations

from apps.catalog.migrations._bilingua_backfill import backfill

TABLE_FIELDS = [
    ("content_banner", ["title", "subtitle", "button_text"]),
    ("content_news", ["title", "preview", "content"]),
    ("content_promo", ["title", "description"]),
]


def forwards(apps, schema_editor):
    backfill(schema_editor.connection, TABLE_FIELDS)


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0007_banner_button_text_en_banner_button_text_uk_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
