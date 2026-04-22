from django.contrib import admin
from .models import Setor

@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "chefe_imediato", "cargo_chefe", "matricula_chefe")
    search_fields = ("nome", "chefe_imediato", "matricula_chefe")
