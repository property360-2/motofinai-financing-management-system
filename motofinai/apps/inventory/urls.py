from django.urls import path

from .views import (
    MotorCreateView,
    MotorDeleteView,
    MotorDetailView,
    MotorListView,
    MotorUpdateView,
)


app_name = "inventory"

urlpatterns = [
    path("", MotorListView.as_view(), name="motor-list"),
    path("create/", MotorCreateView.as_view(), name="motor-create"),
    path("<int:pk>/", MotorDetailView.as_view(), name="motor-detail"),
    path("<int:pk>/edit/", MotorUpdateView.as_view(), name="motor-update"),
    path("<int:pk>/delete/", MotorDeleteView.as_view(), name="motor-delete"),
]
