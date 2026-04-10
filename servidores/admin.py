from django.contrib import admin

# Register your models here.
from .models import Servidor
@admin.register(Servidor)
class ServidorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'matricula', 'cpf', 'vinculo')
    search_fields = ('nome', 'matricula', 'cpf', 'vinculo')
    