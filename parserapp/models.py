import uuid
from django.db import models
from django.core.exceptions import ValidationError

class StudyPlan(models.Model):
    """
    Модель учебного плана, получаемая из элемента «ООП».
    """
    id = models.UUIDField("ID", primary_key=True, default=uuid.uuid4, editable=False)
    specialization_code = models.CharField("Шифр специальности", max_length=50)
    name = models.CharField("Название", max_length=255)
    create_date = models.DateField("Дата документа")
    gos_type = models.CharField("Тип ГОС", max_length=50)

    class Meta:
        verbose_name = "Учебный план"
        verbose_name_plural = "Учебные планы"


class Cycle(models.Model):
    """
    Верхнеуровневый образовательный цикл.
    """
    id = models.UUIDField("ID", primary_key=True, default=uuid.uuid4, editable=False)
    identificator = models.CharField("Идентификатор", max_length=50)
    cycles = models.CharField("Название цикла", max_length=255)
    study_plan = models.ForeignKey(
        StudyPlan,
        on_delete=models.CASCADE,
        related_name='cycles',
        verbose_name="Учебный план"
    )

    class Meta:
        verbose_name = "Цикл"
        verbose_name_plural = "Циклы"


class ChildCycle(models.Model):
    """
    Дочерний образовательный цикл, привязанный к Cycle.
    """
    id = models.UUIDField("ID", primary_key=True, default=uuid.uuid4, editable=False)
    identificator = models.CharField("Идентификатор", max_length=50)
    cycles = models.CharField("Название дочернего цикла", max_length=255)
    parent_cycle = models.ForeignKey(
        Cycle,
        on_delete=models.CASCADE,
        related_name='child_cycles',
        verbose_name="Родительский цикл"
    )

    class Meta:
        verbose_name = "Дочерний цикл"
        verbose_name_plural = "Дочерние циклы"


class PlanString(models.Model):
    """
    План строки, относящийся к дочернему циклу.
    """
    id = models.UUIDField("ID", primary_key=True, default=uuid.uuid4, editable=False)
    discipline = models.CharField("Дисциплина", max_length=255)
    child_cycle = models.ForeignKey(
        ChildCycle,
        on_delete=models.CASCADE,
        related_name='plan_strings',
        verbose_name="Дочерний цикл (блок)"
    )

    class Meta:
        verbose_name = "План строки"
        verbose_name_plural = "Планы строк"


class ChildPlanString(models.Model):
    """
    Дочерний план строки – вложенная запись внутри родительского плана строки.
    """
    id = models.UUIDField("ID", primary_key=True, default=uuid.uuid4, editable=False)
    discipline = models.CharField("Дисциплина", max_length=255)
    parent_plan_string = models.ForeignKey(
        PlanString,
        on_delete=models.CASCADE,
        related_name='child_plan_strings',
        verbose_name="Родительский план строки"
    )

    class Meta:
        verbose_name = "Дочерний план строки"
        verbose_name_plural = "Дочерние планы строк"


class ClockCell(models.Model):
    """
    Ячейка часов, привязанная либо к плану строки, либо к дочернему плану строки.
    """
    id = models.UUIDField("ID", primary_key=True, default=uuid.uuid4, editable=False)
    code_of_type_work = models.IntegerField("Код вида работы", null=True, blank=True)
    code_of_type_hours = models.IntegerField("Код типа часов", null=True, blank=True)
    course = models.IntegerField("Курс", null=True, blank=True)
    semestr = models.IntegerField("Семестр", null=True, blank=True)
    count_of_clocks = models.IntegerField("Количество часов", null=True, blank=True)
    # Связь с родительским планом строки
    plan_string = models.ForeignKey(
        PlanString,
        on_delete=models.CASCADE,
        related_name='clock_cells',
        null=True,
        blank=True,
        verbose_name="План строки"
    )
    # Связь с дочерним планом строки
    child_plan_string = models.ForeignKey(
        ChildPlanString,
        on_delete=models.CASCADE,
        related_name='clock_cells',
        null=True,
        blank=True,
        verbose_name="Дочерний план строки"
    )

    class Meta:
        verbose_name = "Ячейка часов"
        verbose_name_plural = "Ячейки часов"

    def clean(self):
        """
        Гарантирует, что ячейка часов привязана ровно к одному из планов.
        """
        if not (self.plan_string or self.child_plan_string):
            raise ValidationError("Ячейка часов должна быть привязана либо к плану строки, либо к дочернему плану строки.")
        if self.plan_string and self.child_plan_string:
            raise ValidationError("Ячейка часов не может быть привязана одновременно и к плану строки, и к дочернему плану строки.")

