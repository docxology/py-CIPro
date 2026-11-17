"""Run one bounded dashboard computation in its native Python worker."""

from contextlib import redirect_stdout
import json
import sys
import warnings

from ._client import CIPro, EvaluationError
from ._dashboard_research import STUDY_NAMES, recompute_cohomology, recompute_study
from ._dashboard_values import decode, encode
from ._native_errors import NativeUnsupportedError


MAX_RESPONSE = 512 * 1024


def run_operation(client, payload, backend):
    """Decode the original request for exactly one backend and execute it."""
    args = decode(payload["args"], backend)
    options = decode(payload["options"], backend)
    if payload["kind"] != "function":
        args.append(payload["name"])
    head = {"function": payload["name"], "property": "CIProp", "modification": "CIMod"}[payload["kind"]]
    with warnings.catch_warnings(record=True) as emitted:
        detail = client.call_result(head, *args, backend=backend, **options)
    if not detail.success:
        raise EvaluationError(detail)
    value = detail.value
    if "select" in payload:
        value = {name: value[name] for name in payload["select"]}
        for name, child in value.items():
            if type(child) is not (bool if name == "CY" else int):
                raise ValueError(f"CIPro did not return a scalar value for {name}.")
    source = "CIPro v1.0 Python equivalent" if backend == "python" else "CIPro v1.0 Wolfram kernel"
    result = {"backend": backend, "source": source, "result": encode(value)}
    diagnostics = [str(item.message) for item in emitted] + list(map(str, detail.messages))
    output = list(map(str, detail.output))
    if diagnostics:
        result["messages"] = diagnostics
    if output:
        result["output"] = output
    return result


def main():
    try:
        request = json.load(sys.stdin)
        with redirect_stdout(sys.stderr), CIPro(backend="python") as client:
            research = request.get("research") if isinstance(request, dict) else None
            if research == "cohomology":
                result = recompute_cohomology(client, request)
            elif research in STUDY_NAMES:
                result = recompute_study(request)
            else:
                result = run_operation(client, request, "python")
    except NativeUnsupportedError as exc:
        result = {"kind": "unsupported", "error": str(exc)[:800]}
    except (ArithmeticError, KeyError, TypeError, ValueError) as exc:
        result = {"kind": "input", "error": str(exc)[:800]}
    encoded = json.dumps(result, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_RESPONSE:
        encoded = b'{"kind":"input","error":"The result exceeds 512 KiB. Try a smaller selection."}'
    sys.stdout.buffer.write(encoded)


if __name__ == "__main__":
    main()
