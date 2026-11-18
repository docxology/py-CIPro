# Integral content of cubic and Chern pairings {#sec:integral_invariants}

The intersection form and the second Chern functional in [@prop:integral_topological_comparison] contain more information than the Hodge pair. He and Candelas compared these forms for complete-intersection threefolds. He, Yao, and Yau use four divisibility invariants to compare intersection data. The census evaluates these invariants on the integral image supplied by each CIPro configuration, with [@fig:integral_invariants] displaying the joint distribution of tensor and Chern content. [@he-candelas-count; @he-yao-yau-topology; @cipro-release]

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

## Repeated and diagonal evaluations of the cubic form

::: {.proposition #prop:cubic_repeated_diagonal_content title="Contents of repeated and diagonal cubic evaluations"}
The two remaining divisibilities in He, Yao, and Yau's equation (2.11) are the nonnegative generators of the respective evaluation ideals on $L$. Write $P(x)=\mu(x,x,x)$. The finite formulas in terms of the ambient generators are

$$
\begin{aligned}
d_2\mathbb Z
 &=\langle\mu(x,x,y):x,y\in L\rangle\\
 &=\langle d_{iik},\,2d_{ijk}\ (i<j)\rangle,\\
d_3\mathbb Z
 &=\langle P(x):x\in L\rangle\\
 &=\langle d_{iii},\,3(d_{iij}\pm d_{ijj})\ (i<j),\,6d_{ijk}\ (i<j<k)\rangle .
\end{aligned}
$$ {#eq:cubic_repeated_diagonal_content}

For $d_2$, expand $\mu(x,x,y)$ in the $H_i$. Evaluating at $x=H_i$, $y=H_k$ gives $d_{iik}$, and subtracting the two pure evaluations from the evaluation at $x=H_i+H_j$ gives $2d_{ijk}$. For $d_3$, expand $P(\sum_i a_iH_i)$. The pair $i,j$ contributes $3a_i^2a_jd_{iij}+3a_ia_j^2d_{ijj}$. The coefficients $a_i^2a_j$ and $a_ia_j^2$ have equal parity, so this term is an integer combination of the two signed pair generators. Conversely, $P(H_i\pm H_j)-P(H_i)\mp P(H_j)$ recovers the signed pair combinations up to sign, and the alternating three-variable difference of $P$ gives $6d_{ijk}$. Diagonal entries are themselves evaluations. These arguments work for any integral generating set of $L$, including dependent restrictions. [@he-yao-yau-topology; @chandra-enumerating-topology]
:::

The inclusions of evaluation sets give $d_1\mid d_2\mid d_3$, where $d_1=g_3$. The diagonal evaluation ideal sharpens the Riemann–Roch check to $\gcd(2d_3,12)\mid d_p$, with $d_p=g_2$. Every non-product record passes both checks. Replacing $(d_1,d_p)$ with $(d_1,d_2,d_3,d_p)$ increases the number of signatures across {{INTEGRAL_RECORD_COUNT}} rows from {{INTEGRAL_PAIR_COUNT}} to {{REFINEMENT_QUADRUPLES}}. The number of Hodge groups with more than one signature rises from {{INTEGRAL_HODGE_SPLIT}} to {{REFINEMENT_HODGE_SPLIT}} out of {{INTEGRAL_HODGE_GROUPS}}. In all, {{REFINEMENT_HODGE_GROUPS_REFINED}} Hodge groups gain signatures, including groups the pair already distinguished.

Records {{REFINEMENT_WITNESS_FIRST_ID}} and {{REFINEMENT_WITNESS_SECOND_ID}} share Hodge pair $(5,53)$, Euler characteristic $-96$, ambient dimensions, and the archived favorable flag. Their entire Hodge group has one original content pair, $(1,4)$. Their four-part signatures are ${{REFINEMENT_WITNESS_FIRST_SIGNATURE}}$ and ${{REFINEMENT_WITNESS_SECOND_SIGNATURE}}$, separated by $d_2$. The Hodge pair $(4,32)$ supplies a separate $d_3$ comparison. Records 6177 and 6232 share $(d_1,d_2,d_p)=(2,2,4)$ and have $d_3=2$ and $4$, respectively. Both comparisons concern the supplied ambient lattices. The full-lattice obstruction below uses rank-one lattices, for which all three cubic divisibilities equal $|\mu(H,H,H)|$ at a primitive generator $H$.

## Fixed divisor of the ambient line-bundle index

::: {.proposition #prop:ambient_index_fixed_divisor title="A finite formula for the index fixed divisor"}
Let $Q(x)=(2\mu(x,x,x)+\lambda(x))/12$ for $x\in L$, the line-bundle index in [@eq:line_index]. Its fixed divisor $d_\chi$ is the nonnegative generator of the ideal of all its integer values. On the ambient lattice,

$$
d_\chi=\gcd\!\left(d_1,\ \{Q(H_i)\}_i,\
       \left\{\frac{d_{iij}+d_{ijj}}{2}\right\}_{i<j}\right).
$$ {#eq:ambient_index_fixed_divisor}

Write $x=\sum_i k_iH_i$. In the product binomial basis, each coefficient of $Q$ is a forward difference at the origin. It is therefore an integer combination of index values. Each index value is in turn an integer combination of those coefficients because $\binom{k_i}{a}$ is integral at every integer $k_i$. Expanding $k_i^2=k_i+2\binom{k_i}{2}$ and $k_i^3=k_i+6\binom{k_i}{2}+6\binom{k_i}{3}$ gives the linear coefficients $Q(H_i)$ and the mixed quadratic coefficients $(d_{iij}+d_{ijj})/2$. The remaining coefficients are the cubic tensor entries, with $d_{iii}$ occurring also in degree two. Their joint gcd is $d_1$. [@hirzebruch-riemann-roch; @watt-fixed-divisor]
:::

The signed evaluations of $Q$ at $H_i$, $2H_i$, $H_i\pm H_j$, and $H_i+H_j+H_k$ give an independent arithmetic check. The first two yield $Q(H_i)$ and $d_{iii}$ by subtraction. The two signed pair evaluations, after subtracting their pure terms, give the mixed quadratic coefficient and recover $d_{iij},d_{ijj}$ by addition and subtraction. The alternating third difference on three distinct generators gives $d_{ijk}$. The code compares the gcd of these evaluations with [@eq:ambient_index_fixed_divisor] on every non-product record.

The formula gives $d_\chi\mid d_1$. The index identity then gives $d_\chi\mid d_p$. At a prime greater than three, $12$ is invertible modulo every prime power. Consequently $d_\chi$ and $\gcd(d_1,d_p)$ have the same prime powers away from $2$ and $3$. The distinction at these two primes can depend on how the cubic and Chern evaluations combine in the index.

The fixed divisor exceeds one on {{INDEX_DIVISIBILITY_NONUNIT}} of {{INTEGRAL_RECORD_COUNT}} rows. Appending it increases the number of joint signatures from {{REFINEMENT_QUADRUPLES}} to {{INDEX_DIVISIBILITY_SIGNATURES}}. It adds distinctions within {{INDEX_DIVISIBILITY_HODGE_REFINED}} Hodge groups that already had multiple signatures. For example, IDs {{INDEX_DIVISIBILITY_WITNESS_FIRST_ID}} and {{INDEX_DIVISIBILITY_WITNESS_SECOND_ID}} share Hodge pair $(3,47)$, Euler characteristic $-88$, the archived favorable flag, and $(d_1,d_2,d_3,d_p)=(2,2,2,4)$. Their fixed divisors are {{INDEX_DIVISIBILITY_WITNESS_FIRST_VALUE}} and {{INDEX_DIVISIBILITY_WITNESS_SECOND_VALUE}}. The second record has an odd hyperplane index of $5$. The first has only even coefficients in [@eq:ambient_index_fixed_divisor]. This is a comparison of the supplied ambient images.

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
