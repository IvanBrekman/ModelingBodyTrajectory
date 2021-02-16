from constants import *
from sympy import Symbol, sin, cos

# Переменные
v0 = Symbol('v0')
a = Symbol('a')

h = Symbol('h')
s = Symbol('s')
t = Symbol('t')

vmx = Symbol('vmx')
vmn = Symbol('vmx')

tu = Symbol('tu')
td = Symbol('td')
#

# Формулы
h_v0_a = (v0 ** 2 * sin(a) ** 2) / (2 * g) - h
s_v0_a = v0 ** 2 * sin(a * 2) / g - s

vmx_v0 = v0 - vmx
vmn_v0_a = v0 * cos(a) - vmn

tu_v0_a = v0 * sin(a) / g - tu
td_h = (2 * h / g) ** 0.5 - td
t_tu_td = tu + td - t
#
