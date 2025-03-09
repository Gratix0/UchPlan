from django.core.management.base import BaseCommand
from parserapp.parser import get_plan_rup, load_json_to_models, models_to_json
from parserapp.models import StudyPlan, Cycle, ChildCycle, PlanString, ChildPlanString, ClockCell


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
            print(f"{sp.id} | {sp.name} "
                  f"(Спец.: {sp.specialization_code}, ГОС: {sp.gos_type}, Дата: {sp.create_date})")
            for cycle in sp.cycles.all():
                print(f"   └─ Цикл: {cycle.id} | {cycle.identificator}: {cycle.cycles}")
                for child in cycle.child_cycles.all():
                    print(f"       └─ Дочерний цикл: {child.id} | {child.identificator}: {child.cycles}")
                    for plan in child.plan_strings.all():
                        print(f"           └─ План строки: {plan.id} | Дисциплина: {plan.discipline}")
                        # Вывод ячеек часов для плана строки
                        clock_cells = plan.clock_cells.all()
                        if clock_cells:
                            print("               └─ Ячейки часов:")
                            for clock in clock_cells:
                                parent = clock.plan_string.id if clock.plan_string else clock.child_plan_string.id
                                print(f"                  ⏱ {clock.id} | Курс {clock.course}, Семестр {clock.semestr}, "
                                      f"Часы: {clock.count_of_clocks} (Привязан к: {parent})")
                        # Вывод дочерних планов строки
                        for child_plan in plan.child_plan_strings.all():
                            print(f"           └─ Дочерний план строки: {child_plan.id} | Дисциплина: {child_plan.discipline}")
                            clock_cells = child_plan.clock_cells.all()
                            if clock_cells:
                                print("               └─ Ячейки часов:")
                                for clock in clock_cells:
                                    parent = clock.plan_string.id if clock.plan_string else clock.child_plan_string.id
                                    print(f"                  ⏱ {clock.id} | Курс {clock.course}, Семестр {clock.semestr}, "
                                          f"Часы: {clock.count_of_clocks} (Привязан к: {parent})")
