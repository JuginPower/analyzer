from django.shortcuts import render, redirect, get_object_or_404


def index(request):
    return render(request, 'stocks/index.html')