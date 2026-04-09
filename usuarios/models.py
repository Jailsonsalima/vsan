from django.db import models
from setores.models import Setor
from django.contrib.auth.models import AbstractUser
from .managers import UsuarioManager

# Create your models here.

class Usuario(AbstractUser):
    TIPO_USUARIO_CHOICES = [
        ('diretor', 'Diretor'),
        ('coordenador', 'Coordenador'),
        ('funcionario', 'Funcionário'),
    ]
    setor = models.ForeignKey(Setor, on_delete=models.CASCADE, verbose_name='Setor', null=True, blank=True)
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_USUARIO_CHOICES, verbose_name='Tipo de Usuário', null=True, blank=True)

    objects = UsuarioManager()

    def save(self, *args, **kwargs):
        # Se não tiver tipo de usuário, a conta fica inativa
        if not self.tipo_usuario:
            self.is_active = False
        else:
            self.is_active = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} - {self.setor.nome if self.setor else 'Sem setor'} - {self.tipo_usuario if self.tipo_usuario else 'Inativo'}"
