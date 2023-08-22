from django.shortcuts import render
from django.http import HttpResponse


def get_about_page(request):
    return HttpResponse("<h1>About page</h1>")
