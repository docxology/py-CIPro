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

## Exact dimensions on a specified smooth bicubic

The dimension experiment specifies a defining polynomial and evaluates the maps in the hypersurface cohomology sequence. It uses the published dimensions for a generic bicubic as a separate benchmark. Constantin and Lukas give chamber formulas on the charge lattice. Wang connects those generic formulas to maximal rank of the mixed Koszul maps. Rank drops for special defining equations are part of a broader dependence of line-bundle cohomology on complex structure [@constantin-cohomology; @wang-hilbert-cohomology; @anderson-cohomology-jumping].

::: {.definition #def:sparse_bicubic title="Bicubic equation with pure cubes"}
Use coordinates $x_0,x_1,x_2$ and $y_0,y_1,y_2$ on the two projective factors. For the finite computation let $X_A=V(F_A)\subset\mathbb{P}^2\times\mathbb{P}^2$ with
$$
F_A(x,y)=\sum_{i,j=0}^2 A_{ij}x_i^3y_j^3,\qquad
A=\begin{pmatrix}
1&1&1\\
1&2&4\\
1&3&9
\end{pmatrix}.
$$ {#eq:bicubic_sparse_equation}
:::

::: {.lemma #thm:bicubic_smoothness title="Smoothness from the support submatrices"}
If all square minors of $A$ are nonzero, $X_A$ in [@eq:bicubic_sparse_equation] is smooth over $\mathbb{C}$.

*Proof.* For a point $([x],[y])$ write $I=\{i:x_i\ne0\}$ and $J=\{j:y_j\ne0\}$. Both supports are nonempty. Set $u=(x_i^3)_{i\in I}$ and $v=(y_j^3)_{j\in J}$. At a singular point the homogeneous partial derivatives vanish, so
$$
A_{I,J}v=0,\qquad A_{I,J}^{\mathsf{T}}u=0.
$$ {#eq:bicubic_smoothness_kernels}
The submatrix has rank $\min(|I|,|J|)$ by the hypothesis. A full-rank rectangular matrix has a trivial kernel on at least one side, which contradicts $u\ne0$ and $v\ne0$. The supplied matrix has nine nonzero entries, nine nonzero minors of size two, and determinant two. The exact analysis records these determinants.
:::

::: {.proposition #prop:bicubic_koszul_ranks title="Computing dimensions by ranks"}
For $L_{(a,b)}$ on $X_A$, let $S_q=H^q(\mathbb{P}^2\times\mathbb{P}^2,\mathcal O(a-3,b-3))$ and $T_q=H^q(\mathbb{P}^2\times\mathbb{P}^2,\mathcal O(a,b))$. Let $r_q$ be the rank of multiplication by $F_A$ from $S_q$ to $T_q$. The long exact sequence from [@eq:hypersurface_koszul] gives
$$
h^q(X_A,L_{(a,b)})=\dim T_q-r_q+\dim S_{q+1}-r_{q+1},
\qquad 0\le q\le3 .
$$ {#eq:bicubic_dimension_from_rank}
All odd ambient groups are zero by [@eq:ambient_cohomology] and Künneth. The map in degree zero is injective because multiplication by a nonzero polynomial is injective. The map in degree four is surjective by duality on the ambient fourfold. Thus $r_2$ is the sole rank to determine computationally. [@hartshorne-ag; @constantin-cohomology]
:::

To construct the map in degree two, use the monomial basis for $H^0(\mathbb{P}^2,\mathcal O(a-3))$ and the basis of $H^2(\mathbb{P}^2,\mathcal O(b-3))$ dual to monomials of degree $-b$. Index basis terms by pairs of nonnegative exponent triples $(\alpha,\beta)$ with $|\alpha|=a-3$ and $|\beta|=-b$. Multiplication in the first factor raises the exponent. Multiplication in the second factor is the dual of raising it. With $e_i$ the $i$-th unit vector, this summand of the map is
$$
(\alpha,\beta)\longmapsto
\sum_{\substack{0\le i,j\le2\\ \beta_j\ge3}} A_{ij}
(\alpha+3e_i,\beta-3e_j).
$$ {#eq:bicubic_monomial_map}
The other Künneth summand exchanges the projective factors and transposes $A$. The map in [@eq:bicubic_monomial_map] preserves the six exponents modulo three. Grouping source and target by these residues gives independent blocks whose ranks add. The analysis evaluates integer matrices over $\mathbb{Q}$, which gives the same ranks over $\mathbb{C}$. It records both ambient dimensions and the exact rank at each charge. [@constantin-cohomology; @wang-hilbert-cohomology]

::: {.example #thm:bicubic_jump title="A smooth member at a cohomology jump"}
At $(a,b)=(3,-3)$, $S_2$ and $T_2$ each have dimension ten. Only the three pure-cube dual monomials in $S_2$ survive multiplication by $F_A$. Their images are the three columns of $A$ in the pure-cube subspace of $T_2$, so $r_2=3$. For a polynomial $F$ with arbitrary coefficients the same map is the coefficient matrix of the order-three monomials in each factor. The polynomial $\sum_{|\alpha|=3}x^\alpha y^\alpha$ gives the identity matrix and witnesses a nonzero determinant polynomial in those coefficients. The full-rank locus and the smooth locus are nonempty Zariski-open subsets of the irreducible projective space of bicubic sections. Their intersection gives the generic smooth value in this charge. Hence
$$
\begin{aligned}
(h^0,h^1,h^2,h^3)\big(X_A,L_{(3,-3)}\big)&=(0,7,7,0),\\
(h^0,h^1,h^2,h^3)\big(X_{\rm gen},L_{(3,-3)}\big)&=(0,0,0,0).
\end{aligned}
$$ {#eq:bicubic_rank_jump_example}
Both indices equal zero by [@eq:bicubic_index].
:::

## Where the dimensions jump

The calculation gives exact dimensions on $X_A$ at all {{BICUBIC_EXACT_POINTS}} charges in the square from [@fig:line_bundle_cohomology]. It resolves {{BICUBIC_EXACT_UNSUPPORTED_RESOLVED}} charges outside the native dimension dispatch, agrees with all {{BICUBIC_EXACT_SUPPORTED_MATCHES}} supported native vectors, and independently recovers {{BICUBIC_EXACT_INDEX_MATCHES}} native index values by taking the alternating sum of its dimensions. The smooth member has nonzero middle cohomology at {{BICUBIC_EXACT_MIXED_NONZERO}} strictly mixed-sign charges.

::: {.definition #def:bicubic_paired_excess title="Paired excess over the generic dimensions"}
Let $\delta(a,b)$ be $h^1(X_A,L_{(a,b)})-h^1(X_{\rm gen},L_{(a,b)})$, with the generic benchmark from Constantin and Lukas. The groups in degrees zero and three agree across these two cases by [@prop:bicubic_koszul_ranks]. The common index then gives
$$
\delta(a,b)
=h^1(X_A,L_{(a,b)})-h^1(X_{\rm gen},L_{(a,b)})
=h^2(X_A,L_{(a,b)})-h^2(X_{\rm gen},L_{(a,b)}).
$$ {#eq:bicubic_paired_excess}
Equivalently $\delta$ is the generic rank $r_2$ minus the rank for $X_A$. The generic rank is maximal, so $\delta$ is nonnegative. [@constantin-cohomology; @wang-hilbert-cohomology]
:::

There are {{BICUBIC_EXACT_JUMPING_POINTS}} charges with positive paired excess in the tested square. At the largest jump both middle degrees gain {{BICUBIC_EXACT_MAX_PAIRED_EXCESS}} classes. The equality of the gains explains the cancellation along the zero-index slice in [@fig:bicubic_exact]. In particular, [@thm:bicubic_jump] gives an explicit pair of distinct cohomology vectors at the same configuration degree and index. The result depends on the polynomial in [@eq:bicubic_sparse_equation]. The analysis receipt preserves that equation and the rank at each charge so the finite experiment can be reproduced.

![Paired cohomology jumps on the smooth bicubic of [@def:sparse_bicubic]. Panel A maps the excess in each of $H^1$ and $H^2$ over the generic dimensions from [@eq:bicubic_paired_excess]. The nonlinear color scale is inverse-hyperbolic-sine, with its ticks in dimension units. The dashed line is the zero-index slice $b=-a$, and the ring marks the rank witness in [@thm:bicubic_jump]. Panel B shows the two signed middle-degree contributions to the index along the positive-$a$ half of the slice. On this slice $h^0=h^3=0$, so the two bars cancel at every charge.](../output/figures/bicubic-exact.png){#fig:bicubic_exact width=100%}

## Symmetry and enumerative boundaries

Given a finite group acting freely on a smooth compact variety, the quotient is covered by the original variety with degree $|G|$. Thus $\chi(X/G)=\chi(X)/|G|$. For [@thm:example_bicubic], a verified free action of order nine on a smooth invariant bicubic gives $\chi(X/G)=-18$. A projective generator description and an invariant polynomial are data for a freeness test. One must also check fixed loci against the chosen smooth member. The linear and projective group orders can differ because scalar matrices act trivially in projective coordinates. The ambient linear actions classified by Braun and the subsequent quotient Hodge calculations provide the context for this computation [@braun-quotients; @constantin-quotients; @gray-wang-quotients].

The released CIPro package also computes enumerative quantities linked to the mirror-map calculation [@anderson-cipro; @hosono-mirror]. A reproducible calculation preserves the chosen Kähler basis, degree bounds, series truncation, and exact options. The evidence here verifies specific ambient characteristic classes and line-bundle dimensions, and inspects recorded catalog fields. Independent validation of enumerative invariants and general equivariant cohomology requires a different experiment.
