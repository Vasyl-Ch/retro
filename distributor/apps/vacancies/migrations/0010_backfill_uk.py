from django.db import migrations

from apps.catalog.migrations._bilingua_backfill import backfill

TABLE_FIELDS = [
    ("vacancies_vacancy", ["title", "city", "short_tagline",
                            "description", "requirements", "conditions"]),
    ("vacancies_vacancyimage", ["caption"]),
]


def forwards(apps, schema_editor):
    backfill(schema_editor.connection, TABLE_FIELDS)


class Migration(migrations.Migration):

    dependencies = [
        ('vacancies', '0009_vacancy_city_en_vacancy_city_uk_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
