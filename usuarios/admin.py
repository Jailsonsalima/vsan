from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ("username", "email", "tipo_usuario", "matricula", "is_active", "is_staff")
    list_filter = ("tipo_usuario", "is_active", "is_staff")
    search_fields = ("username", "email", "matricula")
    fieldsets = UserAdmin.fieldsets + (
        ("Informações adicionais", {"fields": ("tipo_usuario", "matricula", "servidor")}),
    )
