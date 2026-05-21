from django.contrib import admin
from .models import Atividade, RecursoAtivo, DiaEspecial

@admin.register(Atividade)
class AtividadeAdmin(admin.ModelAdmin):
    list_display = ("n_memorando", "tipo_atividade", "municipio", "data_ida", "data_retorno", "pernoite", "data_criacao")
    list_filter = ("tipo_atividade", "pernoite", "data_ida", "data_retorno", "data_criacao")
    search_fields = ("n_memorando", "municipio", "objetivo", "data_criacao")
    filter_horizontal = ("servidores",)

@admin.register(RecursoAtivo)
class RecursoAtivoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "atualizado_em")
    list_filter = ("codigo",)
    search_fields = ("codigo",)
    
@admin.register(DiaEspecial)
class DiaEspecialAdmin(admin.ModelAdmin):
    list_display = ("data", "tipo", "nome")
    list_filter = ("tipo",)
    search_fields = ("nome",)
