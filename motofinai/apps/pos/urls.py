"""URL routing for POS payment system."""

from django.urls import path

from . import views

app_name = "pos"

urlpatterns = [
    # POS Terminal
    path("", views.POSTerminalView.as_view(), name="terminal"),
    path("search/", views.QuickPaySearchView.as_view(), name="search"),
    path("pay/<int:pk>/", views.QuickPayView.as_view(), name="quick_pay"),

    # Receipts
    path("receipt/<int:receipt_id>/", views.ReceiptView.as_view(), name="receipt_view"),

    # Session Management
    path("sessions/", views.POSSessionListView.as_view(), name="session_list"),
    path("sessions/open/", views.POSSessionOpenView.as_view(), name="session_open"),
    path("sessions/close/", views.POSSessionCloseView.as_view(), name="session_close"),
    path("sessions/<int:pk>/", views.POSSessionDetailView.as_view(), name="session_detail"),
]
