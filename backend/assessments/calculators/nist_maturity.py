from decimal import Decimal
from collections import defaultdict
from assessments.engine import register, to_decimal, status_from_goal
from frameworks.models import Domain
# ajuste estes imports para seu app real
from responses.models import Answer  # tem que ter answer.question.control.domain etc.

@register("maturity-1-5")
def calculate_nist_maturity(assessment, fw_config):
    """
    fw_config.mapping esperado:
      {
        "score_code": "score",        # Question.local_code com a nota
        "goal": 3.0
      }
    """
    mapping = {"score_code": "score", "goal": 3.0}
    mapping.update(fw_config.mapping or {})
    goal = Decimal(str(mapping["goal"]))
    score_code = mapping["score_code"]

    answers = (
        Answer.objects
        .filter(submission=assessment.submission, question__local_code=score_code)
        .select_related("question__control__domain")
    )

    # agrega por nível
    agg = {
        "FUNCTION": defaultdict(list),  # 'GV' -> [scores]
        "CATEGORY": defaultdict(list),  # 'GV.OC' -> [scores]
        "CONTROL": defaultdict(list),   # 'GV.OC-01' -> [scores]
    }
    names = {"FUNCTION": {}, "CATEGORY": {}, "CONTROL": {}}

    for ans in answers:
        ctl = ans.question.control
        dom = ctl.domain
        func_code = dom.code
        cat_code = ctl.code.split("-")[0]
        ctl_code = ctl.code

        val = to_decimal(ans.value)
        agg["FUNCTION"][func_code].append(val)
        agg["CATEGORY"][cat_code].append(val)
        agg["CONTROL"][ctl_code].append(val)

        names["FUNCTION"][func_code] = dom.title or func_code
        names["CATEGORY"][cat_code] = cat_code
        names["CONTROL"][ctl_code] = ctl.title or ctl_code

    from assessments.models import AssessmentBucket
    AssessmentBucket.objects.filter(assessment=assessment).delete()

    total_vals = []

    def dump(level):
        order = 0
        for code in sorted(agg[level].keys()):
            vals = agg[level][code]
            if not vals:
                continue
            media = sum(vals) / Decimal(len(vals))
            total_vals.extend(vals)
            AssessmentBucket.objects.create(
                assessment=assessment,
                level=level,
                code=code,
                name=names[level].get(code, code),
                order=order,
                metrics={
                    "media": float(media.quantize(Decimal("0.1"))),
                    "objetivo": float(goal),
                    "status": status_from_goal(media, goal),
                },
            )
            order += 1

    dump("FUNCTION")
    dump("CATEGORY")
    dump("CONTROL")

    if total_vals:
        media_total = sum(total_vals) / Decimal(len(total_vals))
        assessment.summary = {
            "media_geral": float(media_total.quantize(Decimal("0.1"))),
            "objetivo": float(goal),
            "status": status_from_goal(media_total, goal),
        }
    else:
        assessment.summary = {"media_geral": 0.0, "objetivo": float(goal), "status": "Não Avaliado"}

    assessment.save()
    return assessment
