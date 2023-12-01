from django.urls import path
from example_app.views import *

app_name = 'example_app'

urlpatterns = [
    path('', index, name='index'),
]