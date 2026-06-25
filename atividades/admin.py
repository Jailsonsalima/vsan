from django.contrib import admin
from .models import Atividade, RecursoAtivo, DiaEspecial, ValorDiaria

@admin.register(Atividade)
class AtividadeAdmin(admin.ModelAdmin):
    list_display = ("n_memorando", "tipo_atividade", "municipio", "data_ida", "data_retorno", "pernoite", "data_criacao", "portaria_numero", "data_prestacao", "objetivo_prestacao", "devolucao")
    list_filter = ("tipo_atividade", "pernoite", "data_ida", "data_retorno", "data_criacao", "devolucao")
    search_fields = ("n_memorando", "municipio", "objetivo", "data_criacao", "portaria_numero", "objetivo_prestacao")
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


@admin.register(ValorDiaria)
class ValorDiariaAdmin(admin.ModelAdmin):
    list_display = ("tipo", "valor", "atualizado_em")   # colunas visíveis na listagem
    list_filter = ("tipo",)                             # filtro lateral por tipo
    search_fields = ("tipo",)                           # campo de busca
    ordering = ("tipo",)                                # ordenação padrão
