import sympy
from math import sin, radians, degrees

help(sympy.Symbol.__init__)
g = 10
h = sympy.Symbol('h')
v0 = sympy.Symbol('v0')
a = sympy.Symbol('a')

equation = (v0 ** 2 * sympy.sin(a) ** 2) / (2 * g) - h
equation = equation.subs({h: 31.25, v0: 50})
solves = sympy.solveset(equation, a, sympy.S.Reals)
print(equation, solves)
for solve in solves:
    print(solve)

exp = str(equation)
ans = sympy.solve(exp, a)
for num in ans:
    print(degrees(num))
