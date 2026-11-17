"""Serve the CICY3 explorer and the local CIPro method lab."""

import argparse
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
import json
import logging
import re
import subprocess
import sys
from threading import Lock
from urllib.parse import urlsplit

from ._catalog import FUNCTIONS, MODIFICATIONS, PROPERTIES
from ._client import CIPro, EvaluationError, KernelUnavailable
from ._dashboard_examples import EXAMPLES
from ._dashboard_research import (
    ANALYSIS_NAME,
    PDF_NAMES,
    PROVENANCE_NAME,
    STUDY_DATA,
    prepare_research,
    record_selection,
    research_bundle,
    verify_catalog_binding,
)
from ._dashboard_worker import MAX_RESPONSE, run_operation
from ._native import NATIVE_FUNCTIONS, NATIVE_MODIFICATIONS, NATIVE_PROPERTIES
from .catalog import get_catalog

LOGGER = logging.getLogger(__name__)
COMPUTE_PROPERTIES = frozenset({"CIDim", "CY", "Euler"})
MAX_COMPUTE_BODY = 1024
MAX_LAB_BODY = 24 * 1024
NATIVE_TIMEOUT = 25
BACKENDS = ("python", "wolfram", "auto")
METHODS = {"function": sorted(FUNCTIONS), "property": PROPERTIES, "modification": MODIFICATIONS}
NATIVE = {"function": NATIVE_FUNCTIONS, "property": NATIVE_PROPERTIES, "modification": NATIVE_MODIFICATIONS}
STATIC = {
    "/": ("index.html", "text/html"),
    "/styles.css": ("styles.css", "text/css"),
    "/explorer.js": ("explorer.js", "text/javascript"),
    "/method-lab.js": ("method-lab.js", "text/javascript"),
    "/research.js": ("research.js", "text/javascript"),
    "/research.css": ("research.css", "text/css"),
}
RESEARCH_PDFS = {f"/research/{name}": name for name in PDF_NAMES}
RESEARCH_DATA = {f"/research/{name}": name for name in STUDY_DATA}
_RECORD_QUERY = re.compile(r"id=([1-9][0-9]{0,3})\Z")


class RequestError(Exception):
    def __init__(self, status: HTTPStatus, message: str):
        super().__init__(message)
        self.status = status


class DashboardServer(ThreadingHTTPServer):
    def __init__(self, port: int, *, kernel: bool = False):
        self.catalog = get_catalog()
        self.catalog_body = _json_bytes({
            "dataset": self.catalog.dataset,
            "release": self.catalog.release,
            "sha256": self.catalog.sha256,
            "member_sha256": self.catalog.member_sha256,
            "records": [record.summary() for record in self.catalog.records],
        })
        self.default_backend = "wolfram" if kernel else "python"
        self.kernel = CIPro(startup_timeout=60, evaluation_timeout=30)
        self.compute_lock = Lock()
        self.method_body = _json_bytes({"methods": [
            {"kind": kind, "name": name, "native": name in NATIVE[kind],
             "runnable": name in NATIVE[kind], "example": EXAMPLES.get((kind, name))}
            for kind, names in METHODS.items() for name in names
        ]})
        super().__init__(("127.0.0.1", port), DashboardHandler)

    def server_close(self):
        super().server_close()
        with self.compute_lock:
            self.kernel.close()

    def compute(self, record_id: int, properties: list[str], backend: str) -> dict:
        record = self.catalog.record(record_id)
        payload = {
            "kind": "function", "name": "CIProp",
            "args": [{"Conf": record.configuration, "DimPs": record.ambient_dimensions}, properties],
            "options": {"Format": "Medium"}, "select": properties,
        }
        result = self.run(payload, backend)
        return {"source": result["source"], "backend": result["backend"], "properties": result["result"]}

    def research(self):
        try:
            bundle = research_bundle()
            verify_catalog_binding(bundle, self.catalog)
        except (AttributeError, OSError, ValueError, KeyError, TypeError) as exc:
            LOGGER.warning("Research assets could not be verified: %s", exc)
            raise RequestError(HTTPStatus.SERVICE_UNAVAILABLE, "The bundled manuscript assets are unavailable.") from exc
        return bundle

    def research_records(self, query):
        bundle = self.research()
        try:
            return record_selection(query, bundle.analysis, self.catalog, bundle.studies)
        except ValueError as exc:
            raise RequestError(HTTPStatus.BAD_REQUEST, str(exc)) from exc

    def research_rerun(self, payload):
        bundle = self.research()
        try:
            operation = prepare_research(payload, bundle, self.catalog)
        except ValueError as exc:
            raise RequestError(HTTPStatus.BAD_REQUEST, str(exc)) from exc
        return self.run(operation, "python")

    def run(self, payload, backend):
        if not self.compute_lock.acquire(blocking=False):
            raise RequestError(HTTPStatus.CONFLICT, "Another calculation is running. Try again after it finishes.")
        try:
            if backend != "wolfram":
                native = _run_native(payload)
                if "error" not in native:
                    return native
                if native["kind"] != "unsupported" or backend != "auto":
                    status = HTTPStatus.UNPROCESSABLE_ENTITY if native["kind"] == "unsupported" else HTTPStatus.BAD_REQUEST
                    raise RequestError(status, native["error"])
            result = run_operation(self.kernel, payload, "wolfram")
            if len(_json_bytes(result)) > MAX_RESPONSE:
                raise RequestError(HTTPStatus.UNPROCESSABLE_ENTITY, "The result exceeds 512 KiB. Try a smaller selection.")
            return result
        except KernelUnavailable as exc:
            raise RequestError(HTTPStatus.SERVICE_UNAVAILABLE, str(exc)) from exc
        except EvaluationError as exc:
            raise RequestError(HTTPStatus.BAD_GATEWAY, str(exc)[:800]) from exc
        except (ArithmeticError, KeyError, TypeError, ValueError) as exc:
            raise RequestError(HTTPStatus.BAD_REQUEST, str(exc)[:800]) from exc
        finally:
            self.compute_lock.release()


def _run_native(payload):
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "py_cipro._dashboard_worker"],
            input=_json_bytes(payload), capture_output=True, timeout=NATIVE_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        raise RequestError(HTTPStatus.GATEWAY_TIMEOUT, "The Python calculation exceeded 25 seconds. Try a smaller input.") from exc
    except OSError as exc:
        raise RequestError(HTTPStatus.SERVICE_UNAVAILABLE, "Could not start the Python calculation worker.") from exc
    if completed.returncode != 0:
        LOGGER.warning("CIPro Python calculation worker exited with status %s.", completed.returncode)
        raise RequestError(HTTPStatus.BAD_GATEWAY, "The Python calculation worker exited before returning a result.")
    try:
        return json.loads(completed.stdout)
    except ValueError as exc:
        raise RequestError(HTTPStatus.BAD_GATEWAY, "The Python calculation worker returned an invalid response.") from exc


def _json_bytes(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")


class DashboardHandler(BaseHTTPRequestHandler):
    def setup(self):
        self.request.settimeout(10)
        super().setup()

    def do_GET(self):
        try:
            self._check_host()
            target = self._target()
            if target.path in STATIC:
                self._static(target.path)
            elif target.path == "/api/catalog" and not target.query:
                self._reply(HTTPStatus.OK, self.server.catalog_body, "application/json")
            elif target.path == "/api/record":
                match = _RECORD_QUERY.fullmatch(target.query)
                if match is None:
                    raise RequestError(HTTPStatus.BAD_REQUEST, "Give one positive record ID in the query string.")
                self._json(HTTPStatus.OK, asdict(self._record(int(match[1]))))
            elif target.path == "/api/kernel" and not target.query:
                self._json(HTTPStatus.OK, {"enabled": True, "default_backend": self.server.default_backend, "backends": BACKENDS})
            elif target.path == "/api/methods" and not target.query:
                self._reply(HTTPStatus.OK, self.server.method_body, "application/json")
            elif target.path == "/api/research" and not target.query:
                self._reply(HTTPStatus.OK, self.server.research().bodies[ANALYSIS_NAME], "application/json")
            elif target.path == "/api/research/studies" and not target.query:
                self._json(HTTPStatus.OK, self.server.research().studies)
            elif target.path == "/api/research/provenance" and not target.query:
                self._reply(HTTPStatus.OK, self.server.research().bodies[PROVENANCE_NAME], "application/json")
            elif target.path == "/api/research/records":
                self._json(HTTPStatus.OK, self.server.research_records(target.query))
            elif target.path in RESEARCH_PDFS and not target.query:
                name = RESEARCH_PDFS[target.path]
                self._reply(HTTPStatus.OK, self.server.research().bodies[name], "application/pdf", filename=name)
            elif target.path in RESEARCH_DATA and not target.query:
                name = RESEARCH_DATA[target.path]
                self._reply(HTTPStatus.OK, self.server.research().bodies[name], "application/json", filename=name)
            else:
                raise RequestError(HTTPStatus.NOT_FOUND, "Unknown dashboard route.")
        except RequestError as exc:
            self._json(exc.status, {"error": str(exc)})

    do_HEAD = do_GET

    def do_POST(self):
        try:
            self._check_host()
            target = self._target()
            if target.path not in ("/api/compute", "/api/run", "/api/research/rerun") or target.query:
                raise RequestError(HTTPStatus.NOT_FOUND, "Unknown dashboard route.")
            origin = self.headers.get("Origin")
            if origin is not None and origin != f"http://{self.headers['Host']}":
                raise RequestError(HTTPStatus.FORBIDDEN, "Compute requests must come from the dashboard origin.")
            if target.path == "/api/compute":
                record_id, properties, backend = self._read_compute_request()
                self._record(record_id)
                self._json(HTTPStatus.OK, self.server.compute(record_id, properties, backend))
            elif target.path == "/api/run":
                payload, backend = self._read_lab_request()
                self._json(HTTPStatus.OK, self.server.run(payload, backend))
            else:
                self._json(HTTPStatus.OK, self.server.research_rerun(self._read_json(MAX_COMPUTE_BODY)))
        except RequestError as exc:
            self._json(exc.status, {"error": str(exc)})

    def _check_host(self):
        port = self.server.server_port
        if self.headers.get_all("Host") not in ([f"127.0.0.1:{port}"], [f"localhost:{port}"]):
            raise RequestError(HTTPStatus.MISDIRECTED_REQUEST, "Use the dashboard's loopback address.")

    def _target(self):
        try:
            target = urlsplit(self.path)
            if not self.path.startswith("/") or target.scheme or target.netloc or target.fragment:
                raise ValueError
            return target
        except ValueError as exc:
            raise RequestError(HTTPStatus.BAD_REQUEST, "Invalid request target.") from exc

    def _record(self, number):
        try:
            return self.server.catalog.record(number)
        except KeyError as exc:
            raise RequestError(HTTPStatus.NOT_FOUND, f"Cicy3 record {number} was not found.") from exc

    def _read_json(self, maximum):
        if self.headers.get_content_type() != "application/json":
            raise RequestError(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "Use Content-Type: application/json.")
        lengths = self.headers.get_all("Content-Length", [])
        if len(lengths) != 1 or not re.fullmatch(r"[0-9]{1,8}", lengths[0]) or self.headers.get("Transfer-Encoding"):
            raise RequestError(HTTPStatus.LENGTH_REQUIRED, "Provide one valid Content-Length.")
        length = int(lengths[0])
        if length > maximum:
            raise RequestError(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, f"Compute request exceeds {maximum} bytes.")
        try:
            body = self.rfile.read(length)
            if len(body) != length:
                raise ValueError
            return json.loads(body.decode("utf-8"), object_pairs_hook=_unique_fields, parse_constant=_bad_constant)
        except (ValueError, RecursionError) as exc:
            raise RequestError(HTTPStatus.BAD_REQUEST, "Invalid compute JSON.") from exc
        except TimeoutError as exc:
            raise RequestError(HTTPStatus.REQUEST_TIMEOUT, "Compute request body timed out.") from exc
    def _backend(self, payload):
        value = payload.get("backend", self.server.default_backend)
        if not isinstance(value, str) or value not in BACKENDS:
            raise RequestError(HTTPStatus.BAD_REQUEST, "Select backend python, wolfram or auto.")
        return value

    def _read_compute_request(self):
        payload = self._read_json(MAX_COMPUTE_BODY)
        if not isinstance(payload, dict) or set(payload) - {"backend"} != {"record_id", "properties"}:
            raise RequestError(HTTPStatus.BAD_REQUEST, "Supply record_id, properties and an optional backend.")
        record_id, properties = payload["record_id"], payload["properties"]
        if type(record_id) is not int or not 1 <= record_id <= len(self.server.catalog.records):
            raise RequestError(HTTPStatus.BAD_REQUEST, "record_id must be an archived Cicy3 record (1–7890).")
        if (
            not isinstance(properties, list)
            or not 1 <= len(properties) <= len(COMPUTE_PROPERTIES)
            or any(not isinstance(name, str) or name not in COMPUTE_PROPERTIES for name in properties)
            or len(properties) != len(set(properties))
        ):
            raise RequestError(HTTPStatus.BAD_REQUEST, "Select distinct properties from CIDim, CY and Euler.")
        return record_id, properties, self._backend(payload)

    def _read_lab_request(self):
        payload = self._read_json(MAX_LAB_BODY)
        if not isinstance(payload, dict) or set(payload) - {"backend"} != {"kind", "name", "args", "options"}:
            raise RequestError(HTTPStatus.BAD_REQUEST, "Supply kind, name, args, options and an optional backend.")
        kind, name, args, options = (payload[key] for key in ("kind", "name", "args", "options"))
        if not isinstance(kind, str) or kind not in NATIVE or not isinstance(name, str) or name not in NATIVE[kind]:
            raise RequestError(HTTPStatus.BAD_REQUEST, "Select a runnable method from the dashboard catalog.")
        if not isinstance(args, list) or not isinstance(options, dict) or "backend" in options:
            raise RequestError(HTTPStatus.BAD_REQUEST, "Args must be an array and options must be an object.")
        if kind != "function" and len(args) != 1:
            raise RequestError(HTTPStatus.BAD_REQUEST, "Property and modification calls need one geometry argument.")
        if kind == "function" and name == "Data" and (not args or args[0] != "Cicy3"):
            raise RequestError(HTTPStatus.BAD_REQUEST, "Dashboard Data calls read only the bundled Cicy3 dataset.")
        return payload, self._backend(payload)

    def _static(self, path):
        filename, content_type = STATIC[path]
        asset = files("py_cipro").joinpath("web", filename)
        self._reply(HTTPStatus.OK, asset.read_bytes(), content_type)

    def _json(self, status, value):
        self._reply(status, _json_bytes(value), "application/json")

    def _reply(self, status, body, content_type, *, filename=None):
        self.send_response(status)
        media = content_type if content_type == "application/pdf" else f"{content_type}; charset=utf-8"
        self.send_header("Content-Type", media)
        self.send_header("Content-Length", str(len(body)))
        if filename is not None:
            self.send_header("Content-Disposition", f'inline; filename="{filename}"')
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; "
            "img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
        )
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def log_message(self, format, *args):
        pass


def _bad_constant(value):
    raise ValueError(f"Non-finite JSON value {value!r}")


def _unique_fields(pairs):
    fields = dict(pairs)
    if len(fields) != len(pairs):
        raise ValueError("Duplicate compute fields")
    return fields


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765, help="loopback port, or 0 for an available port")
    parser.add_argument("--kernel", action="store_true", help="select the local Wolfram kernel as the dashboard default")
    args = parser.parse_args(argv)
    if not 0 <= args.port <= 65535:
        parser.error("--port must be 0–65535")
    with DashboardServer(args.port, kernel=args.kernel) as server:
        print(f"CIPro dashboard: http://127.0.0.1:{server.server_port}/", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
