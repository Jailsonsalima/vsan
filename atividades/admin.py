from django.contrib import admin
from .models import Atividade

@admin.register(Atividade)
class AtividadeAdmin(admin.ModelAdmin):
    list_display = ("n_memorando", "tipo_atividade", "municipio", "data_ida", "data_retorno", "pernoite")
    list_filter = ("tipo_atividade", "pernoite", "data_ida", "data_retorno")
    search_fields = ("n_memorando", "municipio", "objetivo")
    filter_horizontal = ("servidores",)
