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
    warnings = models.BooleanField("Наличие предупреждений", default=False)
    warning_description = models.TextField("Описание предупреждений", null=True, blank=True)

    class Meta:
        verbose_name = "Учебный план"
        verbose_name_plural = "Учебные планы"


class Category(models.Model):
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
    warnings = models.BooleanField("Наличие предупреждений", default=False)
    warning_description = models.TextField("Описание предупреждений", null=True, blank=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"


class StudyCycle(models.Model):
    """
    Дочерний образовательный цикл, привязанный к Category.
    """
    id = models.UUIDField("ID", primary_key=True, default=uuid.uuid4, editable=False)
    identificator = models.CharField("Идентификатор", max_length=50)
    cycles = models.CharField("Название дочернего цикла", max_length=255)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='child_cycles',
        verbose_name="Категория"
    )
    warnings = models.BooleanField("Наличие предупреждений", default=False)
    warning_description = models.TextField("Описание предупреждений", null=True, blank=True)

    class Meta:
        verbose_name = "Учебный цикл"
        verbose_name_plural = "Учебные циклы"


class Module(models.Model):
    """
    План строки, относящийся к дочернему циклу.
    """
    id = models.UUIDField("ID", primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("Дисциплина", max_length=255)
    warnings = models.BooleanField("Наличие предупреждений", default=False)
    warning_description = models.TextField("Описание предупреждений", null=True, blank=True)
    studey_cycle = models.ForeignKey(
        StudyCycle,
        on_delete=models.CASCADE,
        related_name='plan_strings',
        verbose_name="Учебный цикл"
    )


    class Meta:
        verbose_name = "Модуль"
        verbose_name_plural = "Модули"


class Disipline(models.Model):
    """
    Дочерний план строки – вложенная запись внутри родительского плана строки.
    """
    id = models.UUIDField("ID", primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("Дисциплина", max_length=255)
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='child_plan_strings',
        verbose_name="Модуль"
    )

    warnings = models.BooleanField("Наличие предупреждений", default=False)
    warning_description = models.TextField("Описание предупреждений", null=True, blank=True)

    class Meta:
        verbose_name = "Дисциплина"
        verbose_name_plural = "Дисциплины"



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
    warnings = models.BooleanField("Наличие предупреждений", default=False)
    warning_description = models.TextField("Описание предупреждений", null=True, blank=True)
    # Связь с родительским планом строки
    plan_string = models.ForeignKey(
        Disipline,
        on_delete=models.CASCADE,
        related_name='clock_cells',
        null=True,
        blank=True,
        verbose_name="План строки"
    )
    # Связь с дочерним планом строки
    child_plan_string = models.ForeignKey(
        StudyCycle,
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
