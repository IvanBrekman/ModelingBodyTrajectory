import sympy
from sympy.abc import *
from math import sin, radians, degrees

g = 10
h = sympy.Symbol('h')
v0 = sympy.Symbol('v0')
a = sympy.Symbol('a')

equation = (v0 ** 2 * sympy.sin(a) ** 2) / (2 * g) - h
equation = equation.subs({h: 31.25, v0: 50})
solves = sympy.solveset(equation, a, sympy.S.Reals)
print(equation, solves)
for solve in solves:
    print()

exp = 'sin(x) ** 2 - 0.25'
ans = sympy.solve(exp, x)
for num in ans:
    print(degrees(num))
