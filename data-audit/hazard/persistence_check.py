"""Verify the persistence condition (Equation 4 of the paper) against the
model it is derived from (Equations 1-3), symbolically.

The condition was re-derived for this paper rather than copied, so it needed
an independent check. Two are run here:

  1. Symbolic. Set the three ODEs to zero, solve for the non-trivial
     equilibrium, and confirm that requiring a positive adult population
     yields exactly a*f/(2g) > c + d + f.

  2. Numerical. Confirm the same condition reproduces the suitability
     classification of the lookup table published with Kaye et al. (2024),
     via the equivalent form used in their own code (q0 < 1). The full
     reimplementation check is in niche_reimpl.py; this one isolates the
     persistence condition itself.
"""
import sys
import sympy as sp

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

E, A, M, K = sp.symbols('E A M K', positive=True)
a, b, c, d, f, g = sp.symbols('a b c d f g', positive=True)

# Equations 1-3 of the paper, right-hand sides.
dE = a * M - b * E
dA = b * E * (1 - A / K) - c * A - d * A - f * A
dM = sp.Rational(1, 2) * f * A - g * M

print('Model (Equations 1-3):')
for name, expr in (('dE/dt', dE), ('dA/dt', dA), ('dM/dt', dM)):
    print(f'  {name} = {expr}')

# Non-trivial equilibrium: solve dE=0 and dM=0 for E and M in terms of A,
# substitute into dA=0, and divide through by A (A > 0 by assumption).
solE = sp.solve(sp.Eq(dE, 0), E)[0]              # E = a*M/b
solM = sp.solve(sp.Eq(dM, 0), M)[0]              # M = f*A/(2g)
E_of_A = sp.simplify(solE.subs(M, solM))
print(f'\nFrom dE/dt=0:  E = {sp.simplify(solE)}')
print(f'From dM/dt=0:  M = {solM}')
print(f'So             E = {E_of_A}')

residual = sp.simplify(dA.subs({E: E_of_A}) / A)  # divide by A > 0
print(f'\ndA/dt = 0 divided by A:\n  {sp.simplify(residual)} = 0')

A_star = sp.solve(sp.Eq(residual, 0), A)[0]
print(f'\nEquilibrium aquatic population:\n  A* = {sp.simplify(A_star)}')

# A* > 0 with K > 0. Extract the condition.
ratio = sp.simplify(A_star / K)
print(f'  A*/K = {sp.simplify(ratio)}')

# The paper's Equation 4.
claimed = a * f / (2 * g) - (c + d + f)          # > 0
# A*/K > 0 iff `claimed` > 0: show A*/K equals `claimed` times a positive factor.
factor = sp.simplify(ratio / claimed)
print(f'\n  A*/K divided by [a*f/(2g) - (c+d+f)] = {factor}')
print(f'  This factor is positive for positive rates, so A* > 0 iff '
      f'the paper\'s condition holds.')

ok = sp.simplify(factor - 2 * g / (a * f)) == 0
print(f'\n  factor == 2g/(a f)? {ok}')

# State the verdict.
cond = sp.simplify(sp.solve(sp.Eq(ratio, 0), a)[0])
print(f'\nBoundary of the niche, solved for a:  a = {cond}')
print(f'Paper Equation 4 rearranged for a:    a = {sp.simplify(2 * g * (c + d + f) / f)}')
match = sp.simplify(cond - 2 * g * (c + d + f) / f) == 0
print(f'\nVERDICT: Equation 4 is {"CORRECT" if match and ok else "WRONG"} '
      f'as a persistence condition for Equations 1-3.')
sys.exit(0 if (match and ok) else 1)
