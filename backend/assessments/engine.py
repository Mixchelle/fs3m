from decimal import Decimal

REGISTRY = {}  # slug -> callable

def register(slug):
    def deco(fn):
        REGISTRY[slug] = fn
        return fn
    return deco

LABEL_MAP = {
    "Inicial": 1, "Repetido": 2, "Definido": 3, "Gerenciado": 4, "Otimizado": 5
}

def to_decimal(value, label_map=LABEL_MAP):
    if value is None or value == "":
        return Decimal("0")
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))
    v = str(value).strip()
    if v in label_map:
        return Decimal(str(label_map[v]))
    try:
        return Decimal(v)
    except Exception:
        return Decimal("0")

def status_from_goal(media: Decimal, objetivo: Decimal) -> str:
    if media >= objetivo * Decimal("1.2"):
        return "Excelente"
    if media >= objetivo * Decimal("0.9"):
        return "Bom"
    if media >= objetivo * Decimal("0.7"):
        return "Regular"
    if media >= objetivo * Decimal("0.5"):
        return "Atenção"
    return "Crítico"
