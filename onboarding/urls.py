from django.urls import path
from . import views

urlpatterns = [
    path("", views.index),
    path("onboard", views.onboard),
    path("generate", views.generate),
]
