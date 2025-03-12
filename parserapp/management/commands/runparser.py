import json

from django.core.management.base import BaseCommand
from parserapp.parser import get_plan_rup, load_json_to_models, models_to_json
from parserapp.models import StudyPlan, Category, StudyCycle, Module, Disipline, ClockCell, WhitelistWord


class Command(BaseCommand):
    help = "Парсит XML, загружает данные в БД, экспортирует в JSON и выводит данные"

    def add_arguments(self, parser):
        parser.add_argument(
            '--add_to_whitelist',
            nargs='+',
            type=str,
            help='Добавить слова в вайтлист',
        )

    def handle(self, *args, **kwargs):
        add_to_whitelist = kwargs['add_to_whitelist']
        if add_to_whitelist:
            for word in add_to_whitelist:
                WhitelistWord.objects.get_or_create(word=word.lower())
            self.stdout.write(self.style.SUCCESS(f"Слова '{', '.join(add_to_whitelist)}' добавлены в вайтлист"))
            return

        self.stdout.write(self.style.WARNING("Запуск парсера..."))

        # # 1. Загрузка данных из plan.json
        # with open("plan.json", "r", encoding="utf-8") as file:
        #     plan_data = json.load(file)
        # self.stdout.write(self.style.SUCCESS("Данные успешно загружены из plan.json"))

        plan_data = get_plan_rup()
        self.stdout.write(self.style.SUCCESS("XML успешно спарсен и сохранён в plan.json"))


        # 2. Загрузка JSON-данных в БД
        load_json_to_models(plan_data)
        self.stdout.write(self.style.SUCCESS("Данные успешно загружены в базу"))

        # 3. Вывод содержимого моделей в консоль (с информацией о предупреждениях)
        self.print_model_data()

        self.stdout.write(self.style.SUCCESS("Парсер успешно завершил работу!"))

    def print_model_data(self):
        """Выводит содержимое моделей, включая информацию о предупреждениях."""
        print("\n=== Учебные планы ===")
        for sp in StudyPlan.objects.all():
            print(
                f"{sp.id} | {sp.name} (Спец.: {sp.specialization_code}, ГОС: {sp.gos_type}, Дата: {sp.create_date}) | Warnings: {sp.warnings} | Description: {sp.warning_description or 'Нет'}")
            for category in sp.cycles.all():
                print(
                    f"   └─ Категория: {category.id} | {category.identificator}: {category.cycles} | Warnings: {category.warnings} | Description: {category.warning_description or 'Нет'}")
                for study_cycle in category.child_cycles.all():
                    print(
                        f"       └─ Учебный цикл: {study_cycle.id} | {study_cycle.identificator}: {study_cycle.cycles} | Warnings: {study_cycle.warnings} | Description: {study_cycle.warning_description or 'Нет'}")
                    for module in study_cycle.plan_strings.all():
                        print(
                            f"           └─ Модуль: {module.id} | Дисциплина: {module.name} | Warnings: {module.warnings} | Description: {module.warning_description or 'Нет'}")
                        for disipline in module.child_plan_strings.all():
                            print(
                                f"               └─ Дисциплина: {disipline.id} | {disipline.name} | Warnings: {disipline.warnings} | Description: {disipline.warning_description or 'Нет'}")
                            clock_cells = disipline.clock_cells.all()
                            if clock_cells:
                                print("                   └─ Ячейки часов (привязанные к дисциплине):")
                                for clock in clock_cells:
                                    print(
                                        f"                      ⏱ {clock.id} | Курс {clock.course}, Семестр {clock.semestr}, Часы: {clock.count_of_clocks}")
                    clock_cells = study_cycle.clock_cells.all()
                    if clock_cells:
                        print("           └─ Ячейки часов (привязанные к учебному циклу):")
                        for clock in clock_cells:
                            print(
                                f"               ⏱ {clock.id} | Курс {clock.course}, Семестр {clock.semestr}, Часы: {clock.count_of_clocks}")
