from django.urls import path

from .views import (
    MotorApprovalDetailView,
    MotorApprovalListView,
    MotorApproveView,
    MotorCreateView,
    MotorDeleteView,
    MotorDetailView,
    MotorListView,
    MotorRejectView,
    MotorUpdateView,
    StockCreateView,
    StockDeleteView,
    StockDetailView,
    StockListView,
    StockUpdateView,
)


app_name = "inventory"

urlpatterns = [
    # Motor URLs
    path("", MotorListView.as_view(), name="motor-list"),
    path("create/", MotorCreateView.as_view(), name="motor-create"),
    path("<int:pk>/", MotorDetailView.as_view(), name="motor-detail"),
    path("<int:pk>/edit/", MotorUpdateView.as_view(), name="motor-update"),
    path("<int:pk>/delete/", MotorDeleteView.as_view(), name="motor-delete"),
    # Motor Approval URLs
    path("approval/", MotorApprovalListView.as_view(), name="motor-approval-list"),
    path("approval/<int:pk>/", MotorApprovalDetailView.as_view(), name="motor-approval-detail"),
    path("approval/<int:pk>/approve/", MotorApproveView.as_view(), name="motor-approve"),
    path("approval/<int:pk>/reject/", MotorRejectView.as_view(), name="motor-reject"),
    # Stock URLs
    path("stock/", StockListView.as_view(), name="stock-list"),
    path("stock/create/", StockCreateView.as_view(), name="stock-create"),
    path("stock/<int:pk>/", StockDetailView.as_view(), name="stock-detail"),
    path("stock/<int:pk>/edit/", StockUpdateView.as_view(), name="stock-update"),
    path("stock/<int:pk>/delete/", StockDeleteView.as_view(), name="stock-delete"),
]
