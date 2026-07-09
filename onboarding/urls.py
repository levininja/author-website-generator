from django.urls import path

from . import views

urlpatterns = [
    path("", views.index),
    path("onboard", views.onboard),
    path("onboarding", views.create_onboarding),
    path("genres", views.genres),
    path("authors/<uuid:author_id>", views.author_detail),
    path("authors/<uuid:author_id>/books", views.author_books),
    path("books/<uuid:book_id>", views.book_detail),
    path(
        "books/<uuid:book_id>/sample-chapter",
        views.download_sample_chapter,
        name="sample-chapter-download",
    ),
    path("generate", views.generate),
]
