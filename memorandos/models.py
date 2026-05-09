from django.db import models

# Create your models here.
from django.conf import settings
from django.contrib.auth.models import User
from datetime import datetime
from setores.models import Setor

class Memorando(models.Model):
    numero = models.CharField(max_length=10)  # sem unique=True
    ano = models.IntegerField(default=datetime.now().year)
    servidor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    setor = models.ForeignKey(Setor, on_delete=models.SET_NULL, null=True, blank=True)
    data_uso = models.DateTimeField(null=True, blank=True)
    devolvido = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.numero}/{self.ano}"
    
    class Meta:
        unique_together = ('numero', 'ano')  # garante que não haja duplicidade por ano