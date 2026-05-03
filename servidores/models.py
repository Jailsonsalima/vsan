from django.db import models
from setores.models import Setor

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
    cargo = models.CharField(max_length=100)
    funcao = models.CharField(max_length=150, blank=True, null=True)
    cpf = models.CharField(max_length=14, unique=True)
    rg = models.CharField(max_length=20, blank=True, null=True)
    nascimento = models.DateField(blank=True, null=True)
    banco = models.CharField(max_length=50, blank=True, null=True)
    agencia = models.CharField(max_length=20, blank=True, null=True)
    conta = models.CharField(max_length=30, blank=True, null=True)
    # Relacionamento com Setor
    setor = models.ForeignKey(Setor, on_delete=models.SET_NULL, null=True, blank=True)
    chefe_imediato = models.ForeignKey(Setor, on_delete=models.SET_NULL, null=True, blank=True, related_name="servidores_chefiados")
    # Novo campo para disponibilidade
    disponivel = models.BooleanField(default=True)
    ultima_vez_sorteado = models.DateTimeField(null=True, blank=True)

    def primeiro_nome(self):
        return self.nome.split()[0]
    
    def primeiro_e_ultimo_nome(self):
        partes = self.nome.strip().split()
        if len(partes) >= 2:
            return f"{partes[0]}_{partes[-1]}"  # usa underline para evitar espaços em nomes de arquivos
        return self.nome  # se só tiver um nome, retorna ele mesmo

    def __str__(self):
        return f"{self.nome}"
