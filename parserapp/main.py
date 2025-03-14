from parserapp.parser import RUP_parser
from parserapp.models_loader import load_json_to_models
from parserapp.models import StudyPlan, Category, StudyCycle, Module, Disipline, ClockCell
import json

def models_to_json():
    """
    Сериализует объекты моделей Django обратно в JSON-структуру,
    аналогичную исходному формату, и сохраняет её в файл exported_plan.json.
    """
    result = []

    for study_plan in StudyPlan.objects.all():
        study_plan_dict = {
            "id": str(study_plan.id),
            "specialization_code": study_plan.specialization_code,
            "name": study_plan.name,
            "create_date": str(study_plan.create_date),
            "gos_type": study_plan.gos_type,
            "stady_plan": []
        }
        for category in study_plan.cycles.all():
            category_dict = {
                "id": str(category.id),
                "identificator": category.identificator,
                "cycles": category.cycles,
                "children": []
            }
            for study_cycle in category.child_cycles.all():
                study_cycle_dict = {
                    "id": str(study_cycle.id),
                    "identificator": study_cycle.identificator,
                    "cycles": study_cycle.cycles,
                    "parent_id": str(study_cycle.category.id),
                    "plans_of_string": []
                }
                for module in study_cycle.plan_strings.all():
                    module_dict = {
                        "id": str(module.id),
                        "discipline": module.name,
                        "code_of_cycle_block": str(study_cycle.id),
                        "clock_cells": [],
                        "children_strings": []
                    }
                    # Clock cells, прикрепленные к StudyCycle (от модуля)
                    for clock in module.clock_cells.all():
                        module_dict["clock_cells"].append({
                            "id": str(clock.id),
                            "code_of_type_work": clock.code_of_type_work,
                            "code_of_type_hours": clock.code_of_type_hours,
                            "course": clock.course,
                            "term": clock.semestr,
                            "count_of_clocks": clock.count_of_clocks,
                            "parent_string_id": str(module.id)
                        })
                    for disipline in module.child_plan_strings.all():
                        disipline_dict = {
                            "id": str(disipline.id),
                            "discipline": disipline.name,
                            "code_of_cycle_block": str(study_cycle.id),
                            "parent_string_id": str(module.id),
                            "clock_cells": []
                        }
                        for clock in disipline.clock_cells.all():
                            disipline_dict["clock_cells"].append({
                                "id": str(clock.id),
                                "code_of_type_work": clock.code_of_type_work,
                                "code_of_type_hours": clock.code_of_type_hours,
                                "course": clock.course,
                                "term": clock.semestr,
                                "count_of_clocks": clock.count_of_clocks,
                                "parent_string_id": str(disipline.id)
                            })
                        module_dict["children_strings"].append(disipline_dict)
                    study_cycle_dict["plans_of_string"].append(module_dict)
                category_dict["children"].append(study_cycle_dict)
            study_plan_dict["stady_plan"].append(category_dict)
        result.append(study_plan_dict)

    with open("exported_plan.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    print("Данные сохранены в exported_plan.json")
    return result

if __name__ == "__main__":
    # 1. Парсим XML и сохраняем в JSON
    parser = RUP_parser()
    plan_data = parser.get_plan()

    # 2. Загружаем JSON в модели Django
    load_json_to_models(plan_data)

    # 3. Выводим в консоль содержимое моделей для отладки
    print("=== Debug: Содержимое моделей ===")
    print("Study Plans:")
    for sp in StudyPlan.objects.all():
        print(sp)
    print("Categories:")
    for category in Category.objects.all():
        print(category)
    print("Study Cycles:")
    for sc in StudyCycle.objects.all():
        print(sc)
    print("Modules:")
    for module in Module.objects.all():
        print(module)
    print("Disiplines:")
    for disipline in Disipline.objects.all():
        print(disipline)
    print("Clock Cells:")
    for clock in ClockCell.objects.all():
        print(clock)

    # 4. Сериализуем модели обратно в JSON и сохраняем в файл
    restored_json = models_to_json()
    with open("restored_plan.json", "w", encoding="utf-8") as f:
        json.dump(restored_json, f, ensure_ascii=False, indent=4)
    print("=== Restored JSON from models ===")
    print(json.dumps(restored_json, ensure_ascii=False, indent=4))