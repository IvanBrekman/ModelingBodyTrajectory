import itertools as it

from formulas import *
from constants import MY_DB
from database_requests import *
from time import time


def check(combination) -> bool:
    """ Функция проверяет можно ли найти искомую переменную по заданным значениям """
    known_values = {value: best_values[value] for value in combination}
    find(known_values)
    return find_element in known_values


def is_unique(combination) -> bool:
    """ Функция проверяет уникальность найденной комбинации """
    for un_comb in unique_combs:
        if set(un_comb).issubset(combination):
            return False
    return True


s = time()
variables_collections = {}
for var in all_variables:
    print(var, end=' ')
    start_time = time()
    find_element = var
    other_elements = [var for var in all_variables if var != find_element]
    elements_collections = []

    # Поиск всех комбинаций с которыми можно найти искомую величину
    combs = []
    for r in range(1, 2 + 1):
        combs.append(it.combinations(other_elements, r))
    all_combinations = filter(lambda combination: check(combination), it.chain(*combs))
    #

    # Фильтрация найденных комбинаций по уникальности
    unique_combs = []
    for comb in all_combinations:
        if is_unique(comb):
            unique_combs.append(comb)
    #

    variables_collections[find_element] = (len(unique_combs), unique_combs)
    print(time() - start_time)

# Вывод и проверка результатов
for var in variables_collections:
    print(f'{var}: {variables_collections[var][0]}')
    print(*variables_collections[var][1])
    print()
print(time() - s)
#

ans = input('is all ok? (yes or no)\n')
while ans not in ('yes', 'no'):
    ans = input('is all ok? (yes, no)\n')
if ans == 'no':
    exit()

# Запись результатов в базу данных
delete_data_from_db(MY_DB, 'variables_collections', {})
for variable in variables_collections:
    for comb in variables_collections[variable][1]:
        add_data_to_db(MY_DB, 'variables_collections', ('variable', 'required_values'),
                       (f"'{variable}'", f"'{' '.join(str(var) for var in comb)}'"))
#
