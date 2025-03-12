import xml.etree.ElementTree as et
from xml.etree.ElementTree import Element
from typing import List
import json
import uuid
from datetime import datetime

from parserapp.models import StudyPlan, Category, StudyCycle, Module, Disipline, ClockCell

def get_plan_rup():
    """
    Парсит XML и формирует структуру данных с информацией об ООП и учебном плане.
    Новая структура: ООП (StudyPlan) и список циклов (stady_plan),
    в которых находятся дочерние циклы, план строк и ячейки часов.
    """
    plan_dict = []
    rup = {}

    plany_ciclov: List[Element] = []
    plany_ciclov_childs: List[Element] = []
    plany_novie_chasy: List[Element] = []
    plany_stroky: List[Element] = []
    plany_stroky_childs: List[Element] = []

    tree = et.parse("gg.plx")
    root = tree.getroot()
    root_child = root[0][0]

    for child in root_child:
        tag_name = child.tag.replace("{http://tempuri.org/dsMMISDB.xsd}", '')
        match tag_name:
            case "ПланыЦиклы":
                if child.attrib.get('КодРодителя'):
                    plany_ciclov_childs.append(child)
                else:
                    plany_ciclov.append(child)
            case "ПланыСтроки":
                if child.attrib.get('КодРодителя'):
                    plany_stroky_childs.append(child)
                else:
                    plany_stroky.append(child)
            case "ПланыНовыеЧасы":
                plany_novie_chasy.append(child)
            case "ООП":
                rup = {
                    'id': str(uuid.uuid4()),
                    'specialization_code': child.get('Шифр'),
                    'name': child.get('Название'),
                    'create_date': child.get('ДатаДокумента'),
                    'gos_type': child.get('ТипГОСа'),
                    'stady_plan': []
                }

    for cicl in plany_ciclov:
        plan_dict.append({
            "id": cicl.get('Код'),
            "identificator": cicl.get('Идентификатор'),
            "cycles": cicl.get('Цикл'),
            "children": []
        })

    for child in plany_ciclov_childs:
        parent_code = child.get("КодРодителя")
        for parent in plan_dict:
            if parent_code == parent['id']:
                parent['children'].append({
                    "id": child.get('Код'),
                    "identificator": child.get('Идентификатор'),
                    "cycles": child.get('Цикл'),
                    "parent_id": child.get('КодРодителя'),
                    "plans_of_string": []
                })

    for cycl in plan_dict:
        cycl['id'] = str(uuid.uuid4())
        for child in cycl['children']:
            child_id_local = child['id']
            child['id'] = str(uuid.uuid4())
            child['parent_id'] = cycl['id']
            for string in plany_stroky:
                string_block_id = string.get("КодБлока")
                if child_id_local == string_block_id:
                    parent_string_id_local = string.get('Код')
                    parent_string_object = {
                        'id': str(uuid.uuid4()),
                        'discipline': string.get('Дисциплина'),
                        'code_of_cycle_block': child['id'],
                        'clock_cells': [],
                        'children_strings': []
                    }
                    for child_string in plany_stroky_childs:
                        code_of_parent = child_string.get('КодРодителя')
                        if parent_string_id_local == code_of_parent:
                            child_string_id_local = child_string.get('Код')
                            child_string_object = {
                                'id': str(uuid.uuid4()),
                                'discipline': child_string.get('Дисциплина'),
                                'code_of_cycle_block': child['id'],
                                'parent_string_id': parent_string_object['id'],
                                'clock_cells': []
                            }
                            for hour in plany_novie_chasy:
                                new_hour_parent_id = hour.get("КодОбъекта")
                                if new_hour_parent_id == child_string_id_local:
                                    child_string_object['clock_cells'].append({
                                        'id': str(uuid.uuid4()),
                                        'code_of_type_work': hour.get("КодВидаРаботы"),
                                        'code_of_type_hours': hour.get("КодТипаЧасов"),
                                        'course': hour.get("Курс"),
                                        'semestr': hour.get("Семестр"),
                                        'count_of_clocks': hour.get("Количество"),
                                        'parent_string_id': child_string_object['id']
                                    })
                            parent_string_object['children_strings'].append(child_string_object)
                    for hour in plany_novie_chasy:
                        new_hour_parent_id = hour.get("КодОбъекта")
                        if new_hour_parent_id == parent_string_id_local:
                            parent_string_object['clock_cells'].append({
                                'id': str(uuid.uuid4()),
                                'code_of_type_work': hour.get("КодВидаРаботы"),
                                'code_of_type_hours': hour.get("КодТипаЧасов"),
                                'course': hour.get("Курс"),
                                'semestr': hour.get("Семестр"),
                                'count_of_clocks': hour.get("Количество"),
                                'parent_string_id': parent_string_object['id']
                            })
                    child['plans_of_string'].append(parent_string_object)

    rup['stady_plan'] = plan_dict

    with open("plan.json", "w", encoding="utf-8") as file:
        json.dump(rup, file, ensure_ascii=False, indent=4)
    print("=== JSON data (from XML) ===")
    print(json.dumps(rup, ensure_ascii=False, indent=4))
    return rup


def load_json_to_models(rup_data):
    """
    Загружает данные из JSON-структуры, сформированной get_plan_rup(),
    в модели Django. Осуществляет предварительное преобразование даты.
    """
    create_date_str = rup_data.get("create_date")
    try:
        create_date = datetime.strptime(create_date_str, "%Y-%m-%dT%H:%M:%S").date()
    except Exception as e:
        print(f"Ошибка преобразования даты: {e}")
        create_date = create_date_str

    study_plan_obj = StudyPlan.objects.create(
        id=rup_data["id"],
        specialization_code=rup_data.get("specialization_code"),
        name=rup_data.get("name"),
        create_date=create_date,
        gos_type=rup_data.get("gos_type")
    )

    # Обрабатываем циклы (Category) и дочерние циклы (StudyCycle)
    for cycle in rup_data.get("stady_plan", []):
        category_obj = Category.objects.create(
            id=cycle["id"],
            identificator=cycle.get("identificator"),
            cycles=cycle.get("cycles"),
            study_plan=study_plan_obj
        )
        for child in cycle.get("children", []):
            study_cycle_obj = StudyCycle.objects.create(
                id=child["id"],
                identificator=child.get("identificator"),
                cycles=child.get("cycles"),
                category=category_obj
            )
            for plan in child.get("plans_of_string", []):
                # Создаем Module из плана строки
                module_obj = Module.objects.create(
                    id=plan["id"],
                    name=plan.get("discipline"),
                    studey_cycle=study_cycle_obj
                )
                # Обрабатываем ClockCell для плана (Module)
                # Привязываем их к StudyCycle через поле child_plan_string
                existing_clock_ids = set()
                for clock in plan.get("clock_cells", []):
                    if clock["id"] in existing_clock_ids:
                        print(f"⚠WARNING: Duplicate ClockCell ID detected: {clock['id']}")
                    else:
                        existing_clock_ids.add(clock["id"])
                    ClockCell.objects.create(
                        id=clock["id"],
                        code_of_type_work=clock.get("code_of_type_work"),
                        code_of_type_hours=clock.get("code_of_type_hours"),
                        course=int(clock.get("course") or 0),
                        semestr=int(clock.get("semestr") or 0),
                        count_of_clocks=int(clock.get("count_of_clocks") or 0),
                        child_plan_string=study_cycle_obj
                    )
                # Обрабатываем дочерние планы строки (Disipline)
                for child_plan in plan.get("children_strings", []):
                    disipline_obj = Disipline.objects.create(
                        id=child_plan["id"],
                        name=child_plan.get("discipline"),
                        module=module_obj
                    )
                    for clock in child_plan.get("clock_cells", []):
                        ClockCell.objects.create(
                            id=clock["id"],
                            code_of_type_work=clock.get("code_of_type_work"),
                            code_of_type_hours=clock.get("code_of_type_hours"),
                            course=int(clock.get("course") or 0),
                            semestr=int(clock.get("semestr") or 0),
                            count_of_clocks=int(clock.get("count_of_clocks") or 0),
                            plan_string=disipline_obj
                        )


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
                    for clock in study_cycle.clock_cells.all():
                        module_dict["clock_cells"].append({
                            "id": str(clock.id),
                            "code_of_type_work": clock.code_of_type_work,
                            "code_of_type_hours": clock.code_of_type_hours,
                            "course": clock.course,
                            "semestr": clock.semestr,
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
                                "semestr": clock.semestr,
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
    plan_data = get_plan_rup()

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
