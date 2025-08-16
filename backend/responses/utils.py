# responses/utils.py
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from frameworks.models import FormTemplate
from .models import Submission

DEFAULT_TEMPLATE_SLUG = "nist-csf-2-0"  # ajuste ao seu slug do template NIST

# def get_or_create_client_submission(customer_id: int, template_slug: str | None = None) -> Submission | None:
#     template_slug = template_slug or DEFAULT_TEMPLATE_SLUG
#     try:
#         tpl = FormTemplate.objects.select_related("framework").get(slug=template_slug, active=True)
#     except ObjectDoesNotExist:
#         return None

#     existing = (
#         Submission.objects
#         .filter(customer_id=customer_id, template=tpl)
#         .order_by("-updated_at", "-created_at")
#         .first()
#     )
#     if existing:
#         return existing

#     with transaction.atomic():
#         sub = Submission.objects.create(
#             customer_id=customer_id,
#             template=tpl,
#             framework=tpl.framework,
#             status="draft",
#             version=1,
#         )
#     sub.recalc_progress(commit=True)
#     return sub


# responses/utils.py
def get_or_create_client_submission(customer_id: int, template_slug: str | None = None) -> Submission | None:
    template_slug = template_slug or DEFAULT_TEMPLATE_SLUG
    try:
        tpl = FormTemplate.objects.select_related("framework").get(slug=template_slug, active=True)
    except ObjectDoesNotExist:
        return None

    # 🔁 procura por framework (não por template)
    existing = (
        Submission.objects
        .filter(customer_id=customer_id, framework=tpl.framework)
        .order_by("-updated_at", "-created_at")
        .first()
    )
    if existing:
        return existing

    with transaction.atomic():
        sub = Submission.objects.create(
            customer_id=customer_id,
            template=tpl,
            framework=tpl.framework,
            status="draft",
            version=1,
        )
    sub.recalc_progress(commit=True)
    return sub
