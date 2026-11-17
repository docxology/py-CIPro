# Ways to call a Wolfram kernel

Yes. Wolfram supports a persistent Python-to-kernel session, authenticated cloud evaluation and private HTTP functions, and a separate keyed HTTPS service for Wolfram Language snippets. For the released CIPro package and its datasets, use an activated kernel on the machine running py-CIPro. That machine can be an authorized remote host reached through SSH.

| Route | Prerequisite | py-CIPro integration |
| --- | --- | --- |
| Local Python WXF | An activated Wolfram Engine or Mathematica installation | `CIPro()` starts and owns a persistent `WolframLanguageSession`. This is the full Python interface. |
| Private host over SSH | Same kernel requirement on the host, plus authorized SSH access | Run py-CIPro Python there or tunnel to the bundled JSON explorer API for three selected properties. |
| Wolfram Cloud | A Wolfram account with the required plan, credentials, and permissions | The private CIPro deployment uses `WolframCloudSession` and a typed `APIFunction`. Run the live qualification against your account after deployment. |
| Wolfram Language Computation API | Access to Wolfram's Computation API and its API key | POST a Wolfram Language snippet via HTTPS. The documented contract returns formatted result text and does not specify an installation path for CIPro's package and dataset bundle. |

## Activated local kernel

Set `WOLFRAM_KERNEL` to the executable or give the path directly as `CIPro(kernel=...)`. Use the executable path for your installation. The Wolfram Client also attempts to discover a default installation. Each `CIPro` client retains its Wolfram session, caches, and options until it closes, times out, or loses transport. [Wolfram Engine macOS setup](https://support.wolfram.com/46070) · [Wolfram Client local evaluation](https://reference.wolfram.com/language/WolframClientForPython/docpages/basic_usages.html)

```sh
export WOLFRAM_KERNEL='/absolute/path/to/WolframKernel'
py-cipro-qualify > native-qualification.json
python -m unittest discover -s tests -p 'test_live.py' -v
```

```python
from py_cipro import CIPro, wl

with CIPro() as ci:
    print(ci.evaluate(getattr(wl, "System`$Version")))
    print(ci.property({"DimPs": [4], "Conf": [[5]]}, "Euler")["Euler"])
```

Linux, macOS, and Windows installations can have different executable paths. The Wolfram Client talks to the activated kernel process on the same machine. For one-off shell evaluation, Wolfram also supplies the `wolframscript` command. [Wolfram Client executable paths](https://reference.wolfram.com/language/WolframClientForPython/docpages/basic_usages.html) · [WolframScript command reference](https://reference.wolfram.com/language/ref/program/wolframscript.html)

Wolfram describes its free Community Edition as a pre-production development, demo, and test license. Its FAQ treats APIs used in production as requiring an appropriate license even when internal to an organization, and discusses separate restrictions for organizational or commercial reports. Check the terms of the installation and your intended use. The CIPro software license and the Wolfram kernel license apply independently. [Wolfram Engine FAQ](https://www.wolfram.com/engine/faq/#licensing-and-terms-of-use)

## Private host and explorer HTTP API

On an authorized host with this package installed and a suitably licensed kernel, launch the bundled loopback service. Omit `--kernel` to browse the archive with Python alone.

```sh
export WOLFRAM_KERNEL='/absolute/path/to/WolframKernel'
python -m py_cipro.dashboard --port 8765 --kernel
```

If connecting from another machine, forward the same port on its loopback interface. Keep the SSH host key verification and identity controls of your existing access. Open [the local explorer](http://127.0.0.1:8765/) after starting the tunnel.

```sh
ssh -N -o ExitOnForwardFailure=yes -L 127.0.0.1:8765:127.0.0.1:8765 your-user@your-licensed-host
```

| Endpoint | Purpose |
| --- | --- |
| `GET /api/catalog` | Read the compact released `Cicy3` records and archive provenance. |
| `GET /api/record?id=7890` | Read a selected one-based record and its configuration matrix and ambient dimensions. |
| `GET /api/kernel` | Read whether the process was started with computation enabled. This flag makes no promise that kernel startup or activation will succeed. |
| `POST /api/compute` | Ask the host's Wolfram kernel to evaluate selected properties for an archived `Cicy3` configuration. |

```sh
curl --fail-with-body --silent --show-error 'http://127.0.0.1:8765/api/kernel'
curl --fail-with-body --silent --show-error 'http://127.0.0.1:8765/api/record?id=7890'
curl --fail-with-body --silent --show-error 'http://127.0.0.1:8765/api/compute' \
  -H 'Content-Type: application/json' \
  --data '{"record_id":7890,"properties":["CIDim","CY","Euler"]}'
```

The compute endpoint takes an integer `record_id` from 1 through 7890 and one to three distinct keys from `CIDim`, `CY`, and `Euler`. The JSON object has exactly the two keys shown, within a 1,024-byte request body. The service constructs a new association using only the archived configuration and its inferred ambient dimensions. A successful response contains a `source` string and a `properties` object with the evaluated integers or Booleans. Only one kernel calculation can proceed at a time, and an occupied worker returns HTTP 409. Kernel startup and package load each have a 60-second limit, and an evaluation has a 30-second limit. Errors surface as HTTP failures with JSON details. A failed calculation leaves the archive browseable.

The service listens on `127.0.0.1` and is designed for a trusted local or SSH-forwarded client. The host check permits `localhost` and `127.0.0.1` on the listener port. Compute requests supplying a browser `Origin` must use the same authority. The endpoint has no HTTP authentication for users on that host. Keep the listener on trusted loopback. A public or multi-user deployment would need its own authenticated service design and licensing. For arbitrary inputs, other CIPro calls, and WXF results, run the Python wrapper in an authorized shell on the kernel host.

## Deploy py-CIPro to Wolfram Cloud

Use an existing Wolfram Cloud account with private `APIFunction` deployment and evaluation, outgoing HTTPS to GitHub's release assets during installation, storage for the 27,165,392-byte source archive, and enough evaluation time and memory to import the larger datasets. The largest expanded member, `Cicy4`, is 95,145,932 bytes before the Wolfram kernel constructs its in-memory data. In a signed-in notebook, `CloudAccountData /@ {"DeployedMemoryLimit", "DeployedEvaluationTimeLimit"}` reports the limits on the selected account. Wolfram's introductory Cloud Basic plan excludes organizational use, including group research. An existing plan or site license must cover your intended use. [Wolfram Cloud Basic terms](https://support.wolfram.com/53990) · [Wolfram Cloud file limits](https://support.wolfram.com/12576) · [Cloud evaluation](https://reference.wolfram.com/language/ref/CloudEvaluate.html)

In a private Wolfram Cloud notebook, identify the account using `$UserName` and create a dedicated named key using `GenerateSecuredAuthenticationKey["py-cipro"]`. Its `"ConsumerKey"` and `"ConsumerSecret"` values go into the environment of the Python process on the trusted machine. Keep them out of chat, Git, dashboard/browser state, and logs. The key name and username identify the account and key. The installer needs the key belonging to the deployment owner, and grants that named key access to the private endpoint. [Wolfram authentication key reference](https://reference.wolfram.com/language/ref/GenerateSecuredAuthenticationKey.html) · [Authenticated access to deployed APIs](https://reference.wolfram.com/language/WolframClientForPython/docpages/intro.html#api)

| Variable | Value |
| --- | --- |
| `WOLFRAM_CLOUD_OWNER` | Wolfram Cloud username, as returned by `$UserName`. |
| `WOLFRAM_CLOUD_KEY_NAME` | Name of the secured key, for example `py-cipro`. Required to deploy. |
| `WOLFRAM_CLOUD_CONSUMER_KEY` | Secured key's consumer key. |
| `WOLFRAM_CLOUD_CONSUMER_SECRET` | Secured key's consumer secret. |
| `PY_CIPRO_WOLFRAM_CLOUD_ENDPOINT` | Optional relative cloud object name. Defaults to `py-cipro/v1-0/api`. |

On macOS, one way to stage the values securely is to run the following in your Terminal. The two `security add-generic-password` commands prompt for values. Existing keychain entries can be managed through Keychain Access.

```sh
security add-generic-password -a "$(id -un)" -s py-cipro.wolfram.consumer-key -w
security add-generic-password -a "$(id -un)" -s py-cipro.wolfram.consumer-secret -w
export WOLFRAM_CLOUD_OWNER='your-wolfram-username'
export WOLFRAM_CLOUD_KEY_NAME='py-cipro'
export WOLFRAM_CLOUD_CONSUMER_KEY="$(security find-generic-password -a "$(id -un)" -s py-cipro.wolfram.consumer-key -w)"
export WOLFRAM_CLOUD_CONSUMER_SECRET="$(security find-generic-password -a "$(id -un)" -s py-cipro.wolfram.consumer-secret -w)"
```

Install the package from this checkout and run the deployment and acceptance commands from the environment with the credentials. The deployment fetches the pinned public v1.0 archive directly in Wolfram Cloud, checks its SHA-256, stores it as a private cloud object, and creates a private typed API. The API initializes the actual CIPro Wolfram source for each evaluation. Its headless initialization omits the bundled logo and PDF pre-rendering. The deployed operations are package health, bounded CIProp properties for archived configurations, and the native dataset checks. [CIPro v1.0 release](https://github.com/JamesGray-Physics/CIPro/releases/tag/v1.0) · [Wolfram CloudDeploy](https://reference.wolfram.com/language/ref/CloudDeploy.html)

```sh
python -m pip install .
py-cipro-cloud deploy
py-cipro-cloud status
py-cipro-cloud qualify > cloud-qualification.json
PY_CIPRO_RUN_CLOUD_LIVE=1 python -m unittest discover -s tests -p 'test_cloud_live.py' -v
```

If a deployment timed out or returned an authorization error, check the configured endpoint with `py-cipro-cloud status` and inspect its objects in the owner account before retrying. The installer preserves existing endpoints. An existing private archive is reusable only when its bytes match the release.

Keep the qualification receipt. It records the release digest, cloud kernel identity, checks on the quintic, bicubic and tetraquadric, and independent native reads across all eight release datasets. The known lengths of five datasets are checked against the upstream metadata. Seven members are Wolfram `DumpSave` files. Their digest matching the release certifies the bytes. Native read success on the target cloud kernel establishes platform compatibility separately. A failed native dataset remains visible in the receipt. [Wolfram DumpSave portability](https://reference.wolfram.com/language/ref/DumpSave.html)

Launch the explorer with the same credential environment:

```sh
py-cipro-dashboard --cloud
```

Open the local explorer and select a record. The cloud compute panel sends an allowlisted record ID and selected `CIDim`, `CY`, or `Euler` keys through the local server to the deployed API. The browser receives scalar results and a source label. Credentials are held by the Python server. The archived charts remain usable if the Cloud call fails. Use `--kernel` for a local kernel or omit both flags for archive mode. [Local explorer](http://127.0.0.1:8765/)

## General Wolfram Cloud API examples

Wolfram's Python library can authenticate with an account's secured key. Generate a named secured authentication key through the account or Wolfram Language and supply its consumer key and consumer secret through the environment. The following keeps credentials out of the source and verifies only cloud evaluation of a basic Wolfram expression. [Wolfram Cloud Python workflow](https://reference.wolfram.com/language/workflow/ConnectPythonToTheWolframCloud.html)

```python
import os
from wolframclient.evaluation import SecuredAuthenticationKey, WolframCloudSession
from wolframclient.language import wl

credentials = SecuredAuthenticationKey(
    os.environ["WOLFRAM_CLOUD_CONSUMER_KEY"],
    os.environ["WOLFRAM_CLOUD_CONSUMER_SECRET"],
)
with WolframCloudSession(credentials=credentials) as session:
    if not session.authorized():
        raise RuntimeError("Wolfram Cloud authentication failed")
    print(session.evaluate(wl.Total([1, 2, 3])))
```

The client preserves authentication across requests. Each cloud evaluation uses a fresh engine. Definitions, loaded datasets, and session options from one evaluation are unavailable to the next unless stored and explicitly loaded. Wolfram's cloud plan governs memory and time limits. Evaluation can use cloud credits. Check the account's actual permissions, evaluation limits, and allowance before planning a workflow. [Wolfram Client basic usage](https://reference.wolfram.com/language/WolframClientForPython/docpages/basic_usages.html) · [CloudEvaluate plan limits](https://reference.wolfram.com/language/ref/CloudEvaluate.html) · [Wolfram Cloud Credits](https://www.wolfram.com/cloud-credits/)

### Private Wolfram HTTP function

In your authenticated Wolfram notebook, use `APIFunction` to define typed parameters and a deliberate response format. `CloudDeploy` installs the example at an account-owned private object. Grant the named secured authentication key access to that object, using a dedicated key created under your account. This example verifies the typed API pattern.

```wolfram
obj = CloudDeploy[
    APIFunction[{"n" -> "Integer"}, {#n^2} &, "JSON"],
    CloudObject["api/private/py-cipro-auth-check"],
    Permissions -> "Private"
];
SetPermissions[
    obj,
    SecuredAuthenticationKeys["py-cipro"] -> {"Read", "Execute"}
]
```

Use the same credential object as above and your Wolfram account username (`$UserName`). This call is separate from a general cloud evaluation.

```python
import json
import os

with WolframCloudSession(credentials=credentials) as session:
    response = session.call(
        (os.environ["WOLFRAM_CLOUD_OWNER"], "api/private/py-cipro-auth-check"),
        {"n": 4},
    )
    value = response.get()
    if isinstance(value, (bytes, str)):
        value = json.loads(value)
    assert value == [16]
```

When changing the CIPro cloud deployment, keep the pinned release resources in private cloud objects or on an appropriately licensed Wolfram host. Qualify path setup and initialization within one cloud evaluation, legacy dependencies, required dataset imports, binary dump platform compatibility, messages, time and memory, and the mathematical smoke examples. `IncludeDefinitions` packages Wolfram definitions. The code and dataset files used by the release still need an applicable resource layout. Constrain the deployed CIPro function to typed inputs and operation keys, and keep Wolfram credentials outside the dashboard browser. Use the py-CIPro qualification receipt to establish which dataset reads and calculations have succeeded on the target account. [Wolfram private API documentation](https://reference.wolfram.com/language/WolframClientForPython/docpages/intro.html#api) · [APIFunction reference](https://reference.wolfram.com/language/ref/APIFunction.html) · [Cloud object permissions](https://reference.wolfram.com/language/workflow/SetACloudObjectsPermissions.html)

## Keyed HTTPS computation

Wolfram's separate Wolfram Language Computation API accepts a code snippet in the JSON `code` field at `https://services.wolfram.com/api/cag/v1/WolframLanguageCompute`. It uses an API key in the `Authorization` header and can bound result length and evaluation time with `maxChars` and `timeConstraint`. The response carries result text and a request UUID. Inspect the Wolfram result for failures even when the transport succeeds. This is a possible route for standalone Wolfram Language calculations when you have its access key. It has not been qualified to load CIPro. [Wolfram Language Computation API reference and access instructions](https://www.wolfram.com/apis/documentation/cag/wolfram-language-computation-api/)
