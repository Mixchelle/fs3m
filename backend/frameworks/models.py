from django.db import models
from django.utils.text import slugify


class Framework(models.Model):
    """
    Catalog entry for a security framework (e.g., NIST CSF 2.0, CIS Controls v8, ISO 27001:2022).
    Holds taxonomy only (no answers here).
    """
    slug = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=32, default="1.0")
    description = models.TextField(blank=True, default="")
    active = models.BooleanField(default=True)
    editable = models.BooleanField(
        default=False,
        help_text="If true, allow editing this framework (controls/questions) via UI."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("slug", "version")]
        ordering = ["slug", "version"]

    def __str__(self):
        return f"{self.name} v{self.version}"


class Domain(models.Model):
    """
    Hierarchical bucket under a framework. For NIST CSF: GV/ID/PR/DE/RS/RC.
    Parent is optional to support multi-level taxonomies.
    """
    framework = models.ForeignKey(Framework, on_delete=models.CASCADE, related_name="domains")
    code = models.CharField(max_length=50, blank=True, default="")  # e.g.: "GV", "ID"
    title = models.CharField(max_length=255)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["framework", "parent__id", "order", "id"]
        unique_together = [("framework", "code")]

    def __str__(self):
        return f"{self.framework.slug}:{self.code or self.title}"


class ScoringModel(models.Model):
    """
    Reusable scoring/maturity map, e.g. {"Initial": 1, "Repeatable": 2, "Defined": 3, "Managed": 4, "Optimized": 5}
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    # label -> numeric value
    mapping = models.JSONField(default=dict)
    # optional extra rules/explanations
    rules = models.JSONField(default=dict, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Control(models.Model):
    """
    Control/practice/requirement inside a domain (e.g., 'GV.OC-01').
    Questions are attached to a control.
    """
    framework = models.ForeignKey(Framework, on_delete=models.CASCADE, related_name="controls")
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name="controls")
    code = models.CharField(max_length=50)  # e.g.: "GV.OC-01"
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    scoring_model = models.ForeignKey(
        ScoringModel, null=True, blank=True, on_delete=models.SET_NULL, related_name="controls"
    )

    class Meta:
        ordering = ["framework", "domain", "order", "code"]
        unique_together = [("framework", "code")]

    def __str__(self):
        return f"{self.framework.slug}:{self.code} - {self.title}"


class Question(models.Model):
    """
    A question that belongs to a control. (Structure only — answers live in another app.)
    """
    TYPE = [
        ("text", "Text"),
        ("number", "Number"),
        ("boolean", "Yes/No"),
        ("single", "Single choice"),
        ("multiple", "Multiple choice"),
        ("scale", "Scale"),
        ("json", "JSON blob"),
        ("file", "File placeholder (store metadata elsewhere)"),
    ]

    control = models.ForeignKey(Control, on_delete=models.CASCADE, related_name="questions")
    local_code = models.CharField(max_length=50, blank=True, default="")
    prompt = models.CharField(max_length=500)
    type = models.CharField(max_length=20, choices=TYPE, default="text")
    required = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    # Non-sensitive metadata (UI hints, scale min/max, visibility rules, etc.)
    meta = models.JSONField(default=dict, blank=True)

    # If not set, inherit from control (optional behavior you can implement in services)
    scoring_model = models.ForeignKey(
        ScoringModel, null=True, blank=True, on_delete=models.SET_NULL, related_name="questions"
    )

    class Meta:
        ordering = ["control", "order", "id"]

    def __str__(self):
        base = f"{self.control.code}"
        if self.local_code:
            base += f".{self.local_code}"
        return f"{base} - {self.prompt[:60]}"


class ChoiceOption(models.Model):
    """
    Options for single/multiple/scale questions.
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    label = models.CharField(max_length=200)
    value = models.CharField(max_length=100)  # symbolic key you will store in answers app
    weight = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )
    order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["question", "order", "id"]

    def __str__(self):
        return f"{self.question_id} - {self.label}"


class FormTemplate(models.Model):
    """
    A publishable template: selects a subset of controls (and optionally specific questions),
    defines ordering and version. Tied to a single framework for simplicity.
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=128, unique=True)
    framework = models.ForeignKey(Framework, on_delete=models.PROTECT, related_name="templates")
    version = models.CharField(max_length=20, default="1.0")
    description = models.TextField(blank=True, default="")
    active = models.BooleanField(default=True)
    editable = models.BooleanField(default=True)

    controls = models.ManyToManyField(
        Control, through="TemplateItem", related_name="templates", blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("slug", "version")]
        ordering = ["name", "version"]

    def __str__(self):
        return f"{self.name} v{self.version}"


class TemplateItem(models.Model):
    """
    Links a control (and optionally a specific question) to a template, with ordering.
    If 'question' is null, the template includes ALL questions of that control.
    """
    template = models.ForeignKey(FormTemplate, on_delete=models.CASCADE, related_name="items")
    control = models.ForeignKey(Control, on_delete=models.CASCADE, related_name="template_items")
    question = models.ForeignKey(
        Question, null=True, blank=True, on_delete=models.CASCADE, related_name="template_items"
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["template", "order", "id"]
        unique_together = [("template", "control", "question")]

    def __str__(self):
        ref = self.question_id or self.control_id
        return f"{self.template.slug} -> {ref}"


class ControlMapping(models.Model):
    """
    Cross-framework mapping: map a control to another control (e.g., NIST GV.OC-01 -> CIS 01.x).
    """
    origin = models.ForeignKey(Control, on_delete=models.CASCADE, related_name="mappings_origin")
    target = models.ForeignKey(Control, on_delete=models.CASCADE, related_name="mappings_target")
    weight = models.DecimalField(max_digits=6, decimal_places=2, default=1.0)
    note = models.TextField(blank=True, default="")

    class Meta:
        unique_together = [("origin", "target")]
        indexes = [
            models.Index(fields=["origin"]),
            models.Index(fields=["target"]),
        ]

    def __str__(self):
        return f"{self.origin} -> {self.target} ({self.weight})"
