# An atlas of archived CICY presentations {#sec:catalog}

## Catalogue records, Hodge pairs, and product entries

The archive is the textual `CIProData/Cicy3` member of CIPro {{UPSTREAM_TAG}}. The loader checks both the release ZIP and member digests and parses the data without evaluating Wolfram source code. It validates the ID sequence, matrix shape, inferred ambient dimensions, and the stored Euler relation. The archive carries one row per published presentation, with the matrix and IDs alongside `H11`, `H21`, `Euler`, `Favour`, and `IsProduct` [@cipro-release; @candelas-cicy]. Its display dimensions $n_i=\sum_aq_{ia}-1$ are inferred by the Calabi–Yau row equation in [@prop:adjunction]. This makes a row-sum equality calculated on those inferred dimensions an internal consistency check. A general user-supplied configuration needs its ambient dimensions as separate input.

::: {.definition #def:atlas_population title="Units counted by the atlas"}
A **presentation count** weights every released configuration ID once. A **non-product Hodge-pair count** weights every distinct stored pair $(h^{1,1},h^{2,1})$ once after omitting the rows flagged `IsProduct`. A pair's **multiplicity** is the number of non-product IDs with that pair.
:::

There are {{CICY3_RECORDS}} released rows. The {{CICY3_PRODUCT_ROWS}} product rows carry the stored placeholder $(0,0)$ and contribute $\chi=0$ to the presentation-level Euler distribution. The remaining {{CICY3_NONPRODUCT_ROWS}} rows contribute {{NONPRODUCT_HODGE_PAIR_COUNT}} distinct Hodge pairs. The historical classification and Hodge computation give the lineage of the records. The Oxford distribution and CIPro release are separate data sources, and the present denominators bind to the latter [@candelas-cicy; @green-hodge; @oxford-cicy3-data; @cipro-release].

An individual Hodge pair fixes the Calabi–Yau threefold Euler number under the hypotheses of [@thm:hodge_euler]. Comparing diffeomorphism types of six-manifolds requires additional information, including integral cubic and Pontryagin data under the relevant classification hypotheses. A multidegree matrix also specifies a presentation, which matters when selecting an ambient basis. The census keeps distinct row IDs even when they share a Hodge pair [@wall-six-manifolds; @he-candelas-count].

## Euler frequencies and concentration across Hodge pairs

[@fig:cicy3_atlas] plots the distinct non-product Hodge pairs with their frequencies and displays the Euler counts for the whole archive. The archive has {{EULER_VALUE_COUNT}} distinct Euler values, from ${{EULER_MIN}}$ to ${{EULER_MAX}}$. The median is ${{EULER_MEDIAN}}$, and the mode ${{EULER_MODE}}$ appears in {{EULER_MODE_COUNT}} records. Of the {{EULER_ZERO_COUNT}} zero records, {{NONPRODUCT_ZERO_EULER}} are non-products. The stored fields satisfy [@eq:hodge_euler] arithmetically on all {{EULER_IDENTITY_CHECKS}} records, including the placeholder rows. The degree matrices independently give {{CICY3_TRUNCATED_RING_EULER_MATCHES}} exact scalar Euler matches by [@eq:archive_euler].

![Hodge coordinates and the discrete Euler distribution. (A) Each point is one of {{NONPRODUCT_HODGE_PAIR_COUNT}} recorded pairs among {{CICY3_NONPRODUCT_ROWS}} non-product presentations. Color and marker area give the record multiplicity on a logarithmic scale. The bicubic and quintic identify the independently computed fixtures in [@tbl:geometry_fixtures]. (B) Each bar counts one exact stored Euler value across all {{CICY3_RECORDS}} presentations. The dashed line marks the median. Products contribute only to the zero bar. The archive is treated as a finite census, so the counts have no sampling error bars.](../../output/figures/cicy3-atlas.png){#fig:cicy3_atlas width=100%}

{{SINGLETON_PAIR_COUNT}} of the non-product pairs appear exactly once. The ten largest pair counts cover {{TOP10_PAIR_RECORDS}} presentations, and {{PAIRS_TO_HALF}} pairs suffice to account for at least half the records when ordered by decreasing count. [@fig:cicy3_multiplicity] shows the concentration and the distribution of pair sizes. These sizes determine the weights in [@eq:atlas_measures].

![Concentration of recorded Hodge pairs in the non-product catalog. The cumulative curve ranks pairs by decreasing presentation multiplicity and shows the resulting share of {{CICY3_NONPRODUCT_ROWS}} records against a dashed equal-weight reference. The distribution panel bins the {{NONPRODUCT_HODGE_PAIR_COUNT}} pairs by how many times they occur. Each pair contributes once to that histogram. The figure excludes the product placeholder and uses exact finite-catalog counts.](../../output/figures/cicy3-multiplicity.png){#fig:cicy3_multiplicity width=100%}

## Configuration shape and the archived favorability flag

Write matrix shape as $(m,r)$, with one row per ambient factor and one column per equation. [@fig:cicy3_structure] compares this two-dimensional shape distribution with the frequency of the archive's `Favour` flag by ambient factor count. The modal shape is $({{MODAL_AMBIENT_FACTORS}},{{MODAL_CODIMENSION}})$ with {{MODAL_SHAPE_RECORDS}} records. The archive marks {{CICY3_FAVOURABLE_ROWS}} rows favorable, accounting for {{FAVOURABLE_NONPRODUCT_PERCENT}} of the non-product records. The fractions in the figure use the entire non-product subset in each group, including the flagged and unflagged presentations.

Favorability concerns whether ambient divisor classes generate the divisor classes of $X$ in the given presentation. A geometry can admit multiple presentations, and the positive span of the inherited divisors is a separate Kähler-cone question. The comparisons use the released flag as stored for each row [@anderson-fibrations; @gray-wang-quotients].

![Configuration shape and released favorability flags. The shape panel counts all {{CICY3_RECORDS}} presentations by number of ambient factors and number of defining equations. Color shows the cell count on a logarithmic scale. The flag panel groups {{CICY3_NONPRODUCT_ROWS}} non-product presentations by ambient factor count and displays the fraction flagged favorable in each group. The group counts give the denominators. Light gray shape cells denote absence from this release.](../../output/figures/cicy3-structure.png){#fig:cicy3_structure width=100%}

## How the weights change the archive summaries

::: {.definition #def:atlas_measures title="Two measures on the same archive"}
Let $N$ count the non-product rows, $K$ count their distinct Hodge pairs, and $n_p$ be the multiplicity of pair $p$. A non-product row $i$ with pair $p(i)$ receives one of two probability weights.

$$
\pi_{\mathrm{pres}}(i)=\frac{1}{N},
\qquad
\pi_{\mathrm{pair}}(i)=\frac{1}{K\,n_{p(i)}}.
$$ {#eq:atlas_measures}
:::

The first measure selects a presentation uniformly. The second selects a pair uniformly and then chooses one of its presentations uniformly. This gives each pair total mass $1/K$ and retains every row's geometry and flags. Euler characteristic is a function of the Hodge pair, so its cumulative share under equal pair weights is the fraction of pairs at or below the threshold. The pooled favorability share under those weights instead averages the flag fraction within each pair. For either measure, let $G_\pi(x)$ be the cumulative Euler share and let $q_\pi$ be the lower median.

$$
G_\pi(x)=\sum_{i:\,\chi_i\leq x}\pi(i),
\qquad q_\pi=\min\{x\in\{\chi_i\}: G_\pi(x)\geq {\tfrac{1}{2}}\}.
$$ {#eq:atlas_euler_cdf}

The non-product median shifts from ${{ATLAS_PRESENTATION_MEDIAN}}$ to ${{ATLAS_PAIR_MEDIAN}}$ when pairs get equal weight. At $\chi={{ATLAS_MAX_CDF_GAP_EULER}}$, the cumulative shares are {{ATLAS_CDF_PRESENTATION_SHARE}}% for presentations and {{ATLAS_CDF_PAIR_SHARE}}% for pairs. The largest absolute gap is {{ATLAS_MAX_CDF_GAP_PP}} percentage points, computed before rounding either share. Panel A in [@fig:atlas_comparison] shows the full discrete distributions.

The flag also changes across records of the same pair. The archive contains {{ATLAS_ALL_FLAGGED_PAIRS}} uniformly flagged pairs, {{ATLAS_ALL_UNFLAGGED_PAIRS}} uniformly unflagged pairs, and {{ATLAS_MIXED_PAIRS}} pairs with both flag values. The mixed pairs account for {{ATLAS_MIXED_PAIRS_SHARE}}% of distinct non-product pairs. The most common pair, ${{ATLAS_MODAL_PAIR}}$, has {{ATLAS_MODAL_PAIR_FLAGGED}} flagged presentations among {{ATLAS_MODAL_PAIR_COUNT}} and spans {{ATLAS_MODAL_PAIR_FACTOR_RANGE}} ambient factors.

::: {.proposition #prop:atlas_standardization title="Decomposing the pooled flag difference"}
For $s=\mathrm{pres},\mathrm{pair}$, let $w_m^{s}$ be the probability mass at $m$ ambient factors and let $f_m^{s}$ be the flagged share conditional on $m$. Set $\bar f_m=(f_m^{\mathrm{pres}}+f_m^{\mathrm{pair}})/2$ and $\bar w_m=(w_m^{\mathrm{pres}}+w_m^{\mathrm{pair}})/2$. Then

$$
\begin{aligned}
 \sum_m w_m^{\mathrm{pair}}f_m^{\mathrm{pair}}
 -\sum_m w_m^{\mathrm{pres}}f_m^{\mathrm{pres}}
 &=\sum_m (w_m^{\mathrm{pair}}-w_m^{\mathrm{pres}})\bar f_m \\
 &\quad+\sum_m \bar w_m(f_m^{\mathrm{pair}}-f_m^{\mathrm{pres}}).
\end{aligned}
$$ {#eq:atlas_standardization}

Expansion within each $m$ cancels the two cross products. The identity assigns the difference to ambient-factor composition and within-group rates symmetrically [@kitagawa-rates].
:::

Under equal pair weights the pooled flagged share rises from {{ATLAS_PRESENTATION_FLAGGED}}% to {{ATLAS_PAIR_FLAGGED}}%, a change of {{ATLAS_FLAGGED_DIFF_PP}} percentage points. The conditional share falls at ambient factor counts {{ATLAS_RANKS_WITH_DECREASE}}. The change in weights gives {{ATLAS_RANK_COMPOSITION_PP}} points, and the change in within-group rates gives {{ATLAS_WITHIN_RANK_PP}} points through [@eq:atlas_standardization]. The different composition accounts for the direction of the pooled change. These are exact comparisons of two measures on the same finite archive. The last ambient-factor group has {{ATLAS_LARGEST_FACTOR_GROUP_N}} rows, which helps explain the limits of comparisons at the edge of the record distribution.

![Sensitivity of the non-product archive to the unit of counting. (A) Cumulative Euler shares under the two measures. The bracket marks the largest absolute difference on the archived Euler support. (B) Share of total weight at each ambient factor count. (C) Flagged share conditional on ambient factor count under either measure. (D) Ambient composition, within-group, and net changes in the pooled flagged share in percentage points. The complete group denominators and rational weights are preserved in the analysis data.](../../output/figures/atlas-comparison.png){#fig:atlas_comparison width=100%}

In the dashboard, a selected record exposes its degree matrix, dimensions, and flags, linking aggregate atlas marks to inputs for another calculation. The weighted summaries above use the non-product rows of the released threefold census. The upstream distribution also includes fourfolds, alternative presentations, symmetry actions, and model-building data [@anderson-cipro; @gray-cicy4-classification; @gray-cicy4-proceedings; @gray-cicy4-invariants; @candelas-small-hodge].
