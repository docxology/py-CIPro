# Reproducing a calculation

Use the official CIPro 1.0 release [2]. The repository records the upstream
commit and SHA-256 of the release archive. The archive supplies the package
source, auxiliary material, data, and examples together. A computational run
also requires an activated Wolfram kernel with the upstream prerequisites
available.

Record the release checksum, the Python wrapper revision, the Wolfram kernel
version, and each CIPro function or dispatcher key together with its arguments
and options. Record the dataset name and record index for dataset-backed
results. For a compact end-to-end check on the quintic in projective
four-space, pass `{"DimPs": [4], "Conf": [[5]]}` and `["CIDim", "Euler"]` to `property`.
The expected complex dimension is 3 and the expected Euler characteristic is
$-200$. The tangent Chern class is $(1+H)^5/(1+5H)$, where $H$ is the hyperplane
class. Its third component is $-40H^3$ and the integral of $H^3$ is 5.
A property check on that example exercises a small part of the
interface. Dataset queries, symmetry routines, and line-bundle computations
need their own fixtures and kernel runs.

This manuscript contains an interface description and verification procedure.
The reference values above are mathematical checks for a future run. Rendering
this document verifies the manuscript build.
