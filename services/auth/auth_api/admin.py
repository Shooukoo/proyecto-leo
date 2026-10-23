from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    ordering = ["email"]
    list_display = ["email", "rol", "is_active"]
    fieldsets = UserAdmin.fieldsets[:0] + (
        (None, {"fields": ("email", "password")}),
        ("Datos", {"fields": ("first_name", "last_name", "telefono", "rol")}),
        (
            "Permisos",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "rol", "password1", "password2")}),
    )
