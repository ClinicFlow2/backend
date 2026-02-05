from django.urls import path
from .views import (
    AppointmentListCreateAPIView,
    AppointmentDetailAPIView,
    DoctorListAPIView,
    TriggerSmsRemindersView,
)

urlpatterns = [
    path("", AppointmentListCreateAPIView.as_view(), name="appointment-list-create"),
    path("<int:pk>/", AppointmentDetailAPIView.as_view(), name="appointment-detail"),
    path("doctors/", DoctorListAPIView.as_view(), name="doctor-list"),
    # Cron endpoint for SMS reminders (protected by token)
    path("cron/send-reminders/", TriggerSmsRemindersView.as_view(), name="cron-send-reminders"),
]