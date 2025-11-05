from django.urls import path

from . import views

app_name = "audit"

urlpatterns = [
    path("", views.AuditLogListView.as_view(), name="list"),
    path("<int:pk>/", views.AuditLogDetailView.as_view(), name="detail"),
]
