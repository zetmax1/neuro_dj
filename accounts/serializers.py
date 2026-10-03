from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from accounts.permissions import get_role

User = get_user_model()


class UserRegistrationSerializer(serializers.Serializer):
    """
    Manual serializer for user registration.
    Inherits from Serializer for high performance and explicit field mapping.
    """
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"}
    )
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def validate_email(self, value: str) -> str:
        # Use all_objects to prevent re-registration with a soft-deleted email
        if User.all_objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs.get("password") != attrs.get("password_confirm"):
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data: dict[str, Any]) -> Any:
        validated_data.pop("password_confirm", None)
        password = validated_data.pop("password")
        
        # Use make_password for secure hashing
        user = User(
            email=validated_data["email"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            password=make_password(password)
        )
        user.save()
        
        # Assign newly registered users to the Student group by default
        from django.contrib.auth.models import Group
        try:
            student_group = Group.objects.get(name="Student")
            user.groups.add(student_group)
        except Group.DoesNotExist:
            # Fallback in case management command hasn't been run yet
            student_group, _ = Group.objects.get_or_create(name="Student")
            user.groups.add(student_group)
            
        return user



class UserDetailSerializer(serializers.Serializer):
    """
    Manual read-only serializer for fetching user profile details.
    """
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_staff = serializers.BooleanField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)
    is_deleted = serializers.BooleanField(read_only=True)
    deleted_at = serializers.DateTimeField(read_only=True)
    is_simulated = serializers.BooleanField(read_only=True)
    role = serializers.SerializerMethodField(read_only=True)

    def get_role(self, obj) -> str:
        return get_role(obj)


class UserUpdateSerializer(serializers.Serializer):
    """
    Manual serializer for applying partial profile updates.
    """
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    
    def update(self, instance: Any, validated_data: dict[str, Any]) -> Any:
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.save(update_fields=["first_name", "last_name", "updated_at"] if hasattr(instance, "updated_at") else ["first_name", "last_name"])
        return instance


ROLE_GROUPS: dict[str, tuple[str, ...]] = {
    "student": (),
    "instructor": ("Instructor",),
    "admin": ("Admin",),
}


class UserAdminUpdateSerializer(serializers.Serializer):
    """
    What an admin may change on another account: the role and the active flag.

    The role is expressed through the ``Instructor`` and ``Admin`` groups,
    which is exactly what ``get_role`` reads. Two cases cannot be expressed
    that way and are refused rather than half-applied: a superuser is always
    an admin, and a staff member is always at least an instructor. An admin
    may not change their own role or deactivate themselves (no lock-out).
    """

    role = serializers.ChoiceField(choices=list(ROLE_GROUPS), required=False)
    is_active = serializers.BooleanField(required=False)

    def validate(self, attrs):
        request = self.context.get("request")
        user = self.instance
        if request is not None and user.pk == request.user.pk:
            raise serializers.ValidationError(
                {"reason": "self", "detail": "You cannot change your own role or active flag."}
            )
        role = attrs.get("role")
        if role is not None and role != "admin" and user.is_superuser:
            raise serializers.ValidationError(
                {"reason": "superuser", "detail": "A superuser is always an admin."}
            )
        if role == "student" and user.is_staff:
            raise serializers.ValidationError(
                {"reason": "staff", "detail": "A staff member is always at least an instructor."}
            )
        return attrs

    def update(self, instance, validated_data):
        from django.contrib.auth.models import Group
        from django.db import transaction

        with transaction.atomic():
            role = validated_data.get("role")
            if role is not None:
                managed = {name for names in ROLE_GROUPS.values() for name in names}
                instance.groups.remove(*Group.objects.filter(name__in=managed))
                for name in ROLE_GROUPS[role]:
                    instance.groups.add(Group.objects.get_or_create(name=name)[0])
            if "is_active" in validated_data:
                instance.is_active = validated_data["is_active"]
                instance.save(update_fields=["is_active"])
        return instance
