import sympy as sym


g = 10
t = sym.Symbol('t')
v0 = sym.Symbol('v0')
a = sym.Symbol('a')
vmx = sym.Symbol('vmx')

equation = ((v0 * sym.cos(a)) ** 2 + (v0 * sym.sin(a) - g * t) ** 2) ** 0.5 - vmx
equation = equation.subs({v0: 50, g: 10, vmx: 50, t: 5})
print(equation)
solves = sym.solve(equation, a)
print(equation, solves)
for solve in solves:
    print(solve)
