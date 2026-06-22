from django.views.generic import ListView, DetailView
from django.db.models import QuerySet
from .models import Vacancy


class VacancyListView(ListView):
    model = Vacancy
    template_name = "vacancies/list.html"
    context_object_name = "vacancies"
    paginate_by = 12

    def get_queryset(self) -> QuerySet:
        return Vacancy.objects.filter(is_active=True)


class VacancyDetailView(DetailView):
    model = Vacancy
    template_name = "vacancies/detail.html"

    def get_queryset(self) -> QuerySet:
        return Vacancy.objects.filter(is_active=True)
