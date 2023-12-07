from django.urls import path
from marvel_dc_app.views import *

app_name = 'marvel_dc_app'

urlpatterns = [
    path('', index, name='index'),
    path('search_result/', search_result, name='search_result'),
    path('search_result/person', search_result_person, name="search_result_person"),
    path('search_result/film', search_result_film, name="search_result_film"),
    path('search', search_result, name='search_result'),
    path('film', get_film_detail, name='get_film_detail'),
    path('person', get_person_detail, name='get_person_detail')

]