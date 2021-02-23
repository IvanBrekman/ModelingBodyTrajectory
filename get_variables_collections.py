import itertools as it

from formulas import *
from constants import MY_DB
from database_requests import *
from time import time


def check(combination, find_element) -> bool:
    """ Функция проверяет можно ли найти искомую переменную по заданным значениям """
    known_values = {value: best_values[value] for value in combination}
    find(known_values)
    return find_element in known_values


def is_unique(combination, unique_combs) -> bool:
    """ Функция проверяет уникальность найденной комбинации """
    for un_comb in unique_combs:
        if set(un_comb).issubset(combination):
            return False
    return True


def get_collections(y0_fame: bool):
    print(y0_fame)
    y0.is_known = y0_fame

    if not y0_fame:
        index = all_form.index(s_v0_a_y00)
        all_form[index] = s_v0_a_t

    start = time()
    variables_collections = {}

    for var in all_variables:
        print(var, end=' ')
        start_time = time()
        find_element = var
        other_elements = [var for var in all_variables if var != find_element]

        # Поиск всех комбинаций с которыми можно найти искомую величину
        combs = []
        for r in range(1, 3 + 1):
            combs.append(it.combinations(other_elements, r))
        all_combinations = filter(lambda coll: check(coll, find_element), it.chain(*combs))
        #

        # Фильтрация найденных комбинаций по уникальности
        unique_combs = []
        for comb in all_combinations:
            if is_unique(comb, unique_combs):
                unique_combs.append(comb)
        #

        variables_collections[find_element] = (len(unique_combs), unique_combs)
        print(time() - start_time)

    # Вывод и проверка результатов
    for var in variables_collections:
        print(f'{var}: {variables_collections[var][0]}')
        print(*variables_collections[var][1])
        print()
    print(time() - start)
    #

    ans = input('is all ok? (yes or no)\n')
    while ans not in ('yes', 'no'):
        ans = input('is all ok? (yes, no)\n')
    if ans == 'no':
        exit()

    # Запись результатов в базу данных
    for variable in variables_collections:
        for comb in variables_collections[variable][1]:
            add_data_to_db(MY_DB, 'variables_collections', ('variable', 'required_values', 'is_known'),
                           (variable, ' '.join(str(v) for v in comb), int(y0_fame)))
    #


if __name__ == '__main__':
    delete_data_from_db(MY_DB, 'variables_collections', {})
    get_collections(True)
    get_collections(False)
