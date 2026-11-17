# Exact line-bundle experiments {#sec:bundles}

::: {.definition #def:line_bundle title="Ambient-induced line bundle and index"}
For $\mathbf{k}\in\mathbb{Z}^m$, write $L_{\mathbf{k}}=\mathcal{O}_A(\mathbf{k})|_X$ with first Chern class $\ell=\sum_i k_iH_i|_X$. The sheaf cohomology dimensions are $h^q(X,L_{\mathbf{k}})=\dim_{\mathbb C}H^q(X,L_{\mathbf{k}})$. Their alternating sum is the holomorphic Euler characteristic $\chi(X,L_{\mathbf{k}})$.
:::

The single-column charge $\mathbf{k}$ fits into the `LBS` matrix, where each additional column denotes another line-bundle summand. Direct sums add dimensions and indices. Tensor products add charges for each pair of summands, and exterior powers add charges across distinct summands. These operations combine integer charge vectors before evaluating any cohomology [@anderson-cipro].

## Koszul terms and what they determine

For a regular hypersurface of divisor class $D$, restriction of a bundle fits into the sequence
$$
0\longrightarrow\mathcal{O}_A(\mathbf{k}-\mathbf{q})
 \xrightarrow{\ \cdot p\ }\mathcal{O}_A(\mathbf{k})
 \longrightarrow i_*L_{\mathbf{k}}\longrightarrow0,
\qquad \mathbf{q}=(q_i),
$$ {#eq:hypersurface_koszul}
where $i:X\hookrightarrow A$ and $p$ is the defining equation. If there are several regular equations, the sequence is replaced by the Koszul resolution with terms $\mathcal{O}_A(\mathbf{k})\otimes\wedge^jN^\vee$, where $N=\bigoplus_a\mathcal{O}_A(D_a)$ on $A$. By projective-space line-bundle cohomology and Künneth, the dimensions of the ambient terms are calculated from
$$
h^q\bigl(\mathbb{P}^n,\mathcal{O}(s)\bigr)=
\begin{cases}
\binom{s+n}{n} & q=0,\ s\ge0,\\
\binom{-s-1}{n} & q=n,\ s\le -n-1,\\
0 & \text{otherwise},
\end{cases}
\quad n\ge1.
$$ {#eq:ambient_cohomology}

When nonzero terms occupy compatible columns and degrees, the resulting maps determine the dimensions on $X$. The ranks can depend on the coefficients of the defining equations. A vanishing argument or explicit map calculation can be necessary in addition to the dimensions in [@eq:ambient_cohomology]. The native dimension dispatch certifies specific cases, including regular complete intersections in one projective space and multiprojective twists whose relevant ambient terms, or their duals, are acyclic above degree zero. The Python library also supports exact map and basis calculations for prepared inputs in a documented domain. Published cohomology formulas on selected CICYs give complementary information [@hartshorne-ag; @bott-homogeneous; @constantin-cohomology; @anderson-cipro].

::: {.proposition #prop:line_index title="Threefold line-bundle index"}
For a smooth Calabi–Yau threefold as in [@thm:hodge_euler] and the line bundle of [@def:line_bundle], Hirzebruch–Riemann–Roch gives
$$
\chi(X,L_{\mathbf{k}})
 =\frac{1}{6}\int_X \ell^3+\frac{1}{12}\int_X c_2(TX)\ell
 =\frac{1}{6}\sum_{i,j,k}d_{ijk}k_i k_j k_k
   +\frac{1}{12}\sum_i c_{2,i}k_i .
$$ {#eq:line_index}
:::

The degree-three part of $\operatorname{ch}(L)\operatorname{Td}(TX)$ is $\ell^3/6+c_2(TX)\ell/12$ when $c_1(TX)=0$. Substitution of [@prop:integration] yields [@eq:line_index]. The index is an independent invariant of the bundle class. Individual cohomology dimensions contain additional information. On a threefold, Serre duality for $K_X\simeq\mathcal{O}_X$ gives $h^q(X,L_{\mathbf{k}})=h^{3-q}(X,L_{-\mathbf{k}})$ and reverses the sign of the index [@fulton-intersection; @anderson-cipro].

## Quintic sweep and bicubic domain

::: {.example #thm:example_quintic_bundles title="Independent dimensions on the quintic"}
Define $B(s)=\binom{s+4}{4}$ for $s\ge0$ and $B(s)=0$ otherwise. On the quintic, [@eq:hypersurface_koszul] and ambient vanishing give
$$
h^0(X,L_k)=B(k)-B(k-5),\qquad
h^1=h^2=0,\qquad h^3(X,L_k)=h^0(X,L_{-k}).
$$ {#eq:quintic_bundles}
By [@thm:example_quintic] and [@eq:line_index], the index is $(5k^3+25k)/6$. At $k=0$ both $h^0$ and $h^3$ equal one, so the index is zero.
:::

::: {.example #thm:example_bicubic_bundles title="Index on the bicubic and an acyclic twist"}
By [@thm:example_bicubic], the integer index at charges $(a,b)$ is
$$
\chi(X,L_{(a,b)})=\tfrac{3}{2}(a^2b+ab^2)+3(a+b).
$$ {#eq:bicubic_index}
At $(1,0)$ the first bundle of [@eq:hypersurface_koszul] is $\mathcal{O}_A(-2,-3)$, which is acyclic by [@eq:ambient_cohomology], and the second term is $\mathcal{O}_A(1,0)$ with three sections. Thus $(h^0,h^1,h^2,h^3)=(3,0,0,0)$. At $(1,-1)$ both ambient terms are acyclic and all four groups vanish.
:::

The analysis in [@fig:line_bundle_cohomology] compares {{QUINTIC_CHARGE_POINTS}} fresh native `CohLBS` calls on the quintic to [@eq:quintic_bundles] and checks the alternating sum against [@eq:line_index]. For the bicubic it checks native `IndLBS` against [@eq:bicubic_index] across the entire {{BICUBIC_GRID_SIZE}}-point grid, together with Serre duality and index consistency for the supported dimension results. There are {{BICUBIC_SUPPORTED}} native dimension outcomes: {{BICUBIC_H0_ONLY}} with $H^0$ only, {{BICUBIC_H3_ONLY}} with $H^3$ only, and {{BICUBIC_ACYCLIC}} acyclic. The {{BICUBIC_UNSUPPORTED}} remaining charges are reported as unsupported, with no inferred dimension. The origin illustrates the difference between implementation scope and theorem scope. The dispatcher reports it as unsupported in this grid, even though smoothness, connectedness, weak Lefschetz, and Serre duality determine $(1,0,0,1)$ for the structure sheaf.

![Independent line-bundle tests and native cohomology domains. The quintic panel plots $h^0$ and $-h^3$ on a symmetric logarithmic scale for $|k|\le{{QUINTIC_CHARGE_LIMIT}}$. They agree with independent binomial counts, with the two intermediate dimensions zero throughout and the index shown by the dashed curve. The bicubic panel classifies native results for integer pairs with $|a|,|b|\le{{BICUBIC_CHARGE_LIMIT}}$. Circles and triangles indicate $H^0$ and $H^3$ only, and grow with the dimension on a log scale. Squares mark acyclic results and crosses mark unsupported inputs. The separately computed index is verified on the entire grid.](../output/figures/line-bundle-cohomology.png){#fig:line_bundle_cohomology width=100%}

## Symmetry and enumerative boundaries

Given a finite group acting freely on a smooth compact variety, the quotient is covered by the original variety with degree $|G|$. Thus $\chi(X/G)=\chi(X)/|G|$. For [@thm:example_bicubic], a verified free action of order nine on a smooth invariant bicubic gives $\chi(X/G)=-18$. A projective generator description and an invariant polynomial are data for a freeness test. One must also check fixed loci against the chosen smooth member. The linear and projective group orders can differ because scalar matrices act trivially in projective coordinates. The ambient linear actions classified by Braun and the subsequent quotient Hodge calculations provide the context for this computation [@braun-quotients; @constantin-quotients; @gray-wang-quotients].

The released CIPro package also computes enumerative quantities linked to the mirror-map calculation [@anderson-cipro; @hosono-mirror]. A reproducible calculation preserves the chosen Kähler basis, degree bounds, series truncation, and exact options. The evidence here verifies specific ambient characteristic classes and line-bundle dimensions, and inspects recorded catalog fields. Independent validation of enumerative invariants and general equivariant cohomology requires a different experiment.
