# views.py
from django.shortcuts import render
from django.urls import reverse

def main_view(request):
    return render(request, 'main.html')
