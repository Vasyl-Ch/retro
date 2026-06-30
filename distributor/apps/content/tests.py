from django.test import TestCase
from django.utils import timezone

from .models import News, Promo


class NewsSanitizationTests(TestCase):
    def test_script_stripped_on_save(self):
        news = News.objects.create(
            title="T", preview="p",
            content="<p>ok</p><script>alert(1)</script>",
            published_at=timezone.now(),
        )
        # No refresh_from_db: SummernoteTextField masks disallowed tags on
        # read (from_db_value), which would hide whether OUR save()-time
        # sanitizer actually ran. save() reassigns self.content to the bleach
        # output before super().save(), so the returned instance reflects it.
        self.assertNotIn("<script", news.content)
        self.assertIn("<p>ok</p>", news.content)


class PromoSanitizationTests(TestCase):
    def test_script_stripped_on_save(self):
        promo = Promo.objects.create(
            title="T", description="<p>ok</p><script>alert(1)</script>",
        )
        self.assertNotIn("<script", promo.description)
        self.assertIn("<p>ok</p>", promo.description)


class NewsTranslatedSanitizationTests(TestCase):
    def test_script_stripped_in_both_languages(self):
        news = News.objects.create(
            title="T", preview="p", published_at=timezone.now(),
            content_en="<p>en</p><script>alert(1)</script>",
            content_uk="<p>uk</p><img src=x onerror=alert(2)>",
        )
        # Assert on the in-memory instance: save() reassigns the sanitized
        # value (the field does not mask on read), so this reflects our
        # save()-time sanitization of each language variant.
        self.assertNotIn("<script", news.content_en)
        self.assertIn("<p>en</p>", news.content_en)
        self.assertNotIn("onerror", news.content_uk)
        self.assertIn("<p>uk</p>", news.content_uk)
