from django.contrib import admin
from .models import Memorando
# Register your models here.
@admin.register(Memorando)
class MemorandoAdmin(admin.ModelAdmin):
    list_display = ("numero", "ano", "servidor", "setor", "data_uso", "devolvido")
    search_fields = ("numero", "ano", "servidor", "data_uso", "devolvido")


