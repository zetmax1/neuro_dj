from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from accounts.serializers import (
    UserDetailSerializer,
    UserRegistrationSerializer,
    UserUpdateSerializer,
)
from drf_spectacular.utils import extend_schema

User = get_user_model()


@extend_schema(tags=["Auth"])
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT login view with strict rate limiting to prevent brute-force attacks.
    Limits enforced by the 'login' throttle scope.
    """
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"


@extend_schema(tags=["Auth"])
class UserRegistrationView(generics.CreateAPIView):
    """
    Endpoint for new user registration. Allows unauthenticated access.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]


@extend_schema(tags=["Auth"])
class UserProfileView(APIView):
    """
    Endpoint for retrieving, updating, and soft-deleting the authenticated user's profile.
    Uses generic APIView to handle multiple HTTP verbs on the singleton resource (request.user).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Fetch the current user profile."""
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request: Request) -> Response:
        """Partially update the current user profile."""
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # Return full updated profile using DetailSerializer
        return Response(UserDetailSerializer(request.user).data, status=status.HTTP_200_OK)

    def delete(self, request: Request) -> Response:
        """Soft delete the authenticated user's account."""
        user = request.user
        user.delete()  # Triggers the overridden soft-delete method
        return Response(
            {"detail": "User account soft-deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )


@extend_schema(tags=["Auth"])
class UserListView(generics.ListAPIView):
    """
    Admin-only endpoint to list all users, including soft-deleted ones.
    """
    queryset = User.all_objects.all().order_by('-date_joined')
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAdminUser]


@extend_schema(tags=["Auth"])
class UserDetailView(generics.RetrieveDestroyAPIView):
    """
    Admin-only endpoint to retrieve or soft-delete a specific user.
    """
    queryset = User.all_objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_destroy(self, instance):
        instance.delete()  # Triggers the overridden soft-delete method

