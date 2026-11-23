"""Deploy and call the private Wolfram Cloud CIPro service."""

import argparse
from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import partial
from hashlib import sha256
from importlib.resources import files
import json
import logging
import os
import re
from threading import Lock
from urllib.parse import urlsplit

import requests
from wolframclient.evaluation import SecuredAuthenticationKey, WolframCloudSession
from wolframclient.exception import AuthenticationException, WolframLanguageException
from wolframclient.language import wl, wlexpr

from ._catalog import DATASETS
from ._release import RELEASE_SHA256, RELEASE_TAG, open_release
from .catalog import RECORD_COUNT
from .qualify import CASES


DEFAULT_ENDPOINT = "py-cipro/v1-0/api"
ENDPOINT_ENV = "PY_CIPRO_WOLFRAM_CLOUD_ENDPOINT"
COMPUTE_PROPERTIES = frozenset({"CIDim", "CY", "Euler"})
EXPECTED_COUNTS = {
    "Cicy3": RECORD_COUNT,
    "Cicy4": 921_497,
    "LBSStandardModels": 322_678,
    "LBSStandardModels202": 202,
    "delPezzo2": 11,
}
_OWNER_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.@+\-]{0,253}\Z")
_SEGMENT = r"[A-Za-z0-9][A-Za-z0-9_.\-]*"
_ENDPOINT_PATTERN = re.compile(rf"py-cipro/(?:{_SEGMENT}/)*{_SEGMENT}\Z")
_KEY_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.\-]{0,79}\Z")
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
_OFFICIAL_HOSTS = frozenset({"www.wolframcloud.com", "account.wolfram.com"})
_SDK_LOCK = Lock()
_SDK_LOGGERS = (
    "oauthlib.oauth1.rfc5849",
    "wolframclient.evaluation.cloud.cloudsession",
    "wolframclient.evaluation.cloud.oauth",
    "wolframclient.evaluation.result",
)
_REMOTE_ERRORS = {
    "invalid_request": "The cloud service rejected the request parameters.",
    "archive_unavailable": "The private CIPro archive could not be read by the cloud service.",
    "archive_integrity": "The cloud copy of the CIPro archive failed integrity verification.",
    "package_extract_failed": "Wolfram Cloud could not extract the requested CIPro files.",
    "package_load_failed": "Wolfram Cloud could not initialize the actual CIPro package.",
    "dataset_load_failed": "CIPro could not load the dataset in this cloud kernel environment.",
    "dataset_schema_failed": "The loaded CIPro dataset did not have the expected native record structure.",
    "properties_failed": "CIPro did not return the requested cloud calculation.",
    "evaluation_timeout": "The Wolfram Cloud computation expired.",
    "scratch_unavailable": "Wolfram Cloud could not prepare temporary files for CIPro.",
    "endpoint_exists": "This private cloud endpoint already exists. Use status to inspect it or deploy to a fresh path.",
    "archive_not_private": "The destination archive does not have the expected private permissions.",
    "archive_download_failed": "Wolfram Cloud could not download the pinned upstream CIPro archive.",
    "archive_store_failed": "Wolfram Cloud could not store the pinned CIPro archive privately.",
    "endpoint_deploy_failed": "Wolfram Cloud could not deploy the private CIPro endpoint.",
    "endpoint_permissions_failed": "Wolfram Cloud could not verify the endpoint permissions for the named key.",
    "cloud_identity_unavailable": "The deployment evaluator could not establish the Cloud owner identity.",
}


class CloudError(RuntimeError):
    """A CIPro cloud failure with a diagnostic safe to show to a dashboard client."""

    code = "cloud_error"


class CloudConfigurationError(CloudError):
    code = "configuration"


class CloudAuthenticationError(CloudError):
    code = "authentication"


class CloudUnavailableError(CloudError):
    code = "unavailable"


class CloudProtocolError(CloudError):
    code = "protocol"


class CloudEvaluationError(CloudError):
    def __init__(self, code):
        self.code = code if isinstance(code, str) and code in _REMOTE_ERRORS else "remote_rejected"
        super().__init__(_REMOTE_ERRORS.get(self.code, "The cloud service rejected the CIPro operation."))


class _PrivateHTTPSession(requests.Session):
    """Bound requests and keep the signed OAuth exchange on the provider origins."""

    def __init__(self, read_timeout):
        super().__init__()
        self.read_timeout = read_timeout

    def request(self, method, url, **kwargs):
        target = urlsplit(url)
        if target.scheme != "https" or target.netloc not in _OFFICIAL_HOSTS or target.fragment:
            raise CloudConfigurationError("Only the official Wolfram Cloud HTTPS endpoints are supported.")
        kwargs["timeout"] = (10, self.read_timeout)
        kwargs["allow_redirects"] = False
        return super().request(method, url, **kwargs)


def _discard_log(_record):
    return False


@contextmanager
def _protected_sdk_call():
    # The SDK can log signed request headers and remote error bodies at debug level.
    # Its token handshake also changes the global logging threshold.
    with _SDK_LOCK:
        loggers = tuple(logging.getLogger(name) for name in _SDK_LOGGERS)
        disable = logging.root.manager.disable
        for logger in loggers:
            logger.addFilter(_discard_log)
        try:
            yield
        finally:
            if logging.root.manager.disable != disable:
                logging.disable(disable)
            for logger in loggers:
                logger.removeFilter(_discard_log)


def _check_http(status):
    if status == 200:
        return
    if status in (401, 403) or (isinstance(status, int) and 300 <= status < 400):
        raise CloudAuthenticationError("Wolfram Cloud denied access. Check the scoped key and private endpoint permissions.")
    if status == 404:
        raise CloudUnavailableError("The private CIPro cloud endpoint could not be found. Check deployment and endpoint path.")
    if status in (402, 408, 429) or (isinstance(status, int) and status >= 500):
        raise CloudUnavailableError(f"Wolfram Cloud could not complete the request (HTTP {status}).")
    raise CloudProtocolError("Wolfram Cloud returned an unexpected HTTP response.")


def _envelope(value):
    if isinstance(value, (bytes, str)):
        try:
            value = json.loads(value)
        except (ValueError, RecursionError):
            raise CloudProtocolError("The private CIPro endpoint did not return valid JSON.") from None
    if not isinstance(value, Mapping) or type(value.get("ok")) is not bool:
        raise CloudProtocolError("The private CIPro endpoint returned an invalid result envelope.")
    if value.get("release") != RELEASE_TAG or value.get("release_sha256") != RELEASE_SHA256:
        raise CloudProtocolError("The cloud response does not match the pinned CIPro v1.0 release.")
    if not value["ok"]:
        raise CloudEvaluationError(value.get("error"))
    return value


class CloudCIPro:
    """Use the project's bounded cloud API with an authenticated server-side session."""

    def __init__(self, credentials, owner, endpoint=DEFAULT_ENDPOINT, *, key_name=None, read_timeout=120):
        if not isinstance(owner, str) or _OWNER_PATTERN.fullmatch(owner) is None:
            raise CloudConfigurationError("WOLFRAM_CLOUD_OWNER must be the Wolfram account's username, ID or UUID.")
        if not isinstance(endpoint, str) or len(endpoint) > 120 or _ENDPOINT_PATTERN.fullmatch(endpoint) is None:
            raise CloudConfigurationError(f"{ENDPOINT_ENV} must be a relative path within py-cipro/.")
        self._credentials = credentials
        self._owner = owner
        self._endpoint = endpoint
        self._key_name = key_name
        self._read_timeout = read_timeout
        self._session = None

    @classmethod
    def from_environment(cls, env=None, *, read_timeout=120):
        """Read the account owner and credentials without starting a network connection."""
        env = os.environ if env is None else env
        required = ("WOLFRAM_CLOUD_CONSUMER_KEY", "WOLFRAM_CLOUD_CONSUMER_SECRET", "WOLFRAM_CLOUD_OWNER")
        missing = [name for name in required if not env.get(name, "").strip()]
        if missing:
            raise CloudConfigurationError("Set the required Wolfram Cloud environment variables: " + ", ".join(missing))
        key, secret, owner = (env[name] for name in required)
        return cls(
            SecuredAuthenticationKey(key.strip(), secret.strip()),
            owner.strip(),
            env.get(ENDPOINT_ENV, DEFAULT_ENDPOINT),
            key_name=env.get("WOLFRAM_CLOUD_KEY_NAME"),
            read_timeout=read_timeout,
        )

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close(self):
        if self._session is not None:
            self._session.stop()
            self._session = None

    def _transport(self):
        if self._session is not None:
            return self._session
        session = WolframCloudSession(
            credentials=self._credentials,
            inputform_string_evaluation=False,
            http_sessionclass=partial(_PrivateHTTPSession, self._read_timeout),
        )
        try:
            session.start()
            if not session.authorized():
                raise CloudAuthenticationError("Wolfram Cloud did not authorize the configured key.")
        except (AuthenticationException, ValueError, KeyError):
            session.stop()
            raise CloudAuthenticationError("Wolfram Cloud rejected the configured authentication key.") from None
        except BaseException:
            session.stop()
            raise
        self._session = session
        return session

    def _request(self, operation, *, record_id="", properties="", dataset=""):
        try:
            with _protected_sdk_call():
                response = self._transport().call(
                    (self._owner, self._endpoint),
                    {"operation": operation, "record_id": record_id, "properties": properties, "dataset": dataset},
                )
                _check_http(response.status)
                raw = response.get()
        except requests.Timeout:
            raise CloudUnavailableError("The request to Wolfram Cloud timed out.") from None
        except (requests.RequestException, OSError):
            raise CloudUnavailableError("The request to Wolfram Cloud could not be completed.") from None
        except AuthenticationException:
            raise CloudAuthenticationError("Wolfram Cloud rejected the authenticated request.") from None
        except (WolframLanguageException, ValueError, KeyError):
            raise CloudProtocolError("Wolfram Cloud returned an unreadable CIPro response.") from None
        return _envelope(raw)

    def _evaluate(self, expression):
        try:
            with _protected_sdk_call():
                response = self._transport().evaluate_wrap(expression)
                if response.request_error:
                    _check_http(response.http_response.status())
                return response.get(silent=True)
        except requests.Timeout:
            raise CloudUnavailableError("The Wolfram Cloud evaluation timed out. Check Cloud Objects before retrying deployment.") from None
        except (requests.RequestException, OSError):
            raise CloudUnavailableError("The Wolfram Cloud evaluation connection failed.") from None
        except AuthenticationException:
            raise CloudAuthenticationError("Wolfram Cloud rejected the authenticated evaluation.") from None
        except (WolframLanguageException, ValueError, KeyError):
            raise CloudProtocolError("The Wolfram Cloud evaluator did not return a readable result.") from None

    def deploy(self) -> dict:
        """Install the pinned package and private API via the authenticated evaluator."""
        if not isinstance(self._key_name, str) or _KEY_PATTERN.fullmatch(self._key_name) is None:
            raise CloudConfigurationError("Set WOLFRAM_CLOUD_KEY_NAME to the name of the secured authentication key.")
        try:
            source = files("py_cipro").joinpath("cloud_resources", "deploy.wl").read_text(encoding="utf-8")
        except OSError:
            raise CloudConfigurationError("This py-CIPro installation is missing the cloud deployment script.") from None
        identity = self._evaluate(wl.List(*(getattr(wl, name) for name in ("$WolframID", "$WolframUUID", "$UserName"))))
        if not isinstance(identity, (tuple, list)) or self._owner not in identity:
            raise CloudAuthenticationError("The authenticated Wolfram Cloud owner does not match WOLFRAM_CLOUD_OWNER.")
        result = _envelope(self._evaluate(wl.Apply(wlexpr(source), [self._endpoint, self._key_name])))
        if result.get("endpoint_path") != self._endpoint:
            raise CloudProtocolError("The deployment response did not confirm the requested private path.")
        return {"endpoint_path": self._endpoint}

    def health(self) -> dict:
        """Check whether the private endpoint can load the packaged CIPro code."""
        result = self._request("health")
        details = {"kernel_version": result.get("kernel_version"), "system_id": result.get("system_id")}
        if any(not isinstance(value, str) or not value.strip() or len(value) > 256 or not value.isprintable() for value in details.values()):
            raise CloudProtocolError("Cloud CIPro did not identify the kernel version and system.")
        if "system_word_length" in result:
            word_length = result["system_word_length"]
            if type(word_length) is not int or word_length not in (32, 64):
                raise CloudProtocolError("Cloud CIPro returned an invalid kernel word length.")
            details["system_word_length"] = word_length
        return details

    def properties(self, record_id: int, properties: Sequence[str]) -> dict:
        """Compute selected CIPro scalars for an archived Cicy3 configuration."""
        if type(record_id) is not int or not 1 <= record_id <= RECORD_COUNT:
            raise ValueError("record_id must identify an archived Cicy3 configuration.")
        if (
            isinstance(properties, str)
            or not isinstance(properties, Sequence)
            or not 1 <= len(properties) <= len(COMPUTE_PROPERTIES)
            or any(not isinstance(name, str) or name not in COMPUTE_PROPERTIES for name in properties)
            or len(properties) != len(set(properties))
        ):
            raise ValueError("properties must select distinct CIDim, CY or Euler fields.")
        result = self._request("properties", record_id=str(record_id), properties=",".join(properties))
        values = result.get("properties")
        if not isinstance(values, Mapping) or set(values) != set(properties):
            raise CloudProtocolError("Cloud CIPro did not return exactly the requested properties.")
        if any(type(value) is not (bool if name == "CY" else int) for name, value in values.items()):
            raise CloudProtocolError("Cloud CIPro returned a value with an unexpected type.")
        return dict(values)

    def dataset(self, name: str) -> dict:
        """Get a checked native count and source-member digest from the cloud endpoint."""
        if name not in DATASETS:
            raise ValueError("Unknown bundled CIPro dataset.")
        result = self._request("dataset", dataset=name)
        count = result.get("count")
        digest = result.get("member_sha256")
        if result.get("dataset") != name or type(count) is not int or count <= 0:
            raise CloudProtocolError("Cloud CIPro did not return a positive native count for the requested dataset.")
        if not isinstance(digest, str) or _SHA256_PATTERN.fullmatch(digest) is None:
            raise CloudProtocolError("Cloud CIPro did not return a digest for the loaded dataset file.")
        return {"dataset": name, "count": count, "member_sha256": digest}


def _dataset_digests():
    with open_release() as archive:
        for name in DATASETS:
            with archive.open(f"CIProData/{name}") as member:
                digest = sha256()
                for chunk in iter(lambda: member.read(1024 * 1024), b""):
                    digest.update(chunk)
                yield name, digest.hexdigest()


def _receipt():
    return {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "backend": "wolfram-cloud",
        "release": RELEASE_TAG,
        "release_sha256": RELEASE_SHA256,
        "status": "unavailable",
    }


def _failure(receipt, exc):
    access_error = isinstance(exc, (CloudConfigurationError, CloudAuthenticationError, CloudUnavailableError))
    receipt.update(status="unavailable" if access_error else "failed", code=exc.code, error=str(exc))


def qualify(client: CloudCIPro) -> dict:
    """Qualify authenticated package load, three real calculations and every bundled dataset."""
    receipt = _receipt()
    receipt.update(kernel=None, checks=[])
    try:
        expected_digests = dict(_dataset_digests())
    except (ValueError, OSError, KeyError):
        _failure(receipt, CloudProtocolError("The packaged dataset files failed local release verification."))
        return receipt
    try:
        receipt["kernel"] = client.health()
    except CloudError as exc:
        _failure(receipt, exc)
        return receipt
    for label, record_id, euler in CASES:
        expected = {"CIDim": 3, "CY": True, "Euler": euler}
        check = {"case": label, "record_id": record_id, "expected": expected}
        try:
            observed = client.properties(record_id, list(expected))
            check.update(observed=observed, passed=observed == expected)
        except CloudError as exc:
            check.update(passed=False, code=exc.code, error=str(exc))
        receipt["checks"].append(check)
    for name, digest in expected_digests.items():
        expected = {"member_sha256": digest}
        if name in EXPECTED_COUNTS:
            expected["count"] = EXPECTED_COUNTS[name]
        check = {"case": "native dataset", "dataset": name, "expected": expected}
        try:
            observed = client.dataset(name)
            check.update(observed=observed, passed=all(observed[key] == value for key, value in expected.items()))
        except CloudError as exc:
            check.update(passed=False, code=exc.code, error=str(exc))
        receipt["checks"].append(check)
    receipt["status"] = "passed" if all(check["passed"] for check in receipt["checks"]) else "failed"
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("deploy", "status", "qualify"))
    args = parser.parse_args(argv)
    receipt = _receipt()
    try:
        with CloudCIPro.from_environment(read_timeout=300 if args.operation == "deploy" else 120) as client:
            if args.operation == "qualify":
                receipt = qualify(client)
            elif args.operation == "status":
                receipt.update(status="passed", kernel=client.health())
            else:
                receipt.update(status="passed", deployment=client.deploy())
    except CloudError as exc:
        _failure(receipt, exc)
    print(json.dumps(receipt, indent=2))
    return {"passed": 0, "failed": 1, "unavailable": 2}[receipt["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
