from django.shortcuts import render, redirect


def index(request):
    context = {
    }
    return render(request, 'index.html', context)

def about(request):
    context = {
    }
    return render(request, 'about.html', context)


