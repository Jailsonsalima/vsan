from django.contrib import admin

# Register your models here.

from .models import Usuario
@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'tipo_usuario', 'is_active')
    list_filter = ('tipo_usuario', 'is_active')
    search_fields = ('username', 'email')