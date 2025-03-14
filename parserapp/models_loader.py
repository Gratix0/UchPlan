from datetime import datetime
from parserapp.models import StudyPlan, Category, StudyCycle, Module, Disipline, ClockCell
from parserapp.validators import validate_text, validate_discipline_index, validate_discipline_hours

def load_json_to_models(rup_data):
    """
    Загружает данные из JSON-структуры, сформированной get_plan_rup(),
    в модели Django. Осуществляет предварительное преобразование даты.
    """
    # Очистка базы данных перед загрузкой новых данных
    StudyPlan.objects.all().delete()
    Category.objects.all().delete()
    StudyCycle.objects.all().delete()
    Module.objects.all().delete()
    Disipline.objects.all().delete()
    ClockCell.objects.all().delete()

    create_date_str = rup_data.get("create_date")
    if create_date_str:
        try:
            create_date = datetime.strptime(create_date_str, "%Y-%m-%dT%H:%M:%S").date()
        except Exception as e:
            print(f"Ошибка преобразования даты: {e}")
            create_date = None
    else:
        create_date = None

    study_plan_obj = StudyPlan.objects.create(
        id=rup_data["id"],
        qualification=rup_data.get("qualification"),
        admission_year=rup_data.get("admission_year"),
        create_date=create_date
    )

    all_warnings = []  # Список для хранения всех опечаток
    previous_indices = {}  # Словарь для хранения предыдущих индексов

    # Обрабатываем циклы (Category) и дочерние циклы (StudyCycle)
    for cycle in rup_data.get("stady_plan", []):
        # Проверяем имя Category
        category_name = cycle.get("cycles")
        if category_name is not None:  # Добавляем проверку
            category_warnings = validate_text(category_name)
            if category_warnings:
                all_warnings.extend(category_warnings)

        category_obj = Category.objects.create(
            id=cycle["id"],
            identificator=cycle.get("identificator"),
            cycles=category_name,
            study_plan=study_plan_obj,
            warnings=bool(category_warnings),
            warning_description=category_warnings
        )
        for child in cycle.get("children", []):
            # Проверяем имя StudyCycle
            study_cycle_name = child.get("cycles")
            if study_cycle_name is not None:  # Добавляем проверку
                study_cycle_warnings = validate_text(study_cycle_name)
                if study_cycle_warnings:
                    all_warnings.extend(study_cycle_warnings)

            study_cycle_obj = StudyCycle.objects.create(
                id=child["id"],
                identificator=child.get("identificator"),
                cycles=study_cycle_name,
                category=category_obj,
                warnings=bool(study_cycle_warnings),
                warning_description=study_cycle_warnings
            )
            for plan in child.get("plans_of_string", []):
                # Создаем Module из плана строки
                module_name = plan.get("discipline")
                if module_name is not None:  # Добавляем проверку
                    module_warnings = validate_text(module_name)
                    if module_warnings:
                        all_warnings.extend(module_warnings)
                module_obj = Module.objects.create(
                    id=plan["id"],
                    name=module_name,
                    studey_cycle=study_cycle_obj,
                    warnings=bool(module_warnings),
                    warning_description=module_warnings
                )
                # Обрабатываем ClockCell для плана (Module)
                existing_clock_ids = set()
                for course_index, course in enumerate(plan.get("clock_cells", [])):
                    for term_index, term in enumerate(course.get('terms',[])):
                        for clock in term.get('clock_cells',[]):
                            course = clock.get("course")
                            term = clock.get("term")
                            if course is None or term is None:
                                print(f"⚠WARNING: Missing 'course' or 'term' in clock cell: {clock}")
                                continue  # Пропускаем ячейку, если нет номера курса или семестра
                            if clock["id"] in existing_clock_ids:
                                print(f"⚠WARNING: Duplicate ClockCell ID detected: {clock['id']}")
                            else:
                                existing_clock_ids.add(clock["id"])
                            ClockCell.objects.create(
                                id=clock["id"],
                                code_of_type_work=clock.get("code_of_type_work"),
                                code_of_type_hours=clock.get("code_of_type_hours"),
                                course=int(course),
                                semestr=int(term),
                                count_of_clocks=int(clock.get("count_of_clocks") or 0),
                                module_plan_string=module_obj
                            )
                # Обрабатываем дочерние планы строки (Disipline)
                for child_plan in plan.get("children_strings", []):
                    discipline_name = child_plan.get("discipline")
                    discipline_index = child_plan.get("code_of_discipline")

                    if discipline_name is not None:  # Добавляем проверку
                        discipline_warnings = validate_text(discipline_name)
                        if discipline_warnings:
                            all_warnings.extend(discipline_warnings)

                    # Валидация индекса
                    index_warnings = validate_discipline_index(discipline_index, previous_indices)
                    if index_warnings:
                        print("=== Ошибки валидации индекса ===")
                        for warning in index_warnings:
                            print(warning)

                    disipline_obj = Disipline.objects.create(
                        id=child_plan["id"],
                        name=discipline_name,
                        index=discipline_index,
                        module=module_obj,
                        warnings=bool(discipline_warnings or index_warnings),
                        warning_description=discipline_warnings + index_warnings if discipline_warnings and index_warnings else discipline_warnings or index_warnings
                    )

                    # Вызываем валидацию часов для дисциплины
                    hour_warnings = validate_discipline_hours(child_plan)
                    if hour_warnings:
                        all_warnings.extend(hour_warnings)
                        disipline_obj.warnings = True
                        if disipline_obj.warning_description:
                            disipline_obj.warning_description.extend(hour_warnings)
                        else:
                            disipline_obj.warning_description = hour_warnings
                        disipline_obj.save()

                    existing_clock_ids = set()
                    for course_index, course in enumerate(child_plan.get("clock_cells", [])):
                        for term_index, term in enumerate(course.get('terms', [])):
                            for clock in term.get('clock_cells', []):
                                course = clock.get("course")
                                term = clock.get("term")
                                if course is None or term is None:
                                    print(f"⚠WARNING: Missing 'course' or 'term' in clock cell: {clock}")
                                    continue
                                if clock["id"] in existing_clock_ids:
                                    print(f"⚠WARNING: Duplicate ClockCell ID detected: {clock['id']}")
                                else:
                                    existing_clock_ids.add(clock["id"])
                                ClockCell.objects.create(
                                    id=clock["id"],
                                    code_of_type_work=clock.get("code_of_type_work"),
                                    code_of_type_hours=clock.get("code_of_type_hours"),
                                    course=int(course),
                                    semestr=int(term),
                                    count_of_clocks=int(clock.get("count_of_clocks") or 0),
                                    plan_string=disipline_obj
                                )

        print("=== Найденные опечатки ===")
        for warning in all_warnings:
            print(warning)