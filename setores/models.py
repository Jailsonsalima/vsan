from django.db import models

# Create your models here.
class Setor(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    nome = models.CharField(max_length=100, verbose_name='Nome do Setor', unique=True)

    def __str__(self):
        return self.nome