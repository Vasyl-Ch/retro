from django.db import migrations

from ._bilingua_backfill import backfill

TABLE_FIELDS = [
    ("catalog_brand", ["name", "description"]),
    ("catalog_category", ["name"]),
    ("catalog_product", ["name", "description", "location"]),
    ("catalog_vehiclespec", ["color"]),
    ("catalog_productspec", ["label", "value"]),
]


def forwards(apps, schema_editor):
    backfill(schema_editor.connection, TABLE_FIELDS)


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0007_brand_description_en_brand_description_uk_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
