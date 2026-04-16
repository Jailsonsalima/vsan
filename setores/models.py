from django.db import models

# Create your models here.
class Setor(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    nome = models.CharField(max_length=100, verbose_name='Nome do Setor', unique=True)
    chefe_imediato = models.ForeignKey("servidores.Servidor",on_delete=models.PROTECT,verbose_name="Chefe Imediato",null=True,blank=True)
    matricula_chefe = models.CharField(max_length=20, verbose_name="Matrícula", blank=True, null=True)
    def __str__(self):
        return self.nome