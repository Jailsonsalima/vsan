from django.contrib import admin
from .models import Servidor

@admin.register(Servidor)
class ServidorAdmin(admin.ModelAdmin):
    list_display = ("nome", "matricula", "cargo", "setor", "disponivel")
    list_filter = ("vinculo", "setor", "disponivel")
    search_fields = ("nome", "matricula", "cpf")
