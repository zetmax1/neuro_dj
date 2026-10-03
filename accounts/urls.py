from django.urls import path

from accounts.views import (
    CookieTokenRefreshView,
    CsrfTokenView,
    CustomTokenObtainPairView,
    LogoutView,
    UserListView,
    UserDetailView,
    UserProfileView,
    UserRegistrationView,
)

app_name = "accounts"

urlpatterns = [
    # Registration and Profile (CRUD)
    path("register/", UserRegistrationView.as_view(), name="register"),
    path("profile/", UserProfileView.as_view(), name="profile"),
    
    # Admin List / Delete
    path("users/", UserListView.as_view(), name="user_list"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="user_detail"),
    
    # D16: access token in the body, refresh token in an httpOnly cookie
    # scoped to /api/accounts/token/. Every cookie endpoint is CSRF-checked;
    # the SPA gets the token from csrf/.
    path("csrf/", CsrfTokenView.as_view(), name="csrf"),
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"),
    path("token/logout/", LogoutView.as_view(), name="token_logout"),
]
