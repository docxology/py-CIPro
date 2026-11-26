# Install and verify py-CIPro

Install from a source checkout with Python 3.11 or later.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install .
```

Use `CIPro(backend="python")` for the supported exact Python domains. For
example, the quintic hypersurface in projective four-space has Euler
characteristic minus 200:

```python
from py_cipro import CIPro

with CIPro(backend="python") as ci:
    assert ci.property({"DimPs": [4], "Conf": [[5]]}, "Euler", Format="Short") == -200
```

The default `CIPro()` uses an activated Wolfram Engine or Mathematica
installation. Set `WOLFRAM_KERNEL` or pass `kernel=` if discovery cannot
find the executable. `backend="auto"` can start a Wolfram session for
unsupported Python operations. See the [backend and result contracts](python/api.md)
and [activated runtime guide](wolfram-api.md).

## Offline checks

Run the release-preparation and WXF serialization checks with scripted
kernel responses, the archive data checks, and the supported native
dispatch checks:

```sh
python -m unittest discover -s tests -p test_client.py -v
python -m unittest discover -s tests -p test_catalog_data.py -v
python -m unittest discover -s tests -p test_native_dispatch.py -v
```

The Wolfram transport tests use real WXF encoding and scripted responses.
The local archive tests parse the checked release member as data. Native
dispatch checks exercise the Python implementation. Kernel qualification
and live Wolfram tests have a separate [runtime procedure](wolfram-api.md#activated-local-kernel).
The [manuscript build](manuscript.md) specifies the renderer dependencies and
the archive-backed scientific recomputation.
