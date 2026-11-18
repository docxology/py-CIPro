# Evidence and reproduction {#sec:evidence}

## Verification by input and mathematical claim

Byte integrity binds the analyses to a specific release asset and text member. Internal consistency tests compare fields in that member, while mathematical recomputation starts from geometry inputs such as matrix degrees or equation coefficients. The two independent integer-ring fixtures in [@tbl:geometry_fixtures] reconstruct Chern contractions and Euler values from ambient dimensions and degrees. Calculating the native line-bundle dimensions and index from fresh associations checks code against the independent derivations in [@thm:example_quintic_bundles] and [@thm:example_bicubic_bundles]. The installed-dashboard suite exercises every native preset through the HTTP request decoder, method dispatch, and result serializer. Each preset tests one valid entry-point execution. [@tbl:verification] records the evidence at each level.

| Evidence | Input | Check and scope |
| --- | --- | --- |
| Release provenance | Official ZIP and `Cicy3` member | Digest checks and raw catalog binding. |
| Archive census | Stored IDs, fields, shapes, and flags | Record-level frequency, consistency, and population checks. |
| Exact geometric fixtures | Two independently characterized regular hypersurfaces | Chern contractions and threefold Hodge/Euler comparisons with the released fields. |
| Euler recomputation | Every released matrix | Exact integration of the cubic in [@eq:archive_euler] gives {{CICY3_TRUNCATED_RING_EULER_MATCHES}} scalar Euler matches. |
| Quadratic Chern audit | Every released matrix and its ordered ambient generators | {{CHERN_AMBIENT_PAIRINGS}} second Chern pairings recovered independently from [@eq:quadratic_chern]. |
| Weighting sensitivity | All {{CICY3_NONPRODUCT_ROWS}} non-product records with the original flag encodings | Exact empirical distributions and symmetric decomposition under the two weights. |
| Integral lattice divisibility | All {{INTEGRAL_RECORD_COUNT}} non-product records and two smooth rank-one configurations | Exact cubic and second Chern content, with Riemann–Roch congruences and a full-lattice comparison in [@sec:integral_invariants]. |
| Fixed divisor of the line-bundle index | The same non-product archive and its four-part cubic signatures | The coefficient formula in [@eq:ambient_index_fixed_divisor] agrees with signed index evaluations on every row. |
| Exact charge sweeps | Quintic charges and a bounded bicubic grid with an explicit smooth equation | Independent quintic dimensions, rational map ranks on the specified bicubic, and exact index throughout both domains. |
| Local HTTP dispatch | One preset for each of the {{NATIVE_TOTAL}} native registry entries | Browser API inputs, Python execution and typed results for every preset, with separate checks for Auto routing. |
: Verification layers in this release. The tests give evidence for their stated fixtures, populations, and interfaces. Live native-versus-Wolfram comparisons require an activated kernel. {#tbl:verification}

Several limitations matter for use. The atlas summarizes one released list of configurations with inherited fields and flags. Its frequency distributions describe those records and should retain their denominators. Configuration-level Chern calculations assume the relevant regular smooth geometry. Particular equations, different field characteristics, and singular strata can require explicit checks. A line-bundle index can agree when the underlying dimensions differ. Across runtimes an exact basis can change while still spanning the same space, so dimension, rank, or equality of spans is often the correct comparison. Native features with symbolic growth bounds are documented in the concordance. Wolfram-only methods and the other bundled data formats require the original execution path [@anderson-cipro; @cipro-release; @wolfram-dump].

## Release identity and reproducible entry points

The package is **{{PACKAGE_NAME}} {{PACKAGE_VERSION}}**, with Python requirement `{{PYTHON_REQUIRES}}` and license `{{PACKAGE_LICENSE}}`. The manuscript source revision is `{{SOURCE_SHORT_COMMIT}}`. The upstream CIPro tag {{UPSTREAM_TAG}} resolves to `{{UPSTREAM_SHORT_COMMIT}}`. The separate GitHub release asset used for the calculations has SHA-256 beginning `{{ARCHIVE_SHORT_SHA256}}`, and the `Cicy3` member hash begins `{{CICY3_MEMBER_SHORT_SHA256}}`. The machine-readable data give the full digests and analysis counts. The build injects the software identity, registry counts, and numerical summaries at render time. [@cipro-release; @template-renderer]

| Workflow | Reproduction entry point |
| --- | --- |
{{SCRIPT_TABLE_ROWS}}
: Reproduction entry points from the project source and package metadata. The manuscript build guide gives the pinned environment, artifact paths, and complete rendering procedure. {#tbl:reproduction_entry_points}

`docxology/template` {{TEMPLATE_VERSION}} assembles the manuscript from the section sources, bibliography, and generated figures. Its formalism filter numbers the definitions, propositions, examples, and lemmas through stable labels. The linkable figure and equation references reuse those source identifiers across reordering. The build records source and rendered artifact hashes for checking the final PDF against the inputs [@template-renderer].

For a calculation needed in subsequent work, retain the package and release revisions, backend, runtime, original inputs and options, actual result, and messages. When using an archive row, include its ID, dataset digest, and subset filters. Random equations require their concrete coefficients or a seed together with the generator and version. Preserve WXF and Wolfram version for kernel-native symbolic results. These records allow the same case to be replayed even when later versions extend native dispatch or change the representations of intermediate values.

## Requirements for extending the comparisons

The archive audits can extend to additional catalogues by retaining the grouping keys, class conventions, and denominators used in each calculation. The charge-grid experiment can extend to other specified equations by replacing the multiplication map and checking smoothness and rank over the new coefficient field. A cross-backend comparison requires an identified Wolfram kernel and corresponding native fixtures. [@anderson-cipro; @cipro-release]
