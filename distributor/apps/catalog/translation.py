from modeltranslation.translator import TranslationOptions, register

from .models import Brand, Category, Product, ProductSpec, VehicleSpec


@register(Brand)
class BrandTranslationOptions(TranslationOptions):
    fields = ("name", "description")


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = ("name", "description", "location")


@register(VehicleSpec)
class VehicleSpecTranslationOptions(TranslationOptions):
    fields = ("color",)


@register(ProductSpec)
class ProductSpecTranslationOptions(TranslationOptions):
    fields = ("label", "value")
