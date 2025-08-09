from decimal import Decimal
from collections import defaultdict
import json

from assessments.engine import register, to_decimal, status_from_goal
from responses.models import Answer


def _extract_numeric(ans):
    # 1) tenta ans.score
    if hasattr(ans, "score") and ans.score is not None:
        try:
            return Decimal(str(ans.score))
        except Exception:
            pass

    # 2) Answer.value pode ser número, dict {"value":n} ou string/JSON
    v = getattr(ans, "value", None)
    if isinstance(v, (int, float, Decimal)):
        return Decimal(str(v))

    if isinstance(v, dict):
        inner = v.get("value", None)
        if inner is not None:
            return to_decimal(inner)

    if isinstance(v, str):
        s = v.strip()
        if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
            try:
                data = json.loads(s)
                if isinstance(data, dict) and "value" in data:
                    return to_decimal(data["value"])
            except Exception:
                pass
        return to_decimal(s)

    return Decimal("0")


@register("maturity-1-5")
def calculate_nist_maturity(assessment, fw_config):
    """
    fw_config.mapping esperado:
    {
      "goal": 3.0,
      "score_code": "score",
      "use_policy_practice": true,   # se quiser média separada de política/prática
      "policy_code": "politica",
      "practice_code": "pratica",
      "info_code": "info",           # opcional (default)
      "attachment_code": "attachment" # opcional (default)
    }
    """
    mapping = {
        "goal": 3.0,
        "score_code": "score",
        "use_policy_practice": False,
        "policy_code": "politica",
        "practice_code": "pratica",
        "info_code": "info",
        "attachment_code": "attachment",
    }
    mapping.update(getattr(fw_config, "mapping", {}) or {})

    goal = Decimal(str(mapping["goal"]))
    use_pp = bool(mapping.get("use_policy_practice"))

    # carrega respostas
    answers = (
        Answer.objects
        .filter(submission=assessment.submission)
        .select_related("question__control__domain")
    )

    # estruturas
    controls = {}                 # ctl_code -> info e valores
    names_function = {}           # "GV" -> "Governança (GV)" (se vier do domínio)
    cat_to_func = {}              # "GV.RM" -> "GV"

    # extras por controle
    control_notes = defaultdict(list)       # ctl_code -> [str]
    control_attachments = defaultdict(list) # ctl_code -> [ {name, url, description} ]

    def ensure_ctl(ctl, dom):
        code = ctl.code                       # ex: "GV.RM-02"
        if code not in controls:
            cat_code = code.split("-")[0]     # ex: "GV.RM"
            func_code = cat_code.split(".")[0]  # ex: "GV"
            if getattr(dom, "title", None):
                names_function[func_code] = dom.title
            cat_to_func[cat_code] = func_code
            controls[code] = {
                "func": func_code,
                "cat": cat_code,
                "title": ctl.title or code,
                "name": code,
                "policy_vals": [],
                "practice_vals": [],
                "score_vals": [],
            }
        return controls[code]

    info_code = (mapping.get("info_code") or "info").strip()
    att_code  = (mapping.get("attachment_code") or "attachment").strip()
    policy_lc = (mapping.get("policy_code") or "politica").strip()
    pract_lc  = (mapping.get("practice_code") or "pratica").strip()
    score_lc  = (mapping.get("score_code") or "score").strip()

    for ans in answers:
        q = getattr(ans, "question", None)
        ctl = getattr(q, "control", None)
        dom = getattr(ctl, "domain", None)
        if not q or not ctl or not dom:
            continue

        local = (q.local_code or "").strip()
        rec = ensure_ctl(ctl, dom)

        # coleta valores de política/prática/score
        if use_pp:
            if local == policy_lc:
                rec["policy_vals"].append(_extract_numeric(ans))
            elif local == pract_lc:
                rec["practice_vals"].append(_extract_numeric(ans))
            elif local == score_lc:
                rec["score_vals"].append(_extract_numeric(ans))
        else:
            if local == score_lc:
                rec["score_vals"].append(_extract_numeric(ans))

        # coleta NOTES (info + evidence)
        ev = getattr(ans, "evidence", None)
        if ev:
            s = str(ev).strip()
            if s:
                control_notes[ctl.code].append(s)

        if local == info_code:
            v = getattr(ans, "value", None)
            if isinstance(v, dict):
                txt = v.get("value")
            else:
                txt = v
            if txt is not None:
                txt_s = str(txt).strip()
                if txt_s:
                    control_notes[ctl.code].append(txt_s)

        # coleta ATTACHMENTS (payload simples/variável)
        if local == att_code:
            v = getattr(ans, "value", None)
            payload = {}
            if isinstance(v, dict):
                # tenta achar campos comuns
                payload = {
                    "name": v.get("name") or v.get("filename") or None,
                    "url": v.get("url") or v.get("file") or None,
                    "description": v.get("description") or v.get("desc") or None,
                }
                # se vier apenas {"type":"file","value":...}
                inner = v.get("value")
                if inner and not payload.get("url"):
                    payload["url"] = inner if isinstance(inner, str) else None
            elif isinstance(v, str):
                payload = {"name": None, "url": v, "description": None}
            else:
                payload = {"name": None, "url": None, "description": None}
            control_attachments[ctl.code].append(payload)

    # agregadores
    agg_function           = defaultdict(list)   # "GV" -> [médias de controles]
    agg_category           = defaultdict(list)   # "GV.RM" -> [médias de controles]
    agg_function_policy    = defaultdict(list)   # médias só de política
    agg_function_practice  = defaultdict(list)   # médias só de prática
    agg_category_policy    = defaultdict(list)
    agg_category_practice  = defaultdict(list)

    category_items         = defaultdict(list)   # "GV.RM" -> [dicts de controles] (para exibir)
    category_metrics_cache = {}                  # "GV.RM" -> metrics dict completo

    from assessments.models import AssessmentBucket
    AssessmentBucket.objects.filter(assessment=assessment).delete()

    total_vals_for_summary = []

    def avg(vals):
        return (sum(vals) / Decimal(len(vals))) if vals else None

    # ---------- CONTROLS ----------
    order = 0
    for ctl_code in sorted(controls.keys()):
        rec = controls[ctl_code]
        mp = avg(rec["policy_vals"])
        mr = avg(rec["practice_vals"])
        ms = avg(rec["score_vals"])

        # regra de média do controle
        if use_pp and (mp is not None or mr is not None):
            if mp is not None and mr is not None:
                m = (mp + mr) / Decimal("2")
            else:
                m = mp if mp is not None else mr
        else:
            m = ms or Decimal("0")

        # agrega
        agg_category[rec["cat"]].append(m)
        agg_function[rec["func"]].append(m)
        total_vals_for_summary.append(m)
        if use_pp:
            if mp is not None:
                agg_category_policy[rec["cat"]].append(mp)
                agg_function_policy[rec["func"]].append(mp)
            if mr is not None:
                agg_category_practice[rec["cat"]].append(mr)
                agg_function_practice[rec["func"]].append(mr)

        # metrics do controle (bucket CONTROL)
        metrics = {
            "media": float((m or Decimal("0")).quantize(Decimal("0.1"))),
            "objetivo": float(goal),
            "status": status_from_goal(m or Decimal("0"), goal),
            "title": rec["title"],
        }
        if use_pp:
            metrics["politica"] = None if mp is None else float(mp.quantize(Decimal("0.1")))
            metrics["pratica"]  = None if mr is None else float(mr.quantize(Decimal("0.1")))

        AssessmentBucket.objects.create(
            assessment=assessment,
            level="CONTROL",
            code=ctl_code,
            name=rec["name"],
            order=order,
            metrics=metrics,
        )
        order += 1

        # item da lista da categoria (com notas e anexos)
        item = {
            "level": "CONTROL",
            "code": ctl_code,
            "title": rec["title"],
            "media": metrics["media"],
            "status": metrics["status"],
            "objetivo": metrics["objetivo"],
            "notes": control_notes.get(ctl_code, []),
            "attachments": control_attachments.get(ctl_code, []),
        }
        if use_pp:
            item["politica"] = metrics.get("politica")
            item["pratica"]  = metrics.get("pratica")

        category_items[rec["cat"]].append(item)

    # ---------- CATEGORY ----------
    order = 0
    for cat_code in sorted(agg_category.keys()):
        vals = agg_category[cat_code]
        m = sum(vals) / Decimal(len(vals)) if vals else Decimal("0")

        metrics = {
            "media": float(m.quantize(Decimal("0.1"))),
            "objetivo": float(goal),
            "status": status_from_goal(m, goal),
            "items": category_items.get(cat_code, []),
        }
        if use_pp:
            mp_list = agg_category_policy.get(cat_code, [])
            mr_list = agg_category_practice.get(cat_code, [])
            if mp_list:
                mp_cat = sum(mp_list) / Decimal(len(mp_list))
                metrics["media_politica"] = float(mp_cat.quantize(Decimal("0.1")))
            if mr_list:
                mr_cat = sum(mr_list) / Decimal(len(mr_list))
                metrics["media_pratica"] = float(mr_cat.quantize(Decimal("0.1")))

        # cache para usar dentro da FUNÇÃO
        category_metrics_cache[cat_code] = metrics

        AssessmentBucket.objects.create(
            assessment=assessment,
            level="CATEGORY",
            code=cat_code,
            name=cat_code,
            order=order,
            metrics=metrics,
        )
        order += 1

    # ---------- FUNCTION (com CATEGORIAS dentro) ----------
    function_items = defaultdict(list)  # "GV" -> [ {code:"GV.RM", metrics...} ]

    for cat_code, metrics in category_metrics_cache.items():
        func_code = cat_to_func.get(cat_code) or cat_code.split(".")[0]
        cat_item = {
            "level": "CATEGORY",
            "code": cat_code,
            "media": metrics.get("media"),
            "status": metrics.get("status"),
            "objetivo": metrics.get("objetivo"),
            "items": metrics.get("items", []),
        }
        if use_pp:
            if "media_politica" in metrics:
                cat_item["media_politica"] = metrics["media_politica"]
            if "media_pratica" in metrics:
                cat_item["media_pratica"] = metrics["media_pratica"]
        function_items[func_code].append(cat_item)

    order = 0
    for func_code in sorted(agg_function.keys()):
        vals = agg_function[func_code]
        m = sum(vals) / Decimal(len(vals)) if vals else Decimal("0")

        metrics = {
            "media": float(m.quantize(Decimal("0.1"))),
            "objetivo": float(goal),
            "status": status_from_goal(m, goal),
            "items": function_items.get(func_code, []),
        }
        if use_pp:
            mp_list = agg_function_policy.get(func_code, [])
            mr_list = agg_function_practice.get(func_code, [])
            if mp_list:
                mp_fun = sum(mp_list) / Decimal(len(mp_list))
                metrics["media_politica"] = float(mp_fun.quantize(Decimal("0.1")))
            if mr_list:
                mr_fun = sum(mr_list) / Decimal(len(mr_list))
                metrics["media_pratica"] = float(mr_fun.quantize(Decimal("0.1")))

        AssessmentBucket.objects.create(
            assessment=assessment,
            level="FUNCTION",
            code=func_code,
            name=names_function.get(func_code, func_code),
            order=order,
            metrics=metrics,
        )
        order += 1

    # ---------- SUMMARY ----------
    if total_vals_for_summary:
        m_total = sum(total_vals_for_summary) / Decimal(len(total_vals_for_summary))
        assessment.summary = {
            "media_geral": float(m_total.quantize(Decimal("0.1"))),
            "objetivo": float(goal),
            "status": status_from_goal(m_total, goal),
        }
    else:
        assessment.summary = {"media_geral": 0.0, "objetivo": float(goal), "status": "Não Avaliado"}

    assessment.save()
    return assessment
