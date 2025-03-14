from parserapp.models import WhitelistWord
from pyaspeller import YandexSpeller
import re

def get_whitelist():
    """Возвращает множество слов из вайтлиста, используя кеш."""
    _cached_whitelist = set(WhitelistWord.objects.values_list('word', flat=True))
    return _cached_whitelist

def validate_text(text):
    """
    Проверяет текст на наличие ошибок с помощью Yandex Speller,
    игнорируя слова из вайтлиста.
    Возвращает список ошибок или None, если ошибок нет.
    """
    speller = YandexSpeller()
    changes = speller.spell(text)
    if changes:
        errors = []
        whitelist_words = get_whitelist()  # Используем кешированное множество
        for change in changes:
            word_lower = change['word'].lower()
            if word_lower not in whitelist_words:
                errors.append(f"Возможно ошибка в слове '{change['word']}' возможно это подходящее слово: {change['s']}")
        return errors
    return None

def validate_discipline_index(index: str, previous_indices: dict):
    """
    Проверяет формат индекса дисциплины и последовательность индексов,
    учитывая двусоставные индексы модулей (МДК.01.01).

    Args:
        index: Индекс дисциплины (например, "МДК.01.01").
        previous_indices: Словарь, хранящий предыдущие индексы.
                          Ключи - комбинация префикса и номера модуля (МДК.01, МДК.1).

    Returns:
        Список ошибок или None, если ошибок нет.
    """
    if not index:
        return ["Индекс дисциплины отсутствует."]

    index = index.strip()

    match = re.match(r"([А-Я]+)\.(\d{1,2}(?:\.\d{1,2})?)", index)
    if not match:
        return [f"Неверный формат индекса '{index}'. Ожидается формат 'Префикс.Число' или 'Префикс.Число.Число'."]

    prefix = match.group(1)
    number_part = match.group(2)

    valid_prefixes = ["ОГСЭ", "ЕН", "ОПЦ", "ПЦ", "ПМ", "МДК", "УП", "ПП", "ПДП"]
    if prefix not in valid_prefixes:
        return [f"Недопустимый префикс '{prefix}' в индексе '{index}'. Допустимые префиксы: {', '.join(valid_prefixes)}."]

    if "." in number_part:
        main_number_str, secondary_number_str = number_part.split(".")
        main_number, secondary_number = int(main_number_str), int(secondary_number_str)
    else:
        main_number_str = number_part
        main_number = int(main_number_str)
        secondary_number = None

    # Создаем ключ, включающий номер модуля (МДК.01, МДК.1 и т.д.)
    module_key = f"{prefix}.{main_number_str}"

    if module_key not in previous_indices:
        previous_indices[module_key] = (None, None)  # Инициализируем запись

    prev_main, prev_secondary = previous_indices[module_key]

    if prev_main is None:  # Первый индекс для данного модуля
        if secondary_number is None and main_number != int(main_number_str): #проверка на валидность индекса, если он без подчасти
            return [f"Неверная последовательность индекса '{index}'. Ожидается '{prefix}.1' или '{prefix}.01'."]
        if secondary_number is not None and secondary_number != 1:
            return [f"Неверная последовательность индекса '{index}'. Ожидается '{prefix}.{main_number_str}.1' или '{prefix}.0{main_number_str}.01'."]
        previous_indices[module_key] = (main_number, secondary_number)
    else:  # Индекс для данного модуля уже существует
        if secondary_number is None:  # Если текущий индекс - "Префикс.Число"
            if prev_secondary is not None:
                return [f"Неверная последовательность индекса '{index}'. Индекс с одной цифрой не может идти после индекса с двумя."]
            if main_number != prev_main + 1:
                return [f"Неверная последовательность индекса '{index}'. Ожидается '{prefix}.{prev_main + 1}'."]
            previous_indices[module_key] = (main_number, None)
        else:  # Если текущий индекс - "Префикс.Число.Число"
            if prev_secondary is None:
                if main_number != prev_main or secondary_number != 1:
                    return [f"Неверная последовательность индекса '{index}'. Ожидается '{prefix}.{prev_main}.1'."]
            else:
                if main_number != prev_main or secondary_number != prev_secondary + 1:
                    return [f"Неверная последовательность индекса '{index}'. Ожидается '{prefix}.{prev_main}.{prev_secondary + 1}'."]
            previous_indices[module_key] = (main_number, secondary_number)

    return None

def validate_discipline_hours(discipline):
    """
    Проверяет, что суммарное количество часов за семестр у дисциплины
    равняется сумме часов по всем ячейкам, кроме итоговой.
    """
    for course_index, course in enumerate(discipline.get("clock_cells", [])):
        for term_index, term in enumerate(course.get('terms', [])):
            total_hours = 0
            max_hours = 0
            for clock in term.get('clock_cells', []):
                count_of_clocks = clock.get("count_of_clocks", 0)
                total_hours += count_of_clocks
                if count_of_clocks > max_hours:
                    max_hours = count_of_clocks

            if total_hours - max_hours != max_hours:
                 return [
                    f"Сумма часов по ячейкам ({total_hours - max_hours}) не совпадает с итоговым количеством часов ({max_hours}) за семестр {term_index + 1} курса {course_index + 1} у дисциплины '{discipline.get('discipline')}'."]
    return None