from django.urls import path
from . import views

app_name = 'parte_mortorios'

urlpatterns = [
    path('', views.index, name='index'),
]