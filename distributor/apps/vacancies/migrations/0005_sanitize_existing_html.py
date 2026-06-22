from django.db import migrations


def sanitize_existing(apps, schema_editor):
    from apps.core.sanitizer import sanitize_html

    Vacancy = apps.get_model("vacancies", "Vacancy")
    for obj in Vacancy.objects.all():
        changed = False
        for field in ("description", "requirements", "conditions"):
            cleaned = sanitize_html(getattr(obj, field))
            if cleaned != getattr(obj, field):
                setattr(obj, field, cleaned)
                changed = True
        if changed:
            obj.save(update_fields=["description", "requirements", "conditions"])


class Migration(migrations.Migration):
    dependencies = [
        ("vacancies", "0004_alter_vacancy_city_alter_vacancy_conditions_and_more"),
    ]
    operations = [
        migrations.RunPython(sanitize_existing, migrations.RunPython.noop),
    ]
