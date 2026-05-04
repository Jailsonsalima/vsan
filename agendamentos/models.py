from django.db import models

# Create your models here.

from django.contrib.auth import get_user_model
from servidores.models import Servidor
from setores.models import Setor

Usuario = get_user_model()

class Agendamento(models.Model):
    data_ida = models.DateField()
    data_retorno = models.DateField()
    municipio = models.CharField(max_length=100)
    servidor = models.ForeignKey(Servidor, on_delete=models.CASCADE)  # servidor vinculado ao usuário solicitante
    solicitante = models.ForeignKey(Usuario, on_delete=models.CASCADE)  # usuário que solicitou
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    motivo = models.TextField()
    processado = models.BooleanField(default=False)

    def __str__(self):
        return f"Agendamento {self.id} - {self.servidor.nome} ({self.municipio})"


class MotoristaExterno(models.Model):
    nome = models.CharField(max_length=200)
    cpf = models.CharField(max_length=14)
    rg = models.CharField(max_length=20)
    nascimento = models.DateField()
    endereco = models.CharField(max_length=255)
    vinculo = models.CharField(max_length=50)
    matricula = models.CharField(max_length=20)
    setor = models.ForeignKey(Setor, on_delete=models.SET_NULL, null=True, blank=True)
    chefe_imediato = models.ForeignKey(Setor, on_delete=models.SET_NULL, null=True, blank=True, related_name="motoristas_externos_chefiados")
    cargo = models.CharField(max_length=100)
    funcao = models.CharField(max_length=150, blank=True, null=True)
    banco = models.CharField(max_length=50, blank=True, null=True)
    agencia = models.CharField(max_length=20, blank=True, null=True)
    conta = models.CharField(max_length=30, blank=True, null=True)
    # Novo campo para controle de disponibilidade
    disponivel = models.BooleanField(default=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.nome
    
    def primeiro_nome(self):
        return self.nome.split()[0]
    
    def primeiro_e_ultimo_nome(self):
        partes = self.nome.strip().split()
        if len(partes) >= 2:
            return f"{partes[0]}_{partes[-1]}"  # usa underline para evitar espaços em nomes de arquivos
        return self.nome  # se só tiver um nome, retorna ele mesmo
  


class AutorizacaoAgendamento(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    pode_visualizar = models.BooleanField(default=False)
    pode_processar = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.usuario.username} - Visualizar: {self.pode_visualizar}, Processar: {self.pode_processar}"

class ProcessamentoAgendamento(models.Model):
    agendamento = models.OneToOneField(Agendamento, on_delete=models.CASCADE, related_name="processamento")
    tipo = models.CharField(max_length=20, choices=[('Da Vigilância','Da Vigilância'),('outros','Outros')])
    motorista_servidor = models.ForeignKey('servidores.Servidor', on_delete=models.SET_NULL, null=True, blank=True)
    motorista_externo = models.ForeignKey(MotoristaExterno, on_delete=models.SET_NULL, null=True, blank=True)
    data_processamento = models.DateTimeField(auto_now_add=True)
    numero_processo = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Processamento {self.agendamento}"
