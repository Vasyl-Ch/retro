from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ["product", "product_name", "price", "currency", "quantity", "subtotal"]
    readonly_fields = ["subtotal"]

    @admin.display(description=_("Сума"))
    def subtotal(self, obj: OrderItem):
        return obj.subtotal


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "phone", "email", "status", "total_display", "created_at"]
    list_display_links = ["id", "name"]
    list_filter = ["status", "created_at"]
    list_editable = ["status"]
    search_fields = ["name", "phone", "email"]
    readonly_fields = ["created_at", "total_display"]
    inlines = [OrderItemInline]
    save_on_top = True

    @admin.display(description=_("Разом"))
    def total_display(self, obj: Order):
        return obj.total
