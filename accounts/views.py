from typing import Any

from django.contrib.auth import get_user_model
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from accounts.auth_cookies import (
    clear_refresh_cookie,
    enforce_csrf,
    read_refresh_cookie,
    set_refresh_cookie,
)
from accounts.permissions import IsAdminRole
from accounts.serializers import (
    UserAdminUpdateSerializer,
    UserDetailSerializer,
    UserRegistrationSerializer,
    UserUpdateSerializer,
)
from drf_spectacular.utils import extend_schema

User = get_user_model()


@extend_schema(tags=["Auth"])
@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfTokenView(APIView):
    """
    GET /api/accounts/csrf/ — sets the ``csrftoken`` cookie and returns its value.

    The SPA calls this once on start and sends the value back as
    ``X-CSRFToken`` on login, refresh and logout. Returning it in the body
    means the frontend does not have to read cookies of another port.
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    def get(self, request: Request) -> Response:
        return Response({"csrfToken": get_token(request._request)})


@extend_schema(tags=["Auth"])
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    POST /api/accounts/token/ — log in (D16).

    The access token comes back in the body, for the SPA to keep in memory.
    The refresh token does not: it is set as an httpOnly cookie, so no script
    can read it. CSRF-checked (login CSRF), and rate-limited by the ``login``
    throttle scope against brute force.
    """
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"
    authentication_classes: list = []

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        enforce_csrf(request._request)
        response = super().post(request, *args, **kwargs)
        refresh = response.data.pop("refresh", None)
        if refresh:
            set_refresh_cookie(response, refresh)
        return response


@extend_schema(tags=["Auth"])
class CookieTokenRefreshView(APIView):
    """
    POST /api/accounts/token/refresh/ — a new access token from the cookie.

    No body: the refresh token is read from the httpOnly cookie, rotated, and
    the new one is set in its place while the old one is blacklisted. A
    missing, expired or blacklisted token answers 401 and clears the cookie.
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    def post(self, request: Request) -> Response:
        enforce_csrf(request._request)
        token = read_refresh_cookie(request)
        if not token:
            return Response(
                {"detail": "No session.", "code": "no_refresh_cookie"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        serializer = TokenRefreshSerializer(data={"refresh": token})
        try:
            serializer.is_valid(raise_exception=True)
        except (TokenError, InvalidToken):
            response = Response(
                {"detail": "Session expired.", "code": "token_not_valid"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            clear_refresh_cookie(response)
            return response

        data = dict(serializer.validated_data)
        response = Response({"access": data["access"]}, status=status.HTTP_200_OK)
        set_refresh_cookie(response, data.get("refresh", token))
        return response


@extend_schema(tags=["Auth"])
class LogoutView(APIView):
    """
    POST /api/accounts/token/logout/ — end the session.

    Blacklists the refresh token from the cookie and clears it. Idempotent: a
    request without a valid cookie still answers 204 and clears it.
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    def post(self, request: Request) -> Response:
        enforce_csrf(request._request)
        token = read_refresh_cookie(request)
        if token:
            try:
                RefreshToken(token).blacklist()
            except TokenError:
                pass  # already expired or blacklisted: nothing left to revoke
        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_refresh_cookie(response)
        return response


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
    Admin-only list of every user, soft-deleted ones included.

    Filters: ``?role=student|instructor|admin`` and ``?simulated=true|false``
    (D13: simulator accounts are never research data, so the page can hide
    them). Guarded by the ``admin`` role from the API, not by ``is_staff``, so
    the frontend and the backend apply one rule (D15).
    """
    serializer_class = UserDetailSerializer
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        queryset = User.all_objects.all().order_by("-date_joined").prefetch_related("groups")
        simulated = self.request.query_params.get("simulated")
        if simulated in ("true", "false"):
            queryset = queryset.filter(is_simulated=(simulated == "true"))
        return queryset

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        response = super().list(request, *args, **kwargs)
        role = request.query_params.get("role")
        if role in ("student", "instructor", "admin"):
            rows = response.data["results"] if isinstance(response.data, dict) else response.data
            kept = [row for row in rows if row["role"] == role]
            if isinstance(response.data, dict):
                response.data["results"] = kept
            else:
                response.data = kept
        return response


@extend_schema(tags=["Auth"])
class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin-only: read one user, change their role or active flag, or
    soft-delete them.

    ``PATCH {"role": ...}`` assigns the role through the ``Instructor`` and
    ``Admin`` groups — the same rule ``get_role`` reads. ``PATCH {"is_active":
    false}`` deactivates (reversible), unlike DELETE, which soft-deletes.
    """
    queryset = User.all_objects.all()
    permission_classes = [IsAdminRole]
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return UserAdminUpdateSerializer
        return UserDetailSerializer

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        instance = self.get_object()
        serializer = UserAdminUpdateSerializer(
            instance, data=request.data, partial=True, context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserDetailSerializer(instance).data, status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        instance.delete()  # Triggers the overridden soft-delete method

