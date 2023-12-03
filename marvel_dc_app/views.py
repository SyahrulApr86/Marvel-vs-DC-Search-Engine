from django.shortcuts import render

def index(request):
    return render(request, 'index.html')

def search_result_person(request):
    response = {}
    return render(request, 'search_person.html', response)

def search_result_film(request):
    response = {}
    return render(request, 'search_film.html', response)
