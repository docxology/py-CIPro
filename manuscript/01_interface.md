# The computational interface

CIPro treats a complete intersection as a Wolfram Language association and
resolves dependencies among requested properties. In the Python interface,
`property` addresses a `CIProp` key, `modify` addresses a `CIMod` key,
and `call` addresses a public symbol. The native Python backend calculates
within the documented domains using exact arithmetic and SymPy. With the
Wolfram backend, dictionaries represent associations, lists represent
Wolfram lists, and keyword arguments travel as string-keyed options. The
Wolfram Client Library transports expressions in WXF, a binary format that
preserves expression heads, symbols, and exact rationals. [@anderson-cipro; @cipro-release; @sympy; @wolfram-client]

The roles of the operators matter. `CIProp` can extend a geometry with
invariants, characteristic classes, and intermediate quantities. `CIMod`
addresses derived constructions such as normalization, direct sums, and
exterior powers, with an operation-specific result. A record obtained from
the archived catalog can carry precomputed values. A check that aims to
recompute a property should supply only the defining input, such as
`DimPs` and `Conf`, because CIPro can reuse existing keys. For help output
and message-sensitive investigations, use `call_result` to preserve the
kernel diagnostics. [@anderson-cipro; @cipro-release]

## Browser workflow

The loopback dashboard starts with Python selected. An atlas user can
select a released configuration and recalculate its dimension,
Calabi–Yau row-sum criterion, and Euler characteristic using the
defining degrees and ambient dimensions. The method lab exposes the native
function and dispatch registries for edited inputs. It constructs symbolic
arguments from structured JSON tags for symbols, indexed variables, exact
rationals, arithmetic, and selected constants. Numeric results can be
inspected as values, vectors, or matrices. The result also preserves
structured and symbolic values for inspection and export.

The Wolfram selection uses a local activated kernel. Auto tries Python
first and can retry in Wolfram when the native operation or domain is
unsupported. The browser labels the backend that produced each result.
This label and the input data distinguish a new computation from an
archive lookup and a successful native call from a Wolfram fallback.

A local kernel keeps state, including data caches and options, for the life of
the session. Wolfram Cloud’s authenticated Python API evaluates each request
in a fresh cloud kernel. A cloud implementation would need to load the pinned
package and its dependencies from provisioned storage in each cold evaluation or explicitly deploy a
fixed, protected Wolfram API. Local paths, binary data, and notebook features
require compatibility checks in the destination environment. Cloud deployment remains unverified. [@wolfram-client; @wolfram-api]
