# Abstract

py-CIPro connects Python to CIPro, the Wolfram Language library for geometry in products of projective spaces [@anderson-cipro]. It also provides an
interactive atlas of the threefold configurations in the released
`Cicy3` dataset. The library preserves the upstream evaluation boundary for
symbolic algebra, while the atlas reads values already recorded in the
release. We derive explicit Chern and Hodge checks for the quintic and
bicubic, and audit 7,890 archived configurations. They contain 266 recorded
Hodge pairs, including the sentinel pair $(0,0)$ attached to 22 product
records. All rows satisfy the recorded identity
$\chi=2(h^{1,1}-h^{2,1})$. The archival audit and analytic checks can be
reproduced offline. Numerical execution of the CIPro routines requires an
activated Wolfram kernel.
