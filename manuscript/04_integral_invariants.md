# Integral content of cubic and Chern pairings {#sec:integral_invariants}

The intersection form and the second Chern functional in [@prop:integral_topological_comparison] contain more information than the Hodge pair. He and Candelas compared these forms for complete-intersection threefolds, and He, Yao, and Yau use divisibility invariants of the intersection data in comparisons of Calabi–Yau topology. The census below computes two greatest common divisors on the integral lattice supplied by each CIPro configuration. [@he-candelas-count; @he-yao-yau-topology; @cipro-release]

::: {.definition #def:integral_content title="Content of the ambient cubic and Chern functional"}
Let $L$ be the image of $H^2(A,\mathbb{Z})$ in $H^2(X,\mathbb{Z})/\mathrm{torsion}$, with generators the restrictions of the ambient hyperplane classes $H_i$. For the symmetric trilinear cup product $\mu(x,y,z)=\int_X xyz$ and linear functional $\lambda(x)=\int_X c_2(TX)x$, define $g_3$ and $g_2$ as the nonnegative generators of the ideals

$$
g_3\mathbb{Z}=\big\langle\mu(x,y,z):x,y,z\in L\big\rangle,
\qquad
g_2\mathbb{Z}=\big\langle\lambda(x):x\in L\big\rangle.
$$ {#eq:integral_content_ideals}

These are the ambient-lattice analogues of $d_1$ and $d_p$ in He, Yao, and Yau, equation (2.11) of the published edition. For $c_1(TX)=0$, $\operatorname{ch}_2(TX)=-c_2(TX)$, so the second Chern character has the same evaluation ideal. [@he-yao-yau-topology]
:::

::: {.proposition #prop:integral_content title="Generators and integral changes of basis"}
Set $d_{ijk}=\mu(H_i,H_j,H_k)$ and $T_i=\lambda(H_i)$. Then

$$
g_3=\gcd_{i\leq j\leq k}\lvert d_{ijk}\rvert,
\qquad
g_2=\gcd_i\lvert T_i\rvert .
$$ {#eq:integral_content_gcd}

Every integral combination of the $H_i$ gives a contraction in the indicated ideal by multilinearity, and each displayed entry itself occurs as a contraction. In integral bases related by $H'_i=\sum_a U_{ai}H_a$ with $U\in\mathrm{GL}(L)$, the entries transform as

$$
d'_{ijk}=\sum_{a,b,c}U_{ai}U_{bj}U_{ck}d_{abc},
\qquad
T'_i=\sum_a U_{ai}T_a.
$$ {#eq:integral_content_change_basis}

The new entries generate subideals of the old ones. Applying the same argument to $U^{-1}$ gives the reverse inclusions. The generating-set argument still applies to dependent ambient restrictions. Reversing the choice of orientation negates every evaluation and preserves both nonnegative generators.
:::

::: {.proposition #prop:integral_content_saturation title="Effect of finite-index restriction"}
Let $S$ be the saturation of $L$ in the free second cohomology. This is the intersection of its rational span with $H^2(X;\mathbb Z)/\mathrm{torsion}$. Let $e$ be the exponent of the finite quotient $S/L$, with $e=1$ when $S=L$. For the forms of [@def:integral_content], the content ideals satisfy

$$
\begin{aligned}
e^3 g_3(S)\mathbb Z &\subseteq g_3(L)\mathbb Z \subseteq g_3(S)\mathbb Z,\\
e g_2(S)\mathbb Z &\subseteq g_2(L)\mathbb Z \subseteq g_2(S)\mathbb Z .
\end{aligned}
$$ {#eq:integral_content_saturation}

The right-hand inclusions follow from $L\subseteq S$. For the left-hand inclusions, multiply every input in $S$ by $e$ to put it in $L$. Trilinearity and linearity supply the respective factors $e^3$ and $e$. In rank one, replacing a primitive generator $H$ by $eH$ gives these factors exactly. Thus even a full-rank ambient image needs a primitivity check before one reads its content as that of the full lattice.
:::

::: {.corollary #thm:integral_index_content title="Index congruences for the lattice"}
For $x\in L$ and a line bundle with first Chern class represented by $x$, Riemann–Roch in [@prop:line_index] gives $2\mu(x,x,x)+\lambda(x)\equiv0\pmod{12}$. Consequently

$$
\gcd(2g_3,12)\mid g_2, \qquad
2d_{iii}+T_i\equiv 0\pmod{12},\qquad
d_{iij}+d_{ijj}\equiv 0\pmod{2}\quad(i<j).
$$ {#eq:integral_index_congruences}

The first divisibility follows because $2g_3$ divides the cubic term for every $x$. The pairwise congruence follows by taking $H_i+H_j$ and subtracting the two single-generator congruences. Conversely, the single-generator and pairwise congruences imply integrality for every integral combination of the $H_i$. For $x=\sum_i m_iH_i$, the diagonal contribution reduces using $m_i^3\equiv m_i\pmod 6$. Each pair contributes $6m_im_j(m_i d_{iij}+m_j d_{ijj})$ and is divisible by twelve, and the terms with three distinct indices already carry a factor of twelve. [@hirzebruch-riemann-roch]
:::

## Cubic and Chern divisibility across the archive

The calculation multiplies $[X]=\prod_a D_a$ in the integral ambient ring in [@prop:integration]. Taking exponent complements gives the mixed cubic entries in [@eq:integral_content_gcd], with one complement for each unordered triple of hyperplane indices. The second Chern evaluations are recomputed by [@eq:quadratic_chern]. All {{INTEGRAL_C2_CHECKS}} computed $T_i$ agree with the released values and satisfy the single-generator congruence. All {{INTEGRAL_PAIRWISE_CHECKS}} pairs satisfy the parity congruence. The joint census in [@fig:integral_invariants] groups the {{INTEGRAL_RECORD_COUNT}} non-product records by their exact integer pair, with {{INTEGRAL_CUBIC_CONTENTS}} cubic values and {{INTEGRAL_CHERN_CONTENTS}} Chern values present. [@cipro-release]

Of {{INTEGRAL_HODGE_GROUPS}} distinct Hodge groups, {{INTEGRAL_HODGE_SPLIT}} contain more than one joint content pair. Of {{INTEGRAL_EULER_GROUPS}} distinct Euler groups, {{INTEGRAL_EULER_SPLIT}} split in this way. The largest Hodge group, ${{INTEGRAL_MODAL_HODGE}}$, contributes {{INTEGRAL_MODAL_RECORDS}} records in {{INTEGRAL_MODAL_PAIRS}} joint cells. These counts concern archive presentations and their supplied integral lattices. A comparison of the underlying integral cohomology rings uses the full lattice, as in the example below.

![Cubic and second Chern content in the released CIPro archive. (A) Occupied cells show exact counts for the {{INTEGRAL_PAIR_COUNT}} observed pairs among {{INTEGRAL_RECORD_COUNT}} non-product configurations, with a logarithmic color scale. The axes show the occupied integer levels for each invariant. Empty cells have zero records. (B) Two rank-one ample complete intersections share their Hodge pair and Euler characteristic and have different content on the full integral second cohomology. The degrees and record IDs trace both computations to the release.](../output/figures/integral-invariants.png){#fig:integral_invariants width=100%}

In the dashboard's **Manuscript** view, open **Integral lattice divisibility** and select a census scope. A Hodge pair or Euler characteristic restricts the population, and an occupied cell selects the exact $(g_3,g_2)$ cohort. **Open source records** opens that cohort in the archive. Select a record by ID to inspect its dimensions, degree matrix, and ordered second Chern pairings. **Rerun in Python** rebuilds the content values and congruence checks for that record from its configuration. The shared figure link retains the scope, cell, and record for replay.

Use **Compare the rank-one witnesses** to select their common Hodge group, then choose each archive ID in the comparison panel. Each record reruns on its own defining degrees. The calculation verifies the integer contractions and the link to each archive ID. The weak Lefschetz argument in [@thm:integral_content_witness] identifies those particular ambient generators with the full integral lattices.

## Full-lattice comparison of two rank-one threefolds

::: {.example #thm:integral_content_witness title="Equal Hodge numbers and different integral cup products"}
Records {{INTEGRAL_WITNESS_FIRST_ID}} and {{INTEGRAL_WITNESS_SECOND_ID}} are the configurations $(3,3)$ in $\mathbf{P}^5$ and $(3,2,2)$ in $\mathbf{P}^6$. Their Hodge pair is ${{INTEGRAL_WITNESS_HODGE}}$ and their Euler characteristic is ${{INTEGRAL_WITNESS_EULER}}$. Choose smooth representatives with smooth successive ample cuts. Integral weak Lefschetz gives the isomorphism in degree two at each cut, including the cut from complex dimension four to three. Hence $H^2(X,\mathbb{Z})=\mathbb Z H$, generated by the restricted hyperplane class. The contractions in [@eq:integration] and [@eq:quadratic_chern] become

$$
g_3=\int_X H^3=\prod_a d_a,\qquad
g_2=\int_X c_2(TX)H =
\frac{\sum_a d_a^2-(n+1)}{2}\prod_a d_a
$$ {#eq:integral_ample_contents}

for these configurations, with positive values for both evaluations. They give $({{INTEGRAL_WITNESS_FIRST_CUBIC}},{{INTEGRAL_WITNESS_FIRST_CHERN}})$ and $({{INTEGRAL_WITNESS_SECOND_CUBIC}},{{INTEGRAL_WITNESS_SECOND_CHERN}})$. A graded integral cohomology ring isomorphism would carry a primitive degree-two generator to a primitive generator up to sign, and likewise for the normalized top-degree generator. The absolute cubic evaluations would then agree. The differing cubic contents therefore rule out such a ring isomorphism and a homeomorphism between the smooth threefolds. [@lefschetz-analysis-situs; @cipro-release]
:::

Garbagnati and van Geemen identify both families among examples with Hodge pair $({1},{73})$ in their study of periods and monodromy. The calculation above uses their shared Hodge pair to select the archive records and tests the full cubic lattice directly. [@garbagnati-van-geemen-shimura]
