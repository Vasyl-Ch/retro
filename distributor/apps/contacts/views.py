from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext as _

from .forms import ContactForm


class ContactView(View):
    template_name = "contacts/contact.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, self.template_name, {"form": ContactForm()})

    def post(self, request: HttpRequest) -> HttpResponse:
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                _("Ваше повідомлення надіслано. Ми зв’яжемося з вами найближчим часом."),
            )
            return redirect("contacts:contact")
        return render(request, self.template_name, {"form": form})
