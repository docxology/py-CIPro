# The computational interface

CIPro treats a complete intersection as a Wolfram Language association and
resolves dependencies among requested properties. In the Python interface,
`CIPro.property(geometry, keys)` invokes the upstream `CIProp` dispatcher,
`modify` invokes `CIMod`, and `call` addresses a public symbol by its precise
name. Dictionaries represent associations, lists represent Wolfram lists,
and keyword arguments travel as string-keyed options. The Wolfram Client
Library transports expressions in WXF, a binary format that maintains
expression heads, symbols, and exact rationals. Keep those objects intact
when passing a result to another routine. [@anderson-cipro; @cipro-release; @wolfram-client]

The roles of the operators matter. `CIProp` can extend a geometry with
invariants, characteristic classes, and intermediate quantities. `CIMod`
addresses derived constructions such as normalization, direct sums, and
exterior powers, with an operation-specific result. A record obtained from
the archived catalog can carry precomputed values. A check that aims to
recompute a property should supply only the defining input, such as
`DimPs` and `Conf`, because CIPro can reuse existing keys. For help output
and message-sensitive investigations, use `call_result` to preserve the
kernel diagnostics. [@anderson-cipro; @cipro-release]

A local kernel keeps state, including data caches and options, for the life of
the session. Wolfram Cloud’s authenticated Python API evaluates each request
in a fresh cloud kernel. A cloud implementation would need to load the pinned
package and its dependencies from provisioned storage in each cold evaluation or explicitly deploy a
fixed, protected Wolfram API. Local paths, binary data, and notebook features
require compatibility checks in the destination environment. Cloud deployment remains unverified. [@wolfram-client; @wolfram-api]
