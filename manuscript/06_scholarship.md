# Scope in the literature {#sec:scholarship}

## What the archive counts

Candelas, Dale, Lütken, and Schimmrigk enumerated complete-intersection presentations in products of projective spaces. Green, Hübsch, and Lütken supplied Hodge data. The Oxford distribution makes that lineage accessible in text and Mathematica formats. Gagnon and Ho-Kim subsequently gave an independent enumeration with a different list of representatives. Our statistics use the explicit `Cicy3` member of the versioned CIPro release, whose IDs and encodings fix the units counted in [@sec:catalog]. [@candelas-cicy; @green-hodge; @oxford-cicy3-data; @gagnon-hokim; @cipro-release]

A single smooth threefold can admit several complete-intersection descriptions. Row and column permutations relabel the input, and valid changes of presentation can alter the ambient factors or defining equations. The favorable presentations studied by Anderson and collaborators illustrate this distinction. Their notion that divisor classes descend from an ambient space concerns a chosen embedding. Descent of the Kähler cone is a further property, relevant when using restrictions of ambient hyperplanes to reason about fibrations or flops. [@anderson-cipro; @anderson-fibrations; @brodie-flops]

## When the invariants identify a manifold

For closed, simply connected, smooth spin six-manifolds with torsion-free homology, Wall's classification uses the cubic cup product and the linear functional given by the first Pontryagin class on the integral second cohomology, together with the third Betti number. A comparison must use the same integral basis change for both forms. On a Calabi–Yau threefold, the first Pontryagin class is minus twice the second Chern class. He and Candelas used those data to distinguish CICYs that have equal Hodge numbers. More recent work constructs basis-invariant divisibility data from intersection tensors to support such comparisons. [@wall-six-manifolds; @he-candelas-count; @he-yao-yau-topology]

The polarizations in [@sec:geometry] come from the ambient product. Their cubic and Chern contractions are invariants of a threefold equipped with the specified class. Equal Hodge numbers can accompany different contractions, and a different embedding can supply a different class on the same underlying manifold. A test against Wall's theorem requires integral lattice data and its hypotheses for each candidate. [@wall-six-manifolds; @he-candelas-count; @anderson-fibrations]

## What a cohomology computation certifies

The index in [@eq:line_index] depends on characteristic classes. The dimensions in the long exact sequence can also depend on the coefficients of the defining equation through the rank of a multiplication map. For any fixed charge, rank bounds can be expressed by vanishing minors. A characteristic-zero evaluation at a specified equation can certify that member's rank. A nonzero minor certifies generic rank when it attains an independently justified upper bound. For a finite grid, the open conditions for its finitely many generic ranks can be imposed simultaneously in the irreducible coefficient space. [@hirzebruch-riemann-roch; @constantin-cohomology; @anderson-cohomology-jumping; @wang-hilbert-cohomology]

Constantin and Lukas computed chamber formulas in the generic setting and identified complex-structure dependence as a separate question. Larfors and Schneider studied charge regions on favorable codimension-two CICYs of Picard number two. Wang derives a Hilbert-function treatment of rank defects and distinguishes generic statements in a fixed charge from very general statements across infinitely many charges. The specified bicubic experiment in [@sec:bundles] records the chosen equation and its finite charge set, which are part of its evidence. [@constantin-cohomology; @larfors-schneider-cohomology; @wang-hilbert-cohomology]

## Software and reproducibility

| Work | Computation and input | Evidence relevant here |
| --- | --- | --- |
| CIPro [@anderson-cipro; @cipro-release] | Wolfram Language package for products of projective spaces, configuration associations, defining equations, line bundles, and several bundled archives. | The pinned release supplies the data and an upstream implementation for separate kernel-based comparisons. |
| cohomCalg [@cohomcalg] | Combinatorial line-bundle cohomology on a toric ambient variety. | Ambient cohomology supplies terms in a restriction calculation, which can still require equation-dependent maps. |
| CYTools [@cytools] | Topological computations for Calabi–Yau hypersurfaces in toric varieties, with polytope and triangulation input. | A complementary computational setting for characteristic classes and intersection data. |
| py-CIPro | Python dispatch for a documented subset, a callable Wolfram path, and a dashboard backed by the bundled text archive. | Reproducible checks cover specific inputs and the source data behind the figures. |
: Research software considered here and the inputs on which the cited computations operate. {#tbl:scholarship_software}

Reproduction begins with the form of evidence required for the claim. A dataset summary needs the release member and grouping rules. A cohomology audit needs its defining equations, field, charge, and rank method. A backend comparison needs corresponding inputs and an identified executable at both ends. The manifest and verification procedures in [@sec:evidence] preserve the information needed to repeat the measurements in this paper. [@anderson-cipro; @cipro-release; @template-renderer]
