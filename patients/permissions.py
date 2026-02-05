# patients/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS


def _is_admin(user):
    return hasattr(user, 'profile') and user.profile.role == 'admin'


class IsPatientOwnerOrAdmin(BasePermission):
    """
    Read access: any authenticated user.
    Write access: only the patient's created_by user, or an admin.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if _is_admin(request.user):
            return True
        return obj.created_by == request.user


class IsRelatedPatientOwnerOrAdmin(BasePermission):
    """
    For objects that belong to a patient indirectly:
      - PatientFile  → obj.patient.created_by
      - Visit        → obj.patient.created_by
      - VitalSign    → obj.visit.patient.created_by

    Read access: any authenticated user.
    Write access: only the patient's creator or admin.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if _is_admin(request.user):
            return True

        # Walk up to the Patient object
        if hasattr(obj, 'patient'):
            return obj.patient.created_by == request.user
        if hasattr(obj, 'visit'):
            return obj.visit.patient.created_by == request.user
        return False
