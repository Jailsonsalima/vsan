from django.db import models

# Create your models here.
class Veiculo(models.Model):
    modelo = models.CharField(max_length=100)
    placa = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"{self.modelo} - {self.placa}"
