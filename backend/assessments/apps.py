from django.apps import AppConfig
import importlib, pkgutil

class AssessmentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "assessments"

    def ready(self):
        # Auto-discover calculators in assessments/calculators/*.py
        try:
            package = importlib.import_module("assessments.calculators")
            for _, modname, ispkg in pkgutil.iter_modules(package.__path__):
                if not ispkg:
                    importlib.import_module(f"assessments.calculators.{modname}")
        except Exception as e:
            # opcional: logar isso
            print(f"[assessments] calculators autoload error: {e}")
