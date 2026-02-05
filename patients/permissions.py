# patients/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS


def _is_admin(user):
    return hasattr(user, 'profile') and user.profile.role == 'admin'


class IsPatientOwnerOrAdmin(BasePermission):
    """
    For Patient objects.
    Read access: any authenticated user.
    Write access: only the patient's created_by user, or an admin.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if _is_admin(request.user):
            return True
        return obj.created_by == request.user


class IsPatientFileOwnerOrAdmin(BasePermission):
    """
    For PatientFile objects.
    Read access: any authenticated user.
    Write access: only the patient's creator or admin.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if _is_admin(request.user):
            return True
        return obj.patient.created_by == request.user


class IsVisitOwnerOrAdmin(BasePermission):
    """
    For Visit objects.
    Read access: any authenticated user.
    Write access: only the visit's created_by (the doctor who created it), or an admin.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if _is_admin(request.user):
            return True
        # Check visit's own created_by field
        return obj.created_by == request.user


class IsVitalSignOwnerOrAdmin(BasePermission):
    """
    For VitalSign objects.
    Read access: any authenticated user.
    Write access: only the visit's creator (the doctor who created the visit), or an admin.
    VitalSigns inherit ownership from their parent Visit.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if _is_admin(request.user):
            return True
        # Check the parent visit's created_by
        return obj.visit.created_by == request.user
