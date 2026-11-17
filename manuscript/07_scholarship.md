# Scope in the literature {#sec:scholarship}

## Catalogue lineage and the unit of enumeration

Candelas, Dale, Lütken, and Schimmrigk enumerated complete-intersection presentations in products of projective spaces. Green, Hübsch, and Lütken supplied Hodge data. The Oxford distribution makes that lineage accessible in text and Mathematica formats, and Gagnon and Ho-Kim published a separate enumeration. The statistics in [@sec:catalog] count the IDs and use the field encodings of the released CIPro text member. Repeating the census on a different catalogue requires matching its records and checking how it encodes products. [@candelas-cicy; @green-hodge; @oxford-cicy3-data; @gagnon-hokim; @cipro-release]

A single smooth threefold can admit several complete-intersection descriptions. Row and column permutations relabel the input, and changes of presentation can replace the ambient factors or equations. Anderson, Gao, Gray, and Lee report finding new favorable descriptions in 2,946 cases while studying genus-one fibrations. They use these descriptions to compute intersection data in bases of descended divisors. Favorability concerns the descent of divisor classes for a chosen embedding. Their separate Kähler-favorability criterion concerns descent of the whole Kähler cone. That distinction matters for fibration and flop calculations, which use cone information in addition to the divisor lattice. [@anderson-cipro; @anderson-fibrations; @brodie-flops]

## Integral topology and the choice of polarization

::: {.proposition #prop:integral_topological_comparison title="Integral data for oriented six-manifold comparison"}
For an oriented closed smooth six-manifold $X$, let $L_X=H^2(X;\mathbb Z)$ and use the oriented fundamental class $[X]$ to define

$$
\begin{aligned}
\mu_X(u,v,w)&=\langle u\smile v\smile w,[X]\rangle,\\
\rho_X(u)&=\langle p_1(TX)\smile u,[X]\rangle .
\end{aligned}
$$ {#eq:integral_topological_data}

For simply connected spin six-manifolds with torsion-free homology, Wall's classification identifies the oriented diffeomorphism type from $b_3$ and the pair $(\mu,\rho)$ on $L$. Thus, besides equality of $b_3$, it requires one integral isomorphism $\phi:L_X\to L_Y$ satisfying $\mu_X(u,v,w)=\mu_Y(\phi u,\phi v,\phi w)$ and $\rho_X(u)=\rho_Y(\phi u)$ for all $u,v,w$. Jupp extends the classification beyond the spin case for closed, oriented, simply connected six-manifolds with torsion-free homology. [@wall-six-manifolds; @jupp-six-manifolds]
:::

The content ideals in [@prop:integral_content] give direct obstructions to such an isomorphism. Equality of the ideals leaves the simultaneous equivalence question open. He and Candelas used integral intersection and Pontryagin data to distinguish configurations sharing Hodge numbers, establishing a lower bound from a restricted set of ambient embeddings. He, Yao, and Yau study further divisibility invariants and use machine learning to investigate the resulting topology problem. [@he-candelas-count; @he-yao-yau-topology]

On a Calabi–Yau threefold, $p_1(TX)=c_1(TX)^2-2c_2(TX)=-2c_2(TX)$. The quantities in [@eq:polarized_pairings] then give $\mu_X(\ell,\ell,\ell)$ and $-\rho_X(\ell)/2$ at the chosen ambient class $\ell$. This identifies the part of the integral forms that the polarized audit measures. A different embedding can choose a different class on the same manifold, and ambient combinations may span only part of the integral lattice. Comparing full lattices calls for integral generators, including the classes beyond the ambient image where applicable. [@wall-six-manifolds; @he-candelas-count; @anderson-fibrations]

## Rank strata, fixed charges, and generic cohomology

The index in [@eq:line_index] depends on characteristic classes. The dimensions in the long exact sequence can also depend on the defining coefficients through the rank of a multiplication map. A nonzero minor evaluated at a specified equation supplies a rank lower bound there and over the generic coefficient field. An exact rank certificate needs a matching upper bound, supplied by matrix dimensions, vanishing larger minors, or exact row reduction. At charge $(3,-3)$ the middle map is a square coefficient matrix of size ten, so its determinant cuts out the rank-drop locus within the smooth parameter space. On that locus the two middle dimensions both equal the rank deficiency by [@prop:bicubic_koszul_ranks]. [@constantin-cohomology; @anderson-cohomology-jumping; @wang-hilbert-cohomology]

::: {.proposition #prop:finite_grid_maximal_rank title="Simultaneous generic ranks on a finite charge grid"}
Let $U$ be the nonempty smooth locus in the projective parameter space of complex bicubic equations. For each charge $q$ in a finite grid $G$, let $M_q(F)$ be the relevant multiplication map of [@prop:bicubic_koszul_ranks] and $r_q$ its maximum rank on $U$. All these ranks are attained together on the nonempty Zariski-open subset

$$
U_G=\bigcap_{q\in G}\{[F]\in U:\operatorname{rank} M_q(F)=r_q\}.
$$ {#eq:finite_grid_generic_rank}

The entries of each map are linear in the defining coefficients. The complement of the maximum-rank locus is cut out by the $r_q$-minors for $r_q>0$. A zero maximum rank imposes no condition. Each maximum-rank locus is dense in the irreducible space $U$, so their finite intersection is nonempty. [@wang-hilbert-cohomology]
:::

Constantin and Lukas computed chamber formulas in the generic setting, and Larfors and Schneider studied charge regions on favorable codimension-two CICYs of Picard number two. Wang derives a Hilbert-function treatment of rank defects. Passing from a finite charge grid to the whole charge lattice replaces the finite intersection in [@eq:finite_grid_generic_rank] by a countable one. This gives a very general condition over $\mathbb C$. The finite-grid argument establishes openness for the fixed grid. The experiment in [@sec:bundles] records the specified smooth equation and its finite set of tested charges, permitting each rank and dimension to be recomputed at that member. [@constantin-cohomology; @larfors-schneider-cohomology; @wang-hilbert-cohomology]

## Research software and reproducible inputs

| Work | Computation and input | Evidence relevant here |
| --- | --- | --- |
| CIPro [@anderson-cipro; @cipro-release] | Wolfram Language package for products of projective spaces, configuration associations, defining equations, line bundles, and several bundled archives. | The pinned release supplies the data and an upstream implementation for separate kernel-based comparisons. |
| cohomCalg [@cohomcalg] | Combinatorial line-bundle cohomology on a toric ambient variety. | Ambient cohomology supplies terms in a restriction calculation, which can still require equation-dependent maps. |
| CYTools [@cytools] | Topological computations for Calabi–Yau hypersurfaces in toric varieties, with polytope and triangulation input. | A complementary computational setting for characteristic classes and intersection data. |
| py-CIPro | Python dispatch for a documented subset, a callable Wolfram path, and a dashboard backed by the bundled text archive. | Reproducible checks cover specific inputs and the source data behind the figures. |
: Research software considered here and the inputs on which the cited computations operate. {#tbl:scholarship_software}

Replaying a census requires the release member and grouping rules. Replaying a rank calculation requires the defining equations, field, and charge. Replaying a backend comparison also requires the executable identity. [@sec:evidence] records the inputs for these comparisons.
