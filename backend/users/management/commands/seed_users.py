from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Cria usuários de demonstração (3 clientes + 1 analista)."

    @transaction.atomic
    def handle(self, *args, **options):
        created = []

        # Analista (pode revisar submissions)
        analista, a_created = User.objects.get_or_create(
            email="analista@fs3m.com",
            defaults={
                "nome": "Analista FS3M",
                "role": "analista",
                "is_staff": True,
                "is_active": True,
            },
        )
        if a_created:
            analista.set_password("fs3m@analista")
            analista.save()
        created.append(("analista", analista.email, a_created))

        # 3 clientes
        clientes_seed = [
            ("ACME Segurança", "cliente1@empresa.com"),
            ("Stark Tech", "cliente2@empresa.com"),
            ("Wayne Industries", "cliente3@empresa.com"),
        ]
        clientes_objs = []
        for nome, email in clientes_seed:
            user, u_created = User.objects.get_or_create(
                email=email,
                defaults={
                    "nome": nome,
                    "role": "cliente",
                    "is_active": True,
                },
            )
            if u_created:
                user.set_password("fs3m@cliente")
                user.save()
            clientes_objs.append(user)
            created.append(("cliente", email, u_created))

        # Um subcliente vinculado ao primeiro cliente (exemplo)
        sub, s_created = User.objects.get_or_create(
            email="sub@empresa.com",
            defaults={
                "nome": "Filial ACME",
                "role": "subcliente",
                "cliente": clientes_objs[0],
                "is_active": True,
            },
        )
        if s_created:
            sub.set_password("fs3m@sub")
            sub.save()
        created.append(("subcliente", sub.email, s_created))

        # Imprime resumo
        for role, email, was_created in created:
            status = "CRIADO" if was_created else "EXISTENTE"
            self.stdout.write(self.style.SUCCESS(f"[{status}] {role}: {email}"))

        self.stdout.write(self.style.SUCCESS("OK! Usuários de demonstração prontos."))
