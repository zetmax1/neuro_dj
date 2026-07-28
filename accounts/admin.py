from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group

from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm

from accounts.forms import CustomUserCreationForm, CustomUserChangeForm
from accounts.models import CustomUser


admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin, ModelAdmin):
    """
    Custom user admin that safely displays soft delete fields and manages passwords correctly.
    """
    model = CustomUser
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    change_password_form = AdminPasswordChangeForm
    
    list_display = ("email", "first_name", "last_name", "is_staff", "is_active", "is_deleted")
    list_filter = ("is_deleted", "is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)
    readonly_fields = ("date_joined", "last_login", "deleted_at")

    # Use default UserAdmin fieldsets but adapted for our model
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
        ("Soft Delete", {"fields": ("is_deleted", "deleted_at")}),
    )

    # Required for custom User models with email as USERNAME_FIELD when adding new users in Admin
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "first_name", "last_name", "is_staff", "is_active")
        }),
    )

