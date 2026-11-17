# Abstract

py-CIPro connects Python to CIPro, the Wolfram Language library for geometry
in products of projective spaces [@anderson-cipro]. It provides
native Python calculation in documented domains and a dashboard with an
interactive `Cicy3` atlas, a method lab, and a Python, Wolfram, or Auto
backend selector. The dashboard can recompute selected properties from
configuration data and display them alongside archived values.
We derive explicit Chern and Hodge checks for the quintic and bicubic,
and audit 7,890 archived configurations. The archive contains 266 recorded
Hodge pairs, including the sentinel pair $(0,0)$ attached to 22 product
records. All rows satisfy the recorded identity $\chi=2(h^{1,1}-h^{2,1})$.
The archival audit, analytic checks, and supported Python calculations
can run offline. Requests routed to Wolfram use an activated kernel.
