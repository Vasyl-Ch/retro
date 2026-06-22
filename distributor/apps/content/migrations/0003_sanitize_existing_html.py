from django.db import migrations


def sanitize_existing(apps, schema_editor):
    from apps.core.sanitizer import sanitize_html

    News = apps.get_model("content", "News")
    Promo = apps.get_model("content", "Promo")
    for obj in News.objects.all():
        cleaned = sanitize_html(obj.content)
        if cleaned != obj.content:
            obj.content = cleaned
            obj.save(update_fields=["content"])
    for obj in Promo.objects.all():
        cleaned = sanitize_html(obj.description)
        if cleaned != obj.description:
            obj.description = cleaned
            obj.save(update_fields=["description"])


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0002_alter_banner_options_alter_news_options_and_more'),
    ]
    operations = [
        migrations.RunPython(sanitize_existing, migrations.RunPython.noop),
    ]
