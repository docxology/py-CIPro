# Geometry and independent checks

Let $A=\prod_{i=1}^{m}\mathbb{P}^{n_i}$, with hyperplane classes $H_i$. A
configuration $Q=(q_{ia})$ gives the degrees of $r$ polynomials, one column per
polynomial. Write $D_a=\sum_i q_{ia}H_i$ for the divisor of the $a$th equation.
For a smooth intersection of the expected codimension, the normal sequence
and adjunction give

$$
\dim X=\sum_i n_i-r, \qquad
c(TX)=\left.
\frac{\prod_i(1+H_i)^{n_i+1}}{\prod_a(1+D_a)}
\right|_X .
$$

The condition $\sum_a q_{ia}=n_i+1$ in each row makes the canonical bundle
trivial by adjunction. That row check carries no smoothness information
about a chosen set of equations. To integrate a top-degree class $p$ built
from the $H_i$, multiply it by $\prod_a D_a$ in the ambient cohomology ring,
where $H_i^{n_i+1}=0$, and take the coefficient of $\prod_i H_i^{n_i}$.
The independent script `scripts/check_intersections.py` implements this calculation in a truncated integer polynomial ring and compares the analytical Hodge and Euler values to the archive. [@anderson-cipro; @candelas-cicy; @green-hubsch]

## Quintic and bicubic fixtures

**Quintic.** Use `{"DimPs": [4], "Conf": [[5]]}` for a degree-five
hypersurface in $\mathbb{P}^{4}$. The degree-three term of
$(1+H)^5/(1+5H)$ is $-40H^3$, and $\int_XH^3=5$. It follows that
$\int_Xc_3=-200$ and $\int_Xc_2H=50$. Lefschetz gives $h^{1,1}=1$ and
the Euler relation gives $h^{2,1}=101$. The released Cicy3 record is 7890.

**Bicubic.** Use `{"DimPs": [2, 2], "Conf": [[3], [3]]}` for a
hypersurface in $\mathbb{P}^{2}\times\mathbb{P}^{2}$. The nonzero
ambient-induced triple integrals are
$\int_X H_1^2H_2=\int_X H_1H_2^2=3$. The Chern classes in this basis are

$$
\begin{aligned}
c_2(TX)&=3H_1^2+9H_1H_2+3H_2^2,\\
c_3(TX)&=-27(H_1^2H_2+H_1H_2^2).
\end{aligned}
$$

This yields $\chi=-162$ and $\int_X c_2H_1=\int_Xc_2H_2=36$. The
hypersurface is ample, so Lefschetz gives $h^{1,1}=2$, and
$h^{2,1}=83$ follows. The released record is 7884. For a smooth bicubic
on which a group of order nine acts freely, the covering relation would
give $\chi(X/G)=-18$. This implication requires a free action on the
chosen variety. A group order or an invariant polynomial alone does not
establish freeness. [@anderson-cipro; @braun-quotients; @constantin-quotients]

For geometry with $\operatorname{SU}(3)$ holonomy, the Hodge symmetries and
the standard Calabi–Yau threefold vanishings imply
$\chi=2(h^{1,1}-h^{2,1})$. The catalog stores sentinel Hodge values for
products, so numerical agreement with this identity on product rows
does not validate their actual Hodge diamonds.
