# Dashboard and method lab

Install py-CIPro and launch its local dashboard.

```sh
python -m pip install .
py-cipro-dashboard
```

Open [http://127.0.0.1:8765/](http://127.0.0.1:8765/). Use `--port 8765` to select a port. The dashboard listens on loopback and serves the original release's `Cicy3` archive and the native Python methods offline.

## Select a compute backend

The **Compute backend** selector applies to the record inspector and **Method lab**.

| Choice | Execution |
| --- | --- |
| **Python** | Default. Uses the native implementations with SymPy and exact arithmetic. Each operation applies its documented input domain. |
| **Wolfram** | Calls the released CIPro package in a local Wolfram kernel. An activated kernel must be available. Set `WOLFRAM_KERNEL` to its executable path when automatic discovery fails. |
| **Auto** | Tries Python first. An unsupported native operation or input domain can trigger a Wolfram call using the original structured input. Argument and computation errors remain errors. |

`py-cipro-dashboard --kernel` sets the initial selection to Wolfram. Wolfram starts on the first call that needs it. The results identify the backend that produced the value, including the backend selected by Auto. The Wolfram selector targets a local kernel. [Python API](python/api.md) · [Wolfram Language API](wolfram/api.md)

## Recompute an archived configuration

1. Find record **7890** in the archive, the quintic in `P^4`.
2. In **Calculate properties**, select Python and request `CIDim`, `CY`, and `Euler`.
3. Select **Run calculation**. The calculation uses the configuration matrix and ambient dimensions. The expected results are dimension `3`, the Calabi–Yau row-sum check `true`, and Euler characteristic `-200`.

The comparison panel distinguishes calculated results from archived or inferred values. `CY` checks the row-sum condition on the configuration. Checking the smoothness of specific equations is a separate method. [Source and mathematical interpretation](research.md)

## Run an individual method

1. Open **Method lab**. Search for a CIPro name and narrow the catalog by **Method type** or **Availability**.
2. Select an entry and **Load example** to populate its arguments and options. For a native property, **Use selected configuration** copies the archive row's `Conf` and `DimPs` into the arguments. Edit the JSON for your own geometry or parameter choices.
3. Select **Run method**. The result shows the actual backend and source. Numeric vectors and rectangular matrices have visual previews. Inspect nested structures and symbolic results, read **Messages and printed output** when available, or select **Export result JSON** to save the returned payload.

The catalog lists 162 entries. It supplies runnable Python examples for all 88 native functions, 48 native `CIProp` property keys, and 12 native `CIMod` modification keys. The test suite exercises each example through the dashboard decoder, native dispatcher, and result encoder. The language guides give the supported input domains. The 14 Wolfram-only entries remain searchable in the lab, and the concordance gives their calling conventions. [Method concordance](concordance.md)

### Input expressions

Use JSON objects for associations, arrays for sequences, and strings for literal text. The expression tags represent structured symbolic values. For example the following value represents \(x^2+\frac{1}{2}\).

```json
{"$add":[{"$pow":[{"$symbol":"x"},2]},{"$rational":[1,2]}]}
```

| Tag | Value form |
| --- | --- |
| `$symbol` | A symbol name such as `"x"`, with up to 64 ASCII letters or digits beginning with a letter |
| `$indexed` | Name and one to four integer indices, such as `["x",1,0]` |
| `$integer` | Decimal integer as a string, up to 256 digits |
| `$rational` | Integer numerator and nonzero denominator, with `$integer` tags accepted |
| `$add`, `$mul` | An array of one to 64 expressions |
| `$pow` | Base and integer exponent from −64 to 64 |
| `$constant` | `I`, `Pi`, `E`, `All`, `Automatic`, or `None` in the applicable backend |

The dashboard constructs symbolic values from these tags and treats ordinary strings as data. Use a single key in each tag object. Numeric options and arguments can be ordinary JSON values. Results retain exact data such as rational pairs. Integers outside the JavaScript safe integer range use decimal strings inside `{"$integer":"…"}` tags. Symbolic results use `$expression` with a `language` field. To compose new inputs, rebuild the expression with the input tags or use the appropriate language API. [Python API](python/api.md) · [Wolfram Language API](wolfram/api.md)

## Loopback HTTP API

| Route | Purpose |
| --- | --- |
| `GET /api/catalog` | Archived summaries and release metadata |
| `GET /api/record?id=7890` | One archived configuration and its ambient dimensions |
| `GET /api/kernel` | Initial backend and selectable backends |
| `GET /api/methods` | Released method catalog, native availability, dashboard eligibility, and executable examples |
| `POST /api/compute` | Selected `CIDim`, `CY`, and `Euler` properties for one archived record |
| `POST /api/run` | One eligible named method with explicit arguments and options |

```sh
curl -fsS http://127.0.0.1:8765/api/compute \
  -H 'Content-Type: application/json' \
  -d '{"record_id":7890,"properties":["CIDim","CY","Euler"],"backend":"python"}'

curl -fsS http://127.0.0.1:8765/api/run \
  -H 'Content-Type: application/json' \
  -d '{"backend":"python","kind":"property","name":"Euler","args":[{"DimPs":[4],"Conf":[[5]]}],"options":{"Format":"Short"}}'
```

`/api/compute` returns `source`, `backend`, and `properties`. `/api/run` returns `source`, `backend`, and `result`, plus `messages` and `output` arrays when produced. The method request uses `function`, `property`, or `modification` for `kind`. For a public function, `args` contains its positional arguments. For a property or modification key, `args` contains one argument holding the input geometry or association list. Error responses give an `error` message.

Record compute accepts up to 1 KiB of input, and method calls accept up to 24 KiB. Serialized results are capped at 512 KiB. Native calls run in a separate worker with a 25-second timeout. Smaller inputs and narrower queries help keep interactive requests within those bounds.
