from django.db import models

class StudyPlan(models.Model):
    id = models.CharField(primary_key=True, max_length=255)
    specialization_code = models.CharField(max_length=255, null=True)
    name = models.CharField(max_length=255, null=True)
    create_date = models.DateField(null=True)
    gos_type = models.CharField(max_length=255, null=True)
    warnings = models.BooleanField(default=False)
    warning_description = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.specialization_code})"

class Category(models.Model):
    id = models.CharField(primary_key=True, max_length=255)
    identificator = models.CharField(max_length=255, null=True)
    cycles = models.CharField(max_length=255, null=True)
    study_plan = models.ForeignKey(StudyPlan, related_name='cycles', on_delete=models.CASCADE)
    warnings = models.BooleanField(default=False)
    warning_description = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.cycles} ({self.study_plan.name})"

class StudyCycle(models.Model):
    id = models.CharField(primary_key=True, max_length=255)
    identificator = models.CharField(max_length=255, null=True)
    cycles = models.CharField(max_length=255, null=True)
    category = models.ForeignKey(Category, related_name='child_cycles', on_delete=models.CASCADE)
    warnings = models.BooleanField(default=False)
    warning_description = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.cycles} ({self.category.cycles})"

class Module(models.Model):
    id = models.CharField(primary_key=True, max_length=255)
    name = models.CharField(max_length=255, null=True)
    studey_cycle = models.ForeignKey(StudyCycle, related_name='plan_strings', on_delete=models.CASCADE)
    warnings = models.BooleanField(default=False)
    warning_description = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.studey_cycle.cycles})"

class Disipline(models.Model):
    id = models.CharField(primary_key=True, max_length=255)
    name = models.CharField(max_length=255, null=True)
    module = models.ForeignKey(Module, related_name='child_plan_strings', on_delete=models.CASCADE)
    warnings = models.BooleanField(default=False)
    warning_description = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.module.name})"

class ClockCell(models.Model):
    id = models.CharField(primary_key=True, max_length=255)
    code_of_type_work = models.CharField(max_length=255, null=True)
    code_of_type_hours = models.CharField(max_length=255, null=True)
    course = models.IntegerField(null=True)
    semestr = models.IntegerField(null=True)
    count_of_clocks = models.IntegerField(null=True)
    plan_string = models.ForeignKey(Disipline, related_name='clock_cells', on_delete=models.CASCADE, null=True)
    child_plan_string = models.ForeignKey(StudyCycle, related_name='clock_cells', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"Курс {self.course}, Семестр {self.semestr}, Часы: {self.count_of_clocks}"

class WhitelistWord(models.Model):
    word = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.word
