from django.db import models

# Create your models here.

class Atividade(models.Model):
    servidor_nome = models.CharField(max_length=200)
    servidor_matricula = models.CharField(max_length=20, blank=True, null=True)
    servidor_cargo = models.CharField(max_length=100, blank=True, null=True)

    tipo_atividade = models.CharField(
        max_length=50,
        choices=[("Viagem", "Viagem")]
    )
    #periodo_viagem = models.CharField(max_length=100, blank=True, null=True)
    dias_diarias = models.CharField(max_length=50, blank=True, null=True)
    PERNOITE_CHOICES = [("Sim", "Sim"), ("Não", "Não")]
    pernoite = models.CharField(max_length=3, choices=PERNOITE_CHOICES, default="Não")
    transporte = models.CharField(max_length=50, blank=True, null=True)
    objetivo = models.TextField(blank=True, null=True)
    data_ida = models.DateField(blank=True, null=True)
    data_retorno = models.DateField(blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo_atividade} - {self.servidor_nome} ({self.servidor_matricula})"

