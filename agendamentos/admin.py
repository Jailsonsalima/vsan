from django.contrib import admin
from .models import Agendamento, MotoristaExterno, AutorizacaoAgendamento, ProcessamentoAgendamento

@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ("id", "servidor", "municipio", "data_ida", "data_retorno", "solicitante", "status", "data_solicitacao")
    list_filter = ("status", "municipio", "data_ida", "data_retorno")
    search_fields = ("servidor__nome", "municipio", "solicitante__username")

@admin.register(MotoristaExterno)
class MotoristaExternoAdmin(admin.ModelAdmin):
    list_display = ("nome", "cpf", "matricula", "cargo", "disponivel", "conta", "telefone")
    list_filter = ("disponivel", "vinculo")
    search_fields = ("nome", "cpf", "matricula")

@admin.register(AutorizacaoAgendamento)
class AutorizacaoAgendamentoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "pode_visualizar", "pode_processar")
    list_filter = ("pode_visualizar", "pode_processar")
    search_fields = ("usuario__username",)

@admin.register(ProcessamentoAgendamento)
class ProcessamentoAgendamentoAdmin(admin.ModelAdmin):
    list_display = (
        "id", "agendamento", "tipo",
        "motorista_servidor", "motorista_externo", "data_processamento"
    )
    list_filter = ("tipo", "data_processamento")
    search_fields = (
        "agendamento__municipio",
        "motorista_servidor__nome",
        "motorista_externo__nome"
    )
    date_hierarchy = "data_processamento"