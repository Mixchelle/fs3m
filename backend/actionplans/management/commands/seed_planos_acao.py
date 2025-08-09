# backend/actionplans/management/commands/seed_planos_acao.py
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from collections import defaultdict
from statistics import mean

from users.models import CustomUser
from recommendations.models import Recomendacao
from actionplans.models import PlanoDeAcao, PlanoDeAcaoRecomendacao


PRIO_ORDER = {"alta": 0, "media": 1, "baixa": 2}


def _get_analista_padrao():
    # tenta por role
    analista = CustomUser.objects.filter(role="analista").order_by("id").first()
    if analista:
        return analista
    # fallback: admin
    admin = CustomUser.objects.filter(is_superuser=True).order_by("id").first()
    if admin:
        return admin
    # último fallback: primeiro usuário
    return CustomUser.objects.order_by("id").first()


class Command(BaseCommand):
    help = "Gera Planos de Ação a partir das recomendações existentes (1 plano por cliente+submission)."

    def add_arguments(self, parser):
        parser.add_argument("--cliente-id", type=int, help="Filtra por cliente.")
        parser.add_argument("--submission-id", type=int, help="Filtra por submission.")
        parser.add_argument(
            "--forcar",
            action="store_true",
            help="Apaga plano existente do par (cliente, submission) e recria.",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        cliente_id = opts.get("cliente_id")
        submission_id = opts.get("submission_id")
        forcar = bool(opts.get("forcar"))

        # agrupa recomendações por (cliente, submission)
        qs = Recomendacao.objects.select_related("cliente", "submission")
        if cliente_id:
            qs = qs.filter(cliente_id=cliente_id)
        if submission_id:
            qs = qs.filter(submission_id=submission_id)

        grupos = defaultdict(list)
        for rec in qs:
            if rec.submission_id and rec.cliente_id:
                grupos[(rec.cliente_id, rec.submission_id)].append(rec)

        if not grupos:
            self.stdout.write("Nenhuma recomendação encontrada para gerar planos.")
            return

        analista_padrao = _get_analista_padrao()
        if not analista_padrao:
            self.stdout.write(self.style.ERROR("Nenhum usuário encontrado para atribuir como 'criado_por'."))
            return

        criados, atualizados = 0, 0

        for (cli_id, sub_id), recs in grupos.items():
            # apaga/recria se --forcar
            if forcar:
                PlanoDeAcao.objects.filter(cliente_id=cli_id, submission_id=sub_id).delete()

            plano, created = PlanoDeAcao.objects.get_or_create(
                cliente_id=cli_id,
                submission_id=sub_id,
                defaults={
                    "criado_por": analista_padrao,
                    "observacoes": "Plano gerado automaticamente a partir de recomendações.",
                },
            )

            if created:
                criados += 1
            else:
                atualizados += 1

            # limpa vínculos antigos se não forçar criação nova
            PlanoDeAcaoRecomendacao.objects.filter(plano=plano).delete()

            # ordenar recomendações: prioridade (alta>media>baixa), depois data_fim, depois id
            def _key(r: Recomendacao):
                return (
                    PRIO_ORDER.get(r.prioridade, 9),
                    r.data_fim or r.data_inicio or timezone.now().date(),
                    r.id,
                )

            recs_sorted = sorted(recs, key=_key)

            # criar vínculos ordenados
            for idx, rec in enumerate(recs_sorted):
                PlanoDeAcaoRecomendacao.objects.create(
                    plano=plano,
                    recomendacao=rec,
                    ordem=idx,
                    status="A Fazer",
                    data_alteracao=timezone.now(),
                )

            # preencher campos agregados do plano
            try:
                meses_max = max([r.meses for r in recs if r.meses])
            except ValueError:
                meses_max = None

            plano.prazo = f"{meses_max} meses" if meses_max else ""
            # médias simples de gravidade/urgência (guardadas como strings '1'..'5')
            urg_values = [int(r.urgencia) for r in recs if str(r.urgencia).isdigit()]
            grav_values = [int(r.gravidade) for r in recs if str(r.gravidade).isdigit()]
            plano.urgencia = f"{round(mean(urg_values), 1)}" if urg_values else ""
            plano.gravidade = f"{round(mean(grav_values), 1)}" if grav_values else ""
            # categoria opcional: pode deixar vazio ou concatenar principais
            plano.categoria = ""  # ou: ", ".join(sorted({r.categoria for r in recs if r.categoria}))[:255]
            plano.orcamentoMax = ""  # sem cálculo aqui
            plano.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f"Plano #{plano.id} para cliente={cli_id} submission={sub_id}: {len(recs_sorted)} recomendações."
                )
            )

        self.stdout.write(self.style.SUCCESS(f"Planos criados: {criados}, atualizados: {atualizados}."))
