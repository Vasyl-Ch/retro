from django.contrib import admin
from django.db.utils import OperationalError, ProgrammingError
from django.utils.translation import gettext_lazy as _

from apps.core.admin import image_preview_method
from apps.core.models import SiteSettings

from .models import Brand, Category, Product, ProductImage, ProductSpec, VehicleSpec


def _current_preset() -> str:
    """Поточний пресет сайту (для preset-aware конфігуратора). Безпечно за відсутності БД."""
    try:
        return SiteSettings.get_solo().preset
    except (OperationalError, ProgrammingError):  # БД ще не готова (міграції)
        return ""


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ["image", "image_preview", "order"]
    readonly_fields = ["image_preview"]

    image_preview = image_preview_method(
        "image", description=_("Прев’ю"), height=60, object_fit="contain"
    )


class VehicleSpecInline(admin.StackedInline):
    """Характеристики авто — лише для пресета «Автосалон»."""

    model = VehicleSpec
    can_delete = True
    max_num = 1
    extra = 1
    verbose_name = _("Характеристики авто")
    verbose_name_plural = _("Характеристики авто")


class ProductSpecInline(admin.TabularInline):
    """Довільні параметри (key-value) — конфігуратор для будь-якої вертикалі."""

    model = ProductSpec
    extra = 1
    fields = ["label", "value", "order"]


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["logo_preview", "name", "is_active", "order"]
    list_editable = ["is_active", "order"]
    list_display_links = ["name"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}

    logo_preview = image_preview_method(
        "logo", description=_("Лого"), height=40, object_fit="contain"
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "parent", "is_active"]
    list_editable = ["is_active"]
    list_display_links = ["name"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "image_preview",
        "name",
        "brand",
        "category",
        "price",
        "availability",
        "is_active",
        "is_featured",
        "order",
    ]
    list_editable = ["is_active", "is_featured", "order"]
    list_display_links = ["name"]
    list_filter = ["brand", "category", "availability", "is_active", "is_featured"]
    search_fields = ["name", "article", "brand__name", "vehicle__vin"]
    prepopulated_fields = {"slug": ("name",)}
    save_on_top = True

    # Секції форми (спільні для всіх пресетів). Авто-специфіка — в inline VehicleSpec.
    fieldsets = (
        (None, {"fields": ("brand", "category", "name", "slug", "article", "description", "image")}),
        (_("Ціна та наявність"), {
            "fields": ("price", "old_price", "currency", "availability", "location"),
        }),
        (_("Публікація"), {"fields": ("is_active", "is_featured", "order")}),
    )

    image_preview = image_preview_method("image", description=_("Фото"), height=50)

    def get_inlines(self, request, obj=None):
        """Конфігуратор preset-aware: блок характеристик авто — лише для пресета auto.

        Довільні параметри (ProductSpec) доступні завжди.
        """
        inlines = [ProductImageInline]
        if _current_preset() == SiteSettings.PRESET_AUTO:
            inlines.append(VehicleSpecInline)
        inlines.append(ProductSpecInline)
        return inlines
