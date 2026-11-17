# Exact geometry from configuration data {#sec:geometry}

::: {.definition #def:configuration title="Regular projective configuration"}
Let $A=\prod_{i=1}^{m}\mathbb{P}^{n_i}$ over $\mathbb{C}$ and let $H_i$ denote the ambient hyperplane classes. A configuration $Q=(q_{ia})$ with nonnegative integer entries specifies $r$ equations: column $a$ gives a section of $\mathcal{O}_A(q_{1a},\ldots,q_{ma})$ with divisor class $D_a=\sum_i q_{ia}H_i$. A regular configuration in this paper means a choice of such sections cutting out a complete intersection $X$ of codimension $r$, with smoothness stated when required.
:::

The Python association encodes the $n_i$ in `DimPs` and the $q_{ia}$ in `Conf`. Dimensions computed from `CIDim` therefore express an expected dimension until the codimension condition is established. Degenerate sections, singular members, and generalized complete intersections defined in stages require separate geometric arguments [@anderson-cipro; @anderson-gcicy].

## Adjunction and ambient coefficient extraction

::: {.proposition #prop:adjunction title="Adjunction and normal bundle"}
For smooth $X$ as in [@def:configuration], the normal bundle splits as $\bigoplus_{a=1}^r\mathcal{O}_A(D_a)|_X$. Its canonical bundle and total Chern class are
$$
\begin{aligned}
K_X &\simeq \mathcal{O}_A\left(
       \left(\sum_a q_{ia}-n_i-1\right)_{i=1}^{m}\right)\big|_X,\\
c(TX) &= \left.\frac{\prod_i (1+H_i)^{n_i+1}}
                              {\prod_a (1+D_a)}\right|_X .
\end{aligned}
$$ {#eq:adjunction}
:::

To derive [@eq:adjunction], the Euler sequence gives the numerator for each projective factor. The tangent-normal sequence divides this total Chern class by that of the split normal bundle. Taking determinants of the dual sequence gives the canonical bundle [@fulton-intersection; @anderson-cipro]. If $\sum_a q_{ia}=n_i+1$ for every row, $K_X$ is trivial. The `CY` result tests this row equality. It cannot determine whether a specified set of equations is smooth, connected, or of expected codimension.

::: {.proposition #prop:integration title="Ambient integration"}
With the Chow grading $\deg H_i=1$ and $d=\dim_{\mathbb C}X$, a homogeneous class $p$ of degree $d$ in the ambient-induced classes satisfies
$$
\int_X p|_X =
[H_1^{n_1}\cdots H_m^{n_m}]\,
p(H_1,\ldots,H_m)\prod_{a=1}^r D_a .
$$ {#eq:integration}
:::

Each regular equation contributes its divisor class to the fundamental cycle. Pushing the restricted integrand into $A$ multiplies it by $[X]=\prod_a D_a$. The ring $\mathbb{Z}[H_1,\ldots,H_m]/(H_i^{n_i+1})$ has a single normalized top monomial, which proves [@eq:integration] and gives a sparse integer algorithm for contractions [@fulton-intersection]. In the implementation, each factor $(1+D_a)^{-1}$ in [@eq:adjunction] only needs powers through degree $d$. Applying [@prop:integration] to $c_d(TX)$ gives the topological Euler characteristic by Chern–Gauss–Bonnet. Applying it to a degree-$d$ product of hyperplane classes gives intersection numbers. For a threefold, these contractions give $d_{ijk}=\int_X H_iH_jH_k$ and $c_{2,i}=\int_Xc_2(TX)H_i$.

::: {.lemma #thm:hodge_euler title="Euler characteristic for the threefold Hodge diamond"}
For a smooth connected projective threefold with trivial canonical bundle and $h^{1,0}=h^{2,0}=0$, Hodge symmetry and Serre duality give
$$
\chi(X)=2(h^{1,1}-h^{2,1}).
$$ {#eq:hodge_euler}
:::

Indeed, $h^{3,0}=h^{0,3}=1$ implies $b_3=2+2h^{2,1}$. The even Betti numbers are $b_0=b_6=1$ and $b_2=b_4=h^{1,1}$, and $b_1=b_5=0$. Their alternating sum proves [@thm:hodge_euler]. The assumptions hold for the smooth ample hypersurfaces used below by weak Lefschetz and adjunction. Product geometries can have different vanishings, as discussed in [@sec:catalog] [@green-hodge; @lazarsfeld-positivity].

## The quintic and bicubic as exact reference cases

::: {.example #thm:example_quintic title="The quintic in projective four-space"}
For $Q=(5)$, $\dim X=4-1=3$ and [@eq:adjunction] expands to $1+10H^2-40H^3$ through degree three. By [@eq:integration], $\int_XH^3=5$. Hence $\int_Xc_2H=50$ and $\chi(X)=-200$. Weak Lefschetz gives $h^{1,1}=1$, so [@eq:hodge_euler] gives $h^{2,1}=101$.
:::

::: {.example #thm:example_bicubic title="The bicubic in a product of projective planes"}
For $Q=(3,3)^{\mathsf T}$ in $\mathbb{P}^2\times\mathbb{P}^2$, the nonzero ambient-induced triples are $\int_X H_1^2H_2=\int_XH_1H_2^2=3$. In the ambient quotient ring,
$$
\begin{aligned}
c_2(TX)&=3H_1^2+9H_1H_2+3H_2^2,\\
c_3(TX)&=-27(H_1^2H_2+H_1H_2^2).
\end{aligned}
$$ {#eq:bicubic_chern}
The classes in [@eq:bicubic_chern] give $c_{2,1}=c_{2,2}=36$ and $\chi(X)=-162$. Weak Lefschetz gives $h^{1,1}=2$, and [@eq:hodge_euler] gives $h^{2,1}=83$.
:::

| Fixture | Record | $(h^{1,1},h^{2,1})$ | $\chi(X)$ | $\int_X c_2H_i$ | Triples |
| --- | ---: | ---: | ---: | --- | --- |
{{FIXTURE_TABLE_ROWS}}
: Reference data checked by an independent integer-polynomial calculation for the quintic and bicubic. Hodge numbers use weak Lefschetz and [@eq:hodge_euler]. The calculated Hodge numbers and Euler characteristics agree with the archived fields. {#tbl:geometry_fixtures}

The integer-ring computation in `scripts/check_intersections.py` checks [@tbl:geometry_fixtures] without invoking the native characteristic-class routines. It asserts agreement with the released Hodge and Euler fields for the two chosen rows. These checks exercise Chern and intersection signs and normalizations before extending the Euler calculation to the complete archive.

## Recovering the Euler characteristic from the cubic power sum

::: {.corollary #thm:corollary_archive_euler title="Cubic power sums for a threefold"}
Suppose $X$ has complex dimension three and $c_1(TX)=0$. Then [@eq:integration] gives
$$
3\chi(X) =
[H_1^{n_1}\cdots H_m^{n_m}]\,
\left(\sum_i(n_i+1)H_i^3-\sum_a D_a^3\right)
\prod_{a=1}^r D_a .
$$ {#eq:archive_euler}
:::

For formal Chern roots $\alpha_j$, Newton's identity reads $p_3=\sum_j\alpha_j^3=c_1^3-3c_1c_2+3c_3$. The power sum is additive for exact sequences, including the ambient Euler sequences and the tangent-normal sequence in [@prop:adjunction]. It therefore gives the cubic in [@eq:archive_euler] when $c_1(TX)=0$. The computation multiplies sparse integer polynomials, discards terms outside the ambient exponent bounds, and checks that the final coefficient is divisible by three. The released Hodge and Euler fields are withheld as inputs to this calculation. Agreement with the archive is checked by record ID after each computation [@fulton-intersection].

## Polarized Chern pairings and the Hilbert polynomial {#sec:chern_audit}

::: {.proposition #prop:quadratic_chern title="Ambient Chern pairings"}
For the regular Calabi–Yau threefold in [@prop:adjunction], let $T_i=\int_X c_2(TX)H_i$. Then

$$
2T_i=[H_1^{n_1}\cdots H_m^{n_m}]\,
H_i\left(\sum_a D_a^2-\sum_j(n_j+1)H_j^2\right)
\prod_a D_a .
$$ {#eq:quadratic_chern}

The second power sum is $p_2=c_1^2-2c_2$. Apply the ambient Euler sequences and subtract the normal-bundle terms. Since $c_1(TX)=0$, the resulting expression is $-2c_2(TX)$. The coefficient formula follows from [@eq:integration]. [@fulton-intersection; @anderson-cipro]
:::

::: {.definition #def:ambient_polarization title="The all-ones polarization"}
Let $\mathcal L=\mathcal O_A(1,\ldots,1)|_X$ and write $\ell=c_1(\mathcal L)$. Its degree and second Chern pairing are

$$
V=\int_X \ell^3,\qquad T=\int_X c_2(TX)\ell=\sum_i T_i .
$$ {#eq:polarized_pairings}

The line bundle $\mathcal L$ is very ample. It is the restriction of the hyperplane line bundle for the Segre embedding of the ambient product.
:::

::: {.corollary #thm:polarized_sections title="Hilbert polynomial at the chosen polarization"}
For a smooth threefold with trivial canonical bundle, Riemann–Roch and Kodaira vanishing give
$$
h^0(X,\mathcal L^{\otimes t})=\chi(X,\mathcal L^{\otimes t})
=\frac{2t^3 V+tT}{12}
\qquad (t\in\mathbb{Z}_{>0}).
$$ {#eq:polarized_sections}

The degree-three term of $\operatorname{ch}(\mathcal L^{\otimes t})\operatorname{Td}(TX)$ gives the polynomial. Ampleness eliminates the higher cohomology at positive powers. See [@prop:line_index] for the unrestricted index. Each $H_i$ also passes the corresponding integral index congruence, $2\int_X H_i^3+T_i\equiv0\pmod{12}$. [@hirzebruch-riemann-roch; @lazarsfeld-positivity]
:::

::: {.corollary #thm:polarized_divisor_euler title="Euler invariants of a smooth polarized divisor"}
For a smooth member $Y$ of the linear system $|\mathcal L|$, its topological Euler characteristic and holomorphic Euler characteristic are

$$
\chi_{\mathrm{top}}(Y)=V+T,\qquad
\chi(Y,\mathcal O_Y)=\frac{2V+T}{12}.
$$ {#eq:polarized_divisor_euler}

Adjunction gives $c_1(TY)=-\ell|_Y$ and $c_2(TY)=(c_2(TX)+\ell^2)|_Y$. Integration over $Y$ gives the first identity, and the Todd genus of the surface gives the second. A general member is smooth by very ampleness and Bertini. Carta, Mininno, and Shukla use the same two contractions on coordinate and ample divisor classes to study divisor Hodge data. The pairing $(V,T)$ in this audit refers to the single all-ones class. [@hirzebruch-riemann-roch; @lazarsfeld-positivity; @carta-mininno-shukla-divisors]
:::

The quadratic audit reconstructs the ordered Chern pairing vector for each configuration using [@eq:quadratic_chern]. The script first multiplies the defining divisor classes in the truncated ambient ring. It then reads the exponent complement needed for each cubic contraction. Only after finding the pairings does it compare them with the released second Chern component. All {{CHERN_MATCHED_RECORDS}} configurations match, for {{CHERN_AMBIENT_PAIRINGS}} ordered pairings. The row-level receipt also records $V$, $T$, and the exact index at $t=1$ for every configuration. The audit's comparison is with the pinned release data. [@cipro-release]

::: {.example #thm:polarized_hodge_collision title="One Hodge pair with different polarized Hilbert data"}
The {{CHERN_MODAL_RECORDS}} non-product archive records at the modal Hodge pair $({{CHERN_MODAL_H11}},{{CHERN_MODAL_H21}})$ give {{CHERN_MODAL_SIGNATURES}} distinct $(V,T)$ values under [@def:ambient_polarization]. For example, record {{CHERN_MODAL_LOW_ID}} has $V={{CHERN_MODAL_LOW_VOLUME}}$, $T={{CHERN_MODAL_LOW_CONTRACTION}}$, and $\chi(X,\mathcal L)={{CHERN_MODAL_LOW_INDEX}}$. Record {{CHERN_MODAL_HIGH_ID}} gives $V={{CHERN_MODAL_HIGH_VOLUME}}$, $T={{CHERN_MODAL_HIGH_CONTRACTION}}$, and $\chi(X,\mathcal L)={{CHERN_MODAL_HIGH_INDEX}}$. This is a comparison of selected polarizations, which depend on the presentations.
:::

![Polarized degrees and Chern pairings from the exact archive audit. (A) Hexagons group {{CICY3_NONPRODUCT_ROWS}} non-product presentations by the degree $V$ and pairing $T$ defined in [@eq:polarized_pairings]. The degree axis and color count are logarithmic. (B) One point per distinct $(V,T)$ within the modal Hodge pair. Marker area and color increase with the number of represented records. The highlighted IDs attain the minimum and maximum index at the chosen polarization in that Hodge group.](../output/figures/chern-audit.png){#fig:chern_audit width=100%}

[@fig:chern_audit] conditions on a Hodge pair to hold fixed the Euler characteristic while comparing the chosen polarizations across records. An isomorphism carrying one chosen polarization to another preserves the Hilbert polynomial in [@eq:polarized_sections]. Its cubic and linear coefficients recover the pair $(V,T)$, so each of the {{CHERN_MODAL_SIGNATURES}} observed pairs corresponds to a distinct Hilbert polynomial. The oriented classification statement for the underlying six-manifold appears in [@prop:integral_topological_comparison].

## The regular-sequence Hilbert series

When the defining polynomials form a regular sequence in the multigraded ambient polynomial ring, the Koszul resolution gives the Hilbert series of its quotient:
$$
\mathrm{Hilb}(\mathbf{t}) =
  \frac{\prod_a(1-\mathbf{t}^{Q_a})}
       {\prod_i(1-t_i)^{n_i+1}},
\qquad
\mathbf{t}^{Q_a}=\prod_i t_i^{q_{ia}}.
$$ {#eq:hilbert}
This follows by adding alternating series of the graded free modules in the resolution. The denominator counts ambient monomials. The numerator implements the degree shifts of the relations. For example, [@eq:hilbert] on the quintic becomes $(1-t^5)/(1-t)^5$. A Hilbert-series coefficient in the specified quotient and the dimension of a sheaf cohomology group answer different questions in general multidegrees. The Koszul terms give a way to compare them under vanishing hypotheses [@anderson-cipro; @constantin-cohomology].
