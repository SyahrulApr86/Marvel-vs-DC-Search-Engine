from django.urls import path
from example_app.views import *

urlpatterns = [
    path('', index, name='index'),
    path('search', search_result, name='search_result')
]