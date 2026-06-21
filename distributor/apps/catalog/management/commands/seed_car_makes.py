"""Заповнює довідник марок авто (Brand) для пресета «Автосалон».

Ідемпотентно: повторний запуск не створює дублікатів (get_or_create по name) і лагодить
порожні slug. Логотипи не обов'язкові (Brand.logo тепер blank/null).

Slug рахується через slugify (ASCII), бо URL використовує конвертер ``<slug:slug>`` (лише
ASCII). Для кириличних назв задаємо явні ASCII-slug у SLUG_OVERRIDES.
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.catalog.models import Brand

CAR_MAKES = [
    # Європа
    "Audi", "BMW", "Mercedes-Benz", "Volkswagen", "Porsche", "Opel", "Škoda",
    "Seat", "Cupra", "Volvo", "Polestar", "Saab", "Renault", "Peugeot", "Citroën",
    "DS", "Dacia", "Fiat", "Alfa Romeo", "Lancia", "Abarth", "Ferrari", "Lamborghini",
    "Maserati", "Bugatti", "Land Rover", "Jaguar", "Aston Martin", "Bentley",
    "Rolls-Royce", "McLaren", "Lotus", "Mini", "Smart", "Maybach", "MG",
    # Азія
    "Toyota", "Lexus", "Honda", "Acura", "Mazda", "Nissan", "Infiniti", "Datsun",
    "Mitsubishi", "Subaru", "Suzuki", "Isuzu", "Daihatsu", "Hyundai", "Genesis",
    "Kia", "SsangYong", "Daewoo", "Tata", "Mahindra", "Proton",
    # Китай
    "Geely", "Chery", "BYD", "Great Wall", "Haval", "Changan", "Dongfeng", "FAW",
    "JAC", "Exeed", "Jetour", "Omoda", "Zeekr", "Nio", "Xpeng", "Hongqi", "Tank",
    # США
    "Ford", "Chevrolet", "Cadillac", "Chrysler", "Dodge", "RAM", "Jeep", "GMC",
    "Buick", "Lincoln", "Hummer", "Pontiac", "Tesla", "Rivian", "Lucid",
    # СНД / локальні
    "ЗАЗ", "ВАЗ / Lada", "ГАЗ", "УАЗ", "Москвич", "Богдан",
]

# Явні ASCII-slug для назв, які slugify перетворює на порожній рядок.
SLUG_OVERRIDES = {
    "ЗАЗ": "zaz",
    "ВАЗ / Lada": "vaz-lada",
    "ГАЗ": "gaz",
    "УАЗ": "uaz",
    "Москвич": "moskvich",
    "Богдан": "bogdan",
}


def _slug_for(name: str) -> str:
    return SLUG_OVERRIDES.get(name) or slugify(name)


class Command(BaseCommand):
    help = "Створити довідник марок авто (Brand) для пресета «Автосалон»"

    def handle(self, *args, **options) -> None:
        created = 0
        for order, name in enumerate(CAR_MAKES, start=1):
            slug = _slug_for(name)
            obj, was_created = Brand.objects.get_or_create(
                name=name,
                defaults={"slug": slug, "order": order, "is_active": True},
            )
            created += int(was_created)
            if not obj.slug:  # полагодити записи з попереднього (збійного) запуску
                obj.slug = slug
                obj.save(update_fields=["slug"])
        self.stdout.write(
            self.style.SUCCESS(
                f"Марки авто: створено {created}, всього у довіднику {Brand.objects.count()}."
            )
        )
