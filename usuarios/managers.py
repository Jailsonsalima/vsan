from django.contrib.auth.base_user import BaseUserManager

class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, username, email=None, password=None, **extra_fields):
        if not email:
            raise ValueError("O email é obrigatório")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        # superusuário não precisa de setor nem tipo_usuario
        extra_fields.setdefault("setor", None)
        extra_fields.setdefault("tipo_usuario", "diretor")

        return self.create_user(username, email, password, **extra_fields)