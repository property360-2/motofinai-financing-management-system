from django.urls import path

from . import views

app_name = "archive"

urlpatterns = [
    path("", views.ArchiveListView.as_view(), name="list"),
    path("<int:pk>/", views.ArchiveDetailView.as_view(), name="detail"),
    path("<int:pk>/restore/", views.ArchiveRestoreView.as_view(), name="restore"),
]
