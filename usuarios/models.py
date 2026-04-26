from django.db import models
from setores.models import Setor
from django.contrib.auth.models import AbstractUser
from .managers import UsuarioManager
from servidores.models import Servidor

# Create your models here.

class Usuario(AbstractUser):
    TIPO_USUARIO_CHOICES = [
        ('diretor', 'Diretor'),
        ('coordenador', 'Coordenador'),
        ('funcionario', 'Funcionário'),
    ]
    setor = models.ForeignKey(Setor, on_delete=models.SET_NULL, null=True, blank=True, related_name="usuarios")
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_USUARIO_CHOICES, verbose_name='Tipo de Usuário', null=True, blank=True)

    # Matrícula informada no cadastro de usuário
    matricula = models.CharField(max_length=20, unique=True, null=True, blank=True)

    # Relacionamento 1-1 com Servidor (se o objeto pai for excluído, o filho também será excluído automaticamente)
    servidor = models.OneToOneField(Servidor, on_delete=models.CASCADE, null=True, blank=True, related_name="usuario")

    objects = UsuarioManager()

    def save(self, *args, **kwargs):
        # Se não tiver tipo de usuário, a conta fica inativa
        if not self.tipo_usuario:
            self.is_active = False
        else:
            self.is_active = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} - {self.tipo_usuario if self.tipo_usuario else 'Inativo'}"
