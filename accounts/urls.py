from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import (
    CustomTokenObtainPairView,
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
    
    # SimpleJWT Auth (with throttling)
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
