from django.db import models

class Servidor(models.Model):
    nome = models.CharField(max_length=200)
    endereco = models.CharField(max_length=255)
    vinculo = models.CharField(
        max_length=50,
        choices=[
            ("Servidor do Órgão", "Servidor do Órgão"),
            ("Servidor Cedido", "Servidor Cedido"),
            ("Colaborador Eventual", "Colaborador Eventual"),
        ]
    )
    matricula = models.CharField(max_length=20, unique=True)
    lotacao = models.ForeignKey("setores.Setor", on_delete=models.PROTECT, null=True, blank=True)
    cargo = models.CharField(max_length=100)
    funcao = models.CharField(max_length=150, blank=True, null=True)
    cpf = models.CharField(max_length=14, unique=True)
    rg = models.CharField(max_length=20, blank=True, null=True)
    nascimento = models.DateField(blank=True, null=True)
    banco = models.CharField(max_length=50, blank=True, null=True)
    agencia = models.CharField(max_length=20, blank=True, null=True)
    conta = models.CharField(max_length=30, blank=True, null=True)
    chefia = models.CharField(max_length=150, blank=True, null=True)

    def __str__(self):
        return f"{self.nome} - {self.matricula}"
