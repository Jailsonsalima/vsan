from django.db import models
from servidores.models import Servidor
from setores.models import Setor
from usuarios.models import Usuario
from agendamentos.models import MotoristaExterno

# Create your models here.

class RecursoAtivo(models.Model):
    codigo = models.CharField(max_length=2, choices=[("01", "Exercício"), ("02", "Superávit")])
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.codigo}"

class Atividade(models.Model):
    #servidor_nome = models.CharField(max_length=200)
    #servidor_matricula = models.CharField(max_length=20, blank=True, null=True)
    #servidor_cargo = models.CharField(max_length=100, blank=True, null=True)

    tipo_atividade = models.CharField(
        max_length=50,
        choices=[("Viagem", "Viagem")], blank=True, null=True
    )
    #periodo_viagem = models.CharField(max_length=100, blank=True, null=True)
    dias_diarias = models.CharField(max_length=50, blank=True, null=True)
    PERNOITE_CHOICES = [("Sim", "Sim"), ("Não", "Não")]
    pernoite = models.CharField(max_length=3, choices=PERNOITE_CHOICES, default="Não")
    transporte = models.CharField(max_length=50, blank=True, null=True)
    municipio = models.CharField(max_length=100, blank=True, null=True)
    objetivo = models.TextField(blank=True, null=True)
    data_ida = models.DateField(blank=True, null=True)
    data_retorno = models.DateField(blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    recurso_codigo = models.CharField(max_length=2, choices=[("01", "Exercício"), ("02", "Superávit")], default="01")
    servidores = models.ManyToManyField(Servidor, related_name="atividades")  # vínculo
    n_memorando = models.CharField(max_length=10, verbose_name='Nº do Memorando', unique=True, blank=True, null=True)
    chefe_imediato = models.ForeignKey(Setor, on_delete=models.SET_NULL, null=True, blank=True, related_name="atividades_chefiadas")
    numero_processo = models.CharField(max_length=50, blank=True, null=True)
    criador = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="atividades_criadas", null=True, blank=True)
    motoristas_externos = models.ManyToManyField(MotoristaExterno, related_name="atividades", blank=True)  # vínculo com motoristas externos
    def __str__(self):
        return f"{self.data_criacao} - {self.data_ida} ({self.data_retorno}) - {self.objetivo[:30]}..."
