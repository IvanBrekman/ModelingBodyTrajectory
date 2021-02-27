from constants import *

import sympy as sym
from math import radians, degrees


class Symbol(sym.Symbol):
    """ Класс-наследник для реализации работы с углами """

    def __init__(self, name, is_angle=False):
        super(Symbol, self).__init__()
        self.name = name
        self.is_angle = is_angle
        self.is_known = True

    def get_value(self, value):
        return radians(value) if self.is_angle else value


class Formula:
    """ Класс описания формул для поиска различных величин """

    def __init__(self, variables: (list, tuple), formula):
        self.variables = variables
        self._formula = formula

    def can_find(self, known_values: dict):
        """
            Метод проверяет возможность найти значение какой-либо переменной по данной формуле,
            имея known_values.
            Вернет переменную, которую можно найти по данной формуле (или None если такой нет)
        """

        if y0.is_known and y0 not in known_values:
            known_values[y0] = 0
        unknown_variables = set(self.variables) - set(filter(lambda val: val in self.variables,
                                                             known_values))
        if len(unknown_variables) == 1:
            return list(unknown_variables)[0]

    def calc(self, target_variable: sym.Symbol, another_variables: dict):
        """
        Метод рассчитывает знаение целевой переменной по заданным остальным значениям
        :param target_variable: Целевая переменная
        :param another_variables: Словарь остальный переменных с их значениями
        :return: Числовой ответ
        """

        def is_complex(value) -> bool:
            """
            Функция проверяет является ли число комплексным
            :param value: Проверяемое число
            :return: True если число комплексное, иначе False
            """

            try:
                degrees(value)
                return False
            except TypeError:
                return True

        assert all(var in self.variables for var in [target_variable] + list(another_variables)), \
            "Error occurred in Formula.calc_formula. Got incorrect variables."
        assert 1 + len(another_variables) == len(self.variables), \
            f"Error occurred in Formula.calc_formula. Not enough variables (expected " \
            f"{len(self.variables) - 1}, got {len(another_variables)}"

        # Расчет формулы для переменной, выражения и решения для переменной
        formula = sym.solve(self._formula, target_variable)
        another_variables[g] = CONSTANTS['g']
        if y0.is_known and y0 not in another_variables:
            another_variables[y0] = y0_const
        if self.variables == (vmx, v0, a, t) and target_variable == v0:
            solve = formula[1].subs(another_variables)
            return solve, formula[1]
        exp = self._formula.subs(another_variables)
        solve = list(filter(lambda x: not is_complex(x), sym.solve(exp, target_variable)))
        #

        if not solve:  # Проверка на наличие решений
            known_values = "; ".join(f"{key} = {value}" for key, value in another_variables.items())
            raise ValueError(f'Невозможно рассчитать формулу {target_variable} = {formula[0]},\n'
                             f'при {known_values}')

        if target_variable.is_angle:  # Корректирование ответа случае если переменная является углом
            val, f = [(rad, [formula[i]]) for i, rad in enumerate(solve)
                      if 0 <= degrees(rad) <= 90][0]
            return degrees(val), f[0]

        if target_variable == y0 and solve[0] < 10 ** -10:  # Уточнение результата для y0
            if solve[0] < -1:
                known_values = "; ".join(f"{key} = {value}"
                                         for key, value in another_variables.items())
                raise ValueError(f'Невозможно рассчитать формулу {target_variable} = {formula[0]},\n'
                                 f'при {known_values}.\nОтрицательный результат')

            return 0.0, formula[0]

        positive_index = 0 if solve[0] >= 0 else 1
        return solve[positive_index], formula[positive_index]


def find(known_values: dict, variable_formula=None) -> (dict, dict):
    """
    Функция осуществляет поиск значений всевозможных переменных по известным величинам
    :param known_values: Словарь известных значений (передаваемый словарь будет изменяться)
    :param variable_formula: Словарь формул для искомых значений (нужен при погружении в функцию)
    :return: Возвращает кортеж 2-х словарей: словарь известных теперь значений и словарь формул
    """

    assert all(isinstance(value, sym.Symbol) for value in known_values), \
        "Error occurred in find() function: not all values has type Sympy.Symbol"

    len_kn_val = len(known_values)
    variable_formula = variable_formula or {}

    # Поиск величин по всем имеющимся формулам
    for formula in all_form:
        var = formula.can_find(known_values)
        if var:
            val, f = formula.calc(var, {k: k.get_value(v) for k, v in known_values.items()
                                        if k in formula.variables})
            known_values[var] = val
            variable_formula[var] = f
    #

    if len_kn_val != len(known_values):  # Если нашлась хоть 1 новая величина, повторяем поиск
        return find(known_values, variable_formula)

    return known_values, variable_formula


# Переменные
g = Symbol('g')
y0 = Symbol('y0')
v0 = Symbol('v0')
a = Symbol('a', is_angle=True)

h = Symbol('h')
s = Symbol('s')
t = Symbol('t')

vmx = Symbol('vmx')
vmn = Symbol('vmn')

tu = Symbol('tu')
td = Symbol('td')

all_variables = [v0, a, h, s, t, vmx, vmn, tu, td, y0]
#

# Формулы
h_v0_a = Formula((h, v0, a, y0), (v0 ** 2 * sym.sin(a) ** 2) / (2 * g) - h + y0)

s_v0_a_y00 = Formula((s, v0, a), v0 ** 2 * sym.sin(a * 2) / g - s)
s_v0_a_t = Formula((s, v0, a, t), v0 * sym.cos(a) * t - s)

vmx_v0_y00 = Formula((vmx, v0), v0 - vmx)
vmx_v0_a_t = Formula((vmx, v0, a, t),
                     ((v0 * sym.cos(a)) ** 2 + (v0 * sym.sin(a) - g * t) ** 2) ** 0.5 - vmx)
vmn_v0_a = Formula((vmn, v0, a), v0 * sym.cos(a) - vmn)

tu_v0_a = Formula((tu, v0, a), v0 * sym.sin(a) / g - tu)
td_h = Formula((td, h), (2 * h / g) ** 0.5 - td)
t_tu_td = Formula((t, tu, td), tu + td - t)

all_form = [h_v0_a, s_v0_a_y00, vmx_v0_y00, vmn_v0_a, tu_v0_a, td_h, t_tu_td]
#

# "Хорошие" значения для поиска комбинаций переменных
best_values = {v0: 50.0, a: 30.0, h: 31.25, s: 216.506350946110,
               vmx: 50.0, vmn: 43.3012701892219, tu: 2.5, td: 2.5, t: 5.0, y0: 0}
#


if __name__ == '__main__':
    b, f1 = find({v0: 50.0, h: 31.25})
    print(b)
    print(sorted(b, key=lambda val: val != a))
