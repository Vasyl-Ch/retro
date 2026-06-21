from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.catalog.models import Brand, Category, Product
from apps.content.models import Banner, News, Promo
from apps.vacancies.models import Vacancy


class Command(BaseCommand):
    help = "Создать тестовые данные для разработки"

    def handle(self, *args, **options) -> None:
        self._create_brands()
        self._create_categories()
        self._create_products()
        self._create_banners()
        self._create_news()
        self._create_promos()
        self._create_vacancies()
        self.stdout.write(self.style.SUCCESS("Тестовые данные созданы!"))

    def _create_brands(self) -> None:
        brands_data = [
            {
                "name": "TechBrand",
                "description": "Лидер в области технологий",
                "order": 1,
            },
            {"name": "EcoPro", "description": "Экологичные решения", "order": 2},
            {"name": "MaxForce", "description": "Мощные инструменты", "order": 3},
        ]
        for data in brands_data:
            Brand.objects.get_or_create(name=data["name"], defaults=data)
        self.stdout.write("  ✓ Бренды созданы")

    def _create_categories(self) -> None:
        cats = [
            {"name": "Оборудование", "slug": "oborudovanie"},
            {"name": "Расходники", "slug": "rashodniki"},
            {"name": "Аксессуары", "slug": "aksessuary"},
        ]
        for data in cats:
            Category.objects.get_or_create(name=data["name"], defaults=data)
        self.stdout.write("  ✓ Категории созданы")

    def _create_products(self) -> None:
        brand = Brand.objects.first()
        category = Category.objects.first()
        if not brand:
            return
        for i in range(1, 7):
            Product.objects.get_or_create(
                name=f"Продукт {i}",
                defaults={
                    "brand": brand,
                    "category": category,
                    "article": f"ART-{i:03d}",
                    "description": f"Описание продукта {i}",
                    "is_active": True,
                    "is_featured": i <= 4,
                    "order": i,
                },
            )
        self.stdout.write("  ✓ Товары созданы")

    def _create_banners(self) -> None:
        for i in range(1, 3):
            Banner.objects.get_or_create(
                title=f"Баннер {i}",
                defaults={
                    "subtitle": f"Подзаголовок баннера {i}",
                    "button_text": "Узнать больше",
                    "button_url": "/catalog/",
                    "is_active": True,
                    "order": i,
                },
            )
        self.stdout.write("  ✓ Баннеры созданы")

    def _create_news(self) -> None:
        for i in range(1, 4):
            News.objects.get_or_create(
                title=f"Новость {i}",
                defaults={
                    "preview": f"Краткое описание новости {i}",
                    "content": f"<p>Полный текст новости {i}</p>",
                    "is_active": True,
                    "published_at": timezone.now(),
                },
            )
        self.stdout.write("  ✓ Новости созданы")

    def _create_promos(self) -> None:
        from datetime import date, timedelta

        today = date.today()
        Promo.objects.get_or_create(
            title="Летняя акция",
            defaults={
                "slug": "letnyaya-akciya",
                "description": "<p>Скидки до 30% на всё оборудование</p>",
                "date_start": today,
                "date_end": today + timedelta(days=30),
                "is_active": True,
            },
        )
        Promo.objects.get_or_create(
            title="Завершённая акция",
            defaults={
                "slug": "zavershennaya-akciya",
                "description": "<p>Акция уже завершена</p>",
                "date_start": today - timedelta(days=60),
                "date_end": today - timedelta(days=30),
                "is_active": True,
            },
        )
        self.stdout.write("  ✓ Акции созданы")

    def _create_vacancies(self) -> None:
        vacancies_data = [
            {
                "title": "Менеджер по продажам",
                "slug": "menedzher-po-prodazham",
                "city": "Киев",
                "description": "<p>Ищем активного менеджера по продажам</p>",
                "is_urgent": True,
            },
            {
                "title": "Складской работник",
                "slug": "skladskoy-rabotnik",
                "city": "Харьков",
                "description": "<p>Работа на складе, полная занятость</p>",
                "is_urgent": False,
            },
        ]
        for data in vacancies_data:
            Vacancy.objects.get_or_create(title=data["title"], defaults=data)
        self.stdout.write("  ✓ Вакансии созданы")
