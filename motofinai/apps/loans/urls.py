from django.urls import path

from .views import (
    FinancingTermCreateView,
    FinancingTermDeleteView,
    FinancingTermListView,
    FinancingTermUpdateView,
)


app_name = "terms"

urlpatterns = [
    path("", FinancingTermListView.as_view(), name="list"),
    path("create/", FinancingTermCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", FinancingTermUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", FinancingTermDeleteView.as_view(), name="delete"),
]
