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
