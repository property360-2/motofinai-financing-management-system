from django.urls import path

from .views import PaymentScheduleListView, PaymentScheduleSearchView, RecordPaymentView

app_name = "payments"

urlpatterns = [
    path("schedules/", PaymentScheduleListView.as_view(), name="schedule-list"),
    path("schedules/search/", PaymentScheduleSearchView.as_view(), name="schedule-search"),
    path("schedules/<int:pk>/record/", RecordPaymentView.as_view(), name="record-payment"),
]
