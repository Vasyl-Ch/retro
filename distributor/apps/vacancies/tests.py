from django.test import TestCase

from .models import Vacancy


class VacancySanitizationTests(TestCase):
    def test_script_and_handlers_stripped_on_save(self):
        v = Vacancy.objects.create(
            title="Dev",
            description="<p>job</p><script>alert(1)</script>",
            requirements='<ul><li>x</li></ul><img src="http://a/b.png" onerror="alert(1)">',
            conditions="<p>nice</p>",
        )
        # No refresh_from_db: SummernoteTextField masks disallowed tags on
        # read (from_db_value); assert the in-memory instance our save()
        # sanitized (save() reassigns the fields before super().save()).
        self.assertNotIn("<script", v.description)
        self.assertNotIn("onerror", v.requirements)
        self.assertIn("<li>x</li>", v.requirements)
        self.assertIn("<p>nice</p>", v.conditions)
