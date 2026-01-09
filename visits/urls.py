from django.urls import path
from .views import VisitListCreateView, VisitDetailView

urlpatterns = [
    path("", VisitListCreateView.as_view(), name="visit-list-create"),
    path("<int:pk>/", VisitDetailView.as_view(), name="visit-detail"),
]