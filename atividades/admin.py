from django.contrib import admin

from atividades.models import Atividade

# Register your models here.
@admin.register(Atividade)
class AtividadeAdmin(admin.ModelAdmin):
    list_display = ("servidor_nome", "servidor_matricula", "tipo_atividade", "data_ida", "data_retorno", "dias_diarias", "pernoite", "transporte", "objetivo", "data_ida", "data_retorno", "data_criacao")
    search_fields = ("servidor_nome", "servidor_matricula", "tipo_atividade", "data_ida", "data_retorno", "dias_diarias", "data_criacao")