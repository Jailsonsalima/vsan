from django.contrib import admin
from .models import Servidor, HistoricoSituacao

@admin.register(Servidor)
class ServidorAdmin(admin.ModelAdmin):
    list_display = ("nome", "matricula", "cargo", "setor", "disponivel")
    list_filter = ("vinculo", "setor", "disponivel")
    search_fields = ("nome", "matricula", "cpf")

@admin.register(HistoricoSituacao)
class HistoricoSituacaoAdmin(admin.ModelAdmin):
    list_display = ("data_registro", "servidor", "situacao", "mes", "ano")
    list_filter = ("servidor", "situacao", "mes", "ano")
    search_fields = ("servidor", "situacao", "mes", "ano")