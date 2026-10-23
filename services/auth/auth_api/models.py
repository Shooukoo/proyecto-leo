from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class Rol(models.TextChoices):
    CLIENTE = "cliente", "Cliente"
    REPARTIDOR = "repartidor", "Repartidor"
    OPERADOR = "operador", "Operador / Despachador"
    GERENTE = "gerente", "Gerente"
    ADMIN_SISTEMA = "admin_sistema", "Administrador del sistema"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create(self, email, password, **extra):
        if not email:
            raise ValueError("El correo es obligatorio.")
        user = self.model(email=self.normalize_email(email), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("rol", Rol.CLIENTE)
        return self._create(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.update(rol=Rol.ADMIN_SISTEMA, is_staff=True, is_superuser=True)
        return self._create(email, password, **extra)


class User(AbstractUser):
    """Usuario con inicio de sesión por correo y un rol del dominio."""

    username = None
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    rol = models.CharField(max_length=15, choices=Rol, default=Rol.CLIENTE)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.email} ({self.rol})"
