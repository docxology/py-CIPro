# Interface

The original CIPro package and its mathematical conventions are described by
Anderson et al. [1]. CIPro represents a geometric object by a Wolfram Language
association. Alongside a configuration matrix, an association can carry
derived invariants, symmetry data, or charges specifying a sum of line bundles.
A caller can pass such records between routines in the same kernel session.

The Python entry point `call` dispatches by exact CIPro export name. The
`property` and `modify` entry points route named operations through CIPro's
`CIProp` and `CIMod` dispatchers. CIPro resolves prerequisite properties,
interprets options, and evaluates the selected routines in the kernel. This
boundary covers data queries, configuration and intersection calculations,
characteristic classes, symmetry operations, and line-bundle computations.

The Wolfram Client Library transmits expressions in Wolfram Expression Format
(WXF). Wolfram heads and symbols in symbolic results carry mathematical
information. Preserve those expressions when returning them to CIPro. Interactive
help, notebook display, and front-end actions can have different behavior in a
headless kernel from ordinary computation.
