from django.core.management.base import BaseCommand
from parserapp.parser import get_plan_rup, load_json_to_models, models_to_json
from parserapp.models import StudyPlan, Category, StudyCycle, Module, Disipline, ClockCell


class Command(BaseCommand):
    help = "Парсит XML, загружает данные в БД, экспортирует в JSON и выводит данные"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Запуск парсера..."))

        # 1. Парсинг XML и сохранение в plan.json
        plan_data = get_plan_rup()
        self.stdout.write(self.style.SUCCESS("XML успешно спарсен и сохранён в plan.json"))

        # 2. Загрузка JSON-данных в БД
        load_json_to_models(plan_data)
        self.stdout.write(self.style.SUCCESS("Данные успешно загружены в базу"))

        # 3. Экспорт данных из БД в exported_plan.json
        models_to_json()
        self.stdout.write(self.style.SUCCESS("JSON успешно экспортирован в exported_plan.json"))

        # 4. Вывод содержимого моделей в консоль
        self.print_model_data()

        self.stdout.write(self.style.SUCCESS("Парсер успешно завершил работу!"))

    def print_model_data(self):
        """Выводит содержимое моделей в читаемом виде, начиная с учебного плана."""
        print("\n=== Учебные планы ===")
        for sp in StudyPlan.objects.all():
            print(f"{sp.id} | {sp.name} (Спец.: {sp.specialization_code}, ГОС: {sp.gos_type}, Дата: {sp.create_date})")
            for category in sp.cycles.all():
                print(f"   └─ Категория: {category.id} | {category.identificator}: {category.cycles}")
                for study_cycle in category.child_cycles.all():
                    print(f"       └─ Учебный цикл: {study_cycle.id} | {study_cycle.identificator}: {study_cycle.cycles}")
                    # Вывод модулей (План строк)
                    for module in study_cycle.plan_strings.all():
                        print(f"           └─ Модуль: {module.id} | Дисциплина: {module.name}")
                        # Вывод дочерних планов строки (Дисциплины)
                        for disipline in module.child_plan_strings.all():
                            print(f"               └─ Дисциплина: {disipline.id} | {disipline.name}")
                            clock_cells = disipline.clock_cells.all()
                            if clock_cells:
                                print("                   └─ Ячейки часов (привязанные к дисциплине):")
                                for clock in clock_cells:
                                    print(f"                      ⏱ {clock.id} | Курс {clock.course}, Семестр {clock.semestr}, Часы: {clock.count_of_clocks}")
                    # Вывод ячеек часов, прикрепленных к учебному циклу
                    clock_cells = study_cycle.clock_cells.all()
                    if clock_cells:
                        print("           └─ Ячейки часов (привязанные к учебному циклу):")
                        for clock in clock_cells:
                            print(f"               ⏱ {clock.id} | Курс {clock.course}, Семестр {clock.semestr}, Часы: {clock.count_of_clocks}")
