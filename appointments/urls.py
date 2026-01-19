from django.urls import path
from .views import AppointmentListCreateAPIView, AppointmentDetailAPIView, DoctorListAPIView

urlpatterns = [
    path("", AppointmentListCreateAPIView.as_view(), name="appointment-list-create"),
    path("<int:pk>/", AppointmentDetailAPIView.as_view(), name="appointment-detail"),
    path("doctors/", DoctorListAPIView.as_view(), name="doctor-list"),
]