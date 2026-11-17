# What is in the archived catalog?

The atlas reads the plain-text Wolfram data member `CIProData/Cicy3` of CIPro
v1.0. It checks the release archive digest and parses structured records
without evaluating Wolfram source. Each row carries the upstream ID,
configuration, Hodge values, Euler characteristic, and the source’s
`Favour` and `IsProduct` flags. The ambient dimensions used to display each
configuration follow from its Calabi–Yau row sums, $n_i=\sum_a q_{ia}-1$.
These are derived dimensions for this data model. For a general complete
intersection the ambient dimensions must be supplied separately. [@anderson-cipro; @cipro-release]

The 7,890 catalog IDs are contiguous from 1 to 7,890. Counting records by
the pair $(h^{1,1},h^{2,1})$ gives 266 pairs, with $(9,21)$ the most frequent
at 354 records, followed by $(10,20)$ at 292. The 22 product rows all have
the stored placeholder pair $(0,0)$. The remaining rows give 265 Hodge
pairs, the same count reported in the classical Hodge-number study. Catalog
IDs index configurations, and a pair can collect multiple distinct
configurations. Neither provides a count of topological types. [@candelas-cicy; @green-hubsch; @green-hodge]

The observed Euler range is $[-200,0]$ across 70 values. The median is $-40$,
the mode is $-32$ (613 records), and 52 rows have zero Euler characteristic.
The row-wise equality $\chi=2(h^{1,1}-h^{2,1})$ holds for all stored values.
This check tests a relation within the archived data and does not recompute
Chern classes. The 4,874 rows flagged as favorable reflect the chosen
configuration in this release. Favorability of a presentation and
alternative favorable presentations are different questions. [@cipro-release; @anderson-fibrations]

![Recorded Hodge pairs and Euler frequencies in CIPro v1.0 Cicy3. Left: one point per stored Hodge pair, colored by the logarithmically scaled number of configurations with that pair. The gray cross marks the stored product placeholder. Right: exact count at each recorded Euler value. Quintic and bicubic records are labeled.](figures/cicy3-atlas.png){width=100%}

The dashboard uses the same parsed data. Moving from a point to its
constituent records shows how several configurations can share one pair.
The Euler view groups all matching configurations by the exact stored value.
The record inspector exposes the input matrix and flags so an analyst can
trace an aggregate back to the archived record.
