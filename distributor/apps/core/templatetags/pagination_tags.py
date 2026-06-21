"""Template helpers for pagination."""

from django import template

register = template.Library()


@register.filter(name="elided_range")
def elided_range(paginator, current_page: int):
    """Wrap Paginator.get_elided_page_range so it's usable as a template filter."""
    return paginator.get_elided_page_range(number=current_page, on_each_side=1, on_ends=1)
