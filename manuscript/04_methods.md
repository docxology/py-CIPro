# Validation and extension

## Line bundles, symmetries, and enumerative invariants

A multidegree $\mathbf{k}$ specifies the ambient line bundle
$\mathcal{O}_A(\mathbf{k})$. The Koszul resolution uses exterior powers of
the dual normal bundle to compute its restriction to $X$.
Projective-space cohomology and the Künneth formula give the terms of a
spectral sequence. Its differential ranks can depend on the defining
sections and their coefficients. [@anderson-cipro; @constantin-cohomology]

For an independent bicubic example, twist the hypersurface sequence by
$\mathcal{O}_A(1,0)$. Its first term is $\mathcal{O}_A(-2,-3)$, which is
acyclic since $\mathcal{O}_{\mathbb{P}^2}(-2)$ has no cohomology. Hence
$h^0(X,\mathcal{O}_X(1,0))=3$ and the higher groups vanish, giving a
kernel-independent check for this restriction.

Retain the coordinate and equation representations in symmetry runs, including
the linear and projective group orders. A quotient requires a smooth invariant
member and freeness checks. CIPro’s Gopakumar–Vafa tools incorporate code based
on mirror calculations. Reproducing those enumerative results requires the
Kähler basis, degree bounds, and formal expansion. [@anderson-cipro; @braun-quotients; @constantin-quotients; @hosono-mirror]

## Reproduction record

Reproduce the figure with `scripts/render_figures.py` and the PDF with
the pinned docxology/template workflow. The release ZIP SHA-256 is
`39223db768893c958be776071bcbf86d0ef5692f92e1ab153ef1ce8d3440dd53`.
The `Cicy3` member digest is
`e6e61888281efc7bf4d0d1bd76b62c18c764f1028f17924b9ffe8edce9d6ec17`. [@cipro-release; @template-renderer]

Retain the wrapper commit, runtime version, backend, method, inputs, options,
and result. Include the record IDs and atlas filters where applicable. Keep
generated equations or the seed and generator for randomized workflows.
For Wolfram runs, retain messages and WXF and verify compatibility when
using binary datasets. The offline suite exercises an example for each native
method lab entry. Live cross-backend comparisons require an activated
kernel. [@anderson-cipro; @wolfram-client; @wolfram-dump]
