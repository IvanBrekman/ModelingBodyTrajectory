from constants import *

import sympy as sym
from math import radians, degrees


class Symbol(sym.Symbol):
    def __init__(self, name, is_angle=False):
        super(Symbol, self).__init__()
        self.name = name
        self.is_angle = is_angle

    def get_value(self, value):
        return radians(value) if self.is_angle else value


class Formula:
    def __init__(self, variables: (list, tuple), formula):
        self.variables = variables
        self._formula = formula

    def can_find(self, known_values: (list, tuple)):
        unknown_variables = set(self.variables) - \
                            set(filter(lambda val: val in self.variables, known_values))
        if len(unknown_variables) == 1:
            return list(unknown_variables)[0]

    def calc(self, target_variable: sym.Symbol, another_variables: dict):
        """
        Метод рассчитывает знаение целевой переменной по заданным остальным значениям
        :param target_variable: Целевая переменная
        :param another_variables: Словарь остальный переменных с их значениями
        :return: Числовой ответ
        """

        assert all(var in self.variables for var in [target_variable] + list(another_variables)), \
            "Error occurred in Formula.calc_formula. Got incorrect variables."
        assert 1 + len(another_variables) == len(self.variables), \
            f"Error occurred in Formula.calc_formula. Not enough variables (expected " \
            f"{len(self.variables)}, got {1 + len(another_variables)}"

        formula = sym.solve(self._formula, target_variable)
        another_variables[g] = g_const
        exp = self._formula.subs(another_variables)
        solve = sym.solve(exp, target_variable)
        print(solve, self.variables, another_variables, self._formula)

        if not solve:
            known_values = "; ".join(f"{key} = {value}"for key, value in another_variables.items())
            raise ValueError(f'Невозможно рассчитать формулу {target_variable} = {formula[0]},\n'
                             f'при {known_values}')

        if target_variable.is_angle:
            val, f = [(rad, [formula[i]]) for i, rad in enumerate(solve) if 0 <= degrees(rad) <= 90][
                0]
            return degrees(val), f
        return sym.solve(exp, target_variable)[0], formula


def find(known_values: dict, variable_formula=None) -> (dict, dict):
    assert all(isinstance(value, sym.Symbol) for value in known_values), \
        "Error occurred in VariableInfo.find() method: not all values has type Sympy.Symbol"
    len_kn_val = len(known_values)
    variable_formula = variable_formula or {}

    for formula in all_form:
        var = formula.can_find(known_values)
        if var:
            print(formula.calc(var, {k: k.get_value(v) for k, v in known_values.items()
                                     if k in formula.variables}), 'aaaaaaa')
            val, f = formula.calc(var, {k: k.get_value(v) for k, v in known_values.items()
                                        if k in formula.variables})
            known_values[var] = val
            variable_formula[var] = f

    if len_kn_val != len(known_values):
        return find(known_values, variable_formula)

    return known_values, variable_formula


# Переменные
g = Symbol('g')
v0 = Symbol('v0')
a = Symbol('a', is_angle=True)

h = Symbol('h')
s = Symbol('s')
t = Symbol('t')

vmx = Symbol('vmx')
vmn = Symbol('vmn')

tu = Symbol('tu')
td = Symbol('td')
#

# Формулы
h_v0_a = Formula((h, v0, a), (v0 ** 2 * sym.sin(a) ** 2) / (2 * g) - h)
s_v0_a = Formula((s, v0, a), v0 ** 2 * sym.sin(a * 2) / g - s)

vmx_v0 = Formula((vmx, v0), v0 - vmx)
vmn_v0_a = Formula((vmn, v0, a), v0 * sym.cos(a) - vmn)

tu_v0_a = Formula((tu, v0, a), v0 * sym.sin(a) / g - tu)
td_h = Formula((td, h), (2 * h / g) ** 0.5 - td)
t_tu_td = Formula((t, tu, td), tu + td - t)

all_form = [h_v0_a, s_v0_a, vmx_v0, vmn_v0_a, tu_v0_a, td_h, t_tu_td]
#


if __name__ == '__main__':
    b, f1 = find({vmn: 0, vmx: 0})
    a, f2 = find({tu: 2.5, td: 2.5, v0: 50})
    print()
    print(a)
    print(b)
    print()
    print(sorted(a, key=lambda val: val != h))
