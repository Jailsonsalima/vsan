from django.contrib import admin

# Register your models here.

from .models import Setor
@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'id')
    search_fields = ('nome', 'id')
