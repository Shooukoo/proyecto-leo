import os

from django.core.management.base import BaseCommand, CommandError

from auth_api.models import Rol, User

USUARIOS = [
    ("admin@paqueteria.test", Rol.ADMIN_SISTEMA),
    ("gerente@paqueteria.test", Rol.GERENTE),
    ("operador@paqueteria.test", Rol.OPERADOR),
    ("repartidor@paqueteria.test", Rol.REPARTIDOR),
    ("cliente@paqueteria.test", Rol.CLIENTE),
]


class Command(BaseCommand):
    help = "Crea un usuario demo por rol. La contraseña se toma de DEMO_PASSWORD."

    def handle(self, *args, **options):
        password = os.environ.get("DEMO_PASSWORD")
        if not password:
            raise CommandError("Define DEMO_PASSWORD en el entorno.")
        for email, rol in USUARIOS:
            user, creado = User.objects.get_or_create(email=email, defaults={"rol": rol})
            user.rol, user.is_active = rol, True
            user.set_password(password)
            user.save()
            self.stdout.write(f"{'creado' if creado else 'actualizado'}: {email} ({rol})")
