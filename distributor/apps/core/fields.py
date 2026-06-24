"""Project-local model fields.

``SummernoteTextField`` wraps django-summernote's field with a None-safe
``to_python``. Upstream's ``to_python`` calls ``bleach.clean(value)``
unconditionally, but Django's ``TextField.get_prep_value`` routes through
``to_python`` and ``bleach.clean(None)`` raises ``TypeError``. This bites
modeltranslation, which adds ``null=True`` ``_en``/``_uk`` copies of every
rich-text field: Django computes their column default via
``get_prep_value(None)`` during the schema migration, and a runtime
``save()`` of a row with an empty language variant does the same. We mirror
Django's own ``TextField.to_python`` guard (return ``None``/non-str as-is)
before delegating to the upstream sanitizing implementation.
"""

from django_summernote.fields import SummernoteTextField as _SummernoteTextField


class SummernoteTextField(_SummernoteTextField):
    def to_python(self, value):
        if value is None or not isinstance(value, str):
            return value
        return super().to_python(value)
