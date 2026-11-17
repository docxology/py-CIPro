"""Run small native CIPro qualification cases and emit a JSON receipt."""

import argparse
from datetime import datetime, timezone
import json

from wolframclient.language import wl

from ._client import CIPro, CIProError, KernelUnavailable
from ._release import RELEASE_SHA256, RELEASE_TAG
from .catalog import get_catalog


CASES = (("quintic", 7890, -200), ("bicubic", 7884, -162), ("tetraquadric", 7862, -128))


def qualify(kernel=None) -> dict:
    """Check real kernel calculations against three fixed geometries and the Cicy3 count."""
    receipt = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "release": RELEASE_TAG,
        "release_sha256": RELEASE_SHA256,
        "status": "unavailable",
        "kernel": None,
        "checks": [],
    }
    catalog = get_catalog()
    try:
        with CIPro(kernel=kernel, evaluation_timeout=60) as ci:
            version, platform = ci.evaluate(wl.List(getattr(wl, "$Version"), getattr(wl, "$SystemID")))
            receipt["kernel"] = {"version": version, "system_id": platform}
            for label, record_id, euler in CASES:
                record = catalog.record(record_id)
                geometry = {"Conf": record.configuration, "DimPs": record.ambient_dimensions}
                expected = {"CIDim": 3, "CY": True, "Euler": euler}
                result = ci.property(geometry, list(expected))
                observed = {key: result[key] for key in expected}
                passed = all(type(observed[key]) is type(value) and observed[key] == value for key, value in expected.items())
                receipt["checks"].append({
                    "case": label,
                    "record_id": record_id,
                    "expected": expected,
                    "observed": observed,
                    "passed": passed,
                })
            count = ci.Data("Cicy3", "Length")
            receipt["checks"].append({
                "case": "native Cicy3 length",
                "expected": len(catalog.records),
                "observed": count,
                "passed": type(count) is int and count == len(catalog.records),
            })
    except KernelUnavailable as exc:
        receipt["status"] = "failed" if receipt["kernel"] else "unavailable"
        receipt["error"] = str(exc)
    except (CIProError, KeyError, TypeError, ValueError) as exc:
        receipt["status"] = "failed"
        receipt["error"] = str(exc)
    else:
        receipt["status"] = "passed" if all(check["passed"] for check in receipt["checks"]) else "failed"
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel", help="path to an activated WolframKernel executable")
    args = parser.parse_args(argv)
    receipt = qualify(args.kernel)
    print(json.dumps(receipt, indent=2, default=repr))
    return {"passed": 0, "failed": 1, "unavailable": 2}[receipt["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
