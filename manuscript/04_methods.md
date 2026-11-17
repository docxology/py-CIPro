# Validation and extension

## Line bundles, symmetries, and enumerative invariants

A multidegree vector $\mathbf{k}$ specifies the ambient line bundle
$\mathcal{O}_A(\mathbf{k})$, which can be restricted to $X$. The Koszul
resolution of that restriction uses the exterior powers of the dual
normal bundle. Tensor this resolution by $\mathcal{O}_A(\mathbf{k})$ and
use projective-space cohomology together with the Künneth formula on
$A$. A spectral sequence then computes the cohomology of the restriction.
Ranks of differentials can depend on the defining sections, so an ambient
dimension table alone does not determine every surviving class. Record the
sections and coefficient choices when reproducing these calculations. [@anderson-cipro; @constantin-cohomology]

For an independent bicubic example, twist the hypersurface sequence by
$\mathcal{O}_A(1,0)$. Its first term is $\mathcal{O}_A(-2,-3)$, which is
acyclic since $\mathcal{O}_{\mathbb{P}^2}(-2)$ has no cohomology. Therefore
$h^0(X,\mathcal{O}_X(1,0))=3$ and the higher groups vanish. This checks a
particular restriction from the ambient space through a route independent of
the kernel, without asserting behavior for other line bundles.

Symmetry runs should retain both the ambient-coordinate and equation
representations, and distinguish linear from projective group orders.
A quotient also needs a smooth invariant member and freeness checks.
Likewise, enumerative routines belong to a different evidence path from
archived Hodge numbers. CIPro’s Gopakumar–Vafa tools incorporate code based
on the mirror calculations of Hosono, Klemm, Theisen, and Yau. To reuse an
output, retain the Kähler basis, degree bounds, and selected formal
expansion. [@anderson-cipro; @braun-quotients; @constantin-quotients; @hosono-mirror]

## Reproduction record

Reproduce the atlas figure with `scripts/render_figures.py` and rebuild the
PDF with the pinned docxology/template workflow. The plotted input is the
release ZIP with SHA-256
`39223db768893c958be776071bcbf86d0ef5692f92e1ab153ef1ce8d3440dd53`.
The `Cicy3` member digest is
`e6e61888281efc7bf4d0d1bd76b62c18c764f1028f17924b9ffe8edce9d6ec17`.
Record the wrapper commit, selected record IDs, and any active filters
alongside exported results. [@cipro-release; @template-renderer]

For a computation, record the kernel version, platform, release digest,
full input associations, exact operation and options, result, and
Wolfram messages. Preserve WXF for symbolic results. For workflows that
generate equations or make randomized choices, retain the actual input
polynomials or record the seed and generator in addition to options.
Treat elapsed time and timeout as properties of that particular run.
Other CIPro datasets have separate provenance and may be Wolfram binary
dumps that depend on system compatibility. The analytic fixtures and
archived atlas do not establish runtime behavior of those datasets or
the complete 100-function surface. [@anderson-cipro; @wolfram-client; @wolfram-dump]
