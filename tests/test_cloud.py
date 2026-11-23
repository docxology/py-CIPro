"""Exercise typed Wolfram Cloud contracts using in-process SDK doubles."""

from contextlib import redirect_stdout
from io import StringIO
import json
import logging
import unittest
from unittest.mock import MagicMock, patch

import requests
from wolframclient.exception import AuthenticationException
from wolframclient.serializers import export

from py_cipro._catalog import DATASETS
from py_cipro._release import RELEASE_SHA256, RELEASE_TAG
from py_cipro.cloud import (
    DEFAULT_ENDPOINT,
    ENDPOINT_ENV,
    EXPECTED_COUNTS,
    CloudAuthenticationError,
    CloudCIPro,
    CloudConfigurationError,
    CloudEvaluationError,
    CloudProtocolError,
    CloudUnavailableError,
    _PrivateHTTPSession,
    _dataset_digests,
    main,
    qualify,
)
from py_cipro.qualify import CASES


ENV = {
    "WOLFRAM_CLOUD_OWNER": "researcher@example.test",
    "WOLFRAM_CLOUD_CONSUMER_KEY": "fixture-consumer-key",
    "WOLFRAM_CLOUD_CONSUMER_SECRET": "fixture-consumer-secret",
    "WOLFRAM_CLOUD_KEY_NAME": "py-cipro-fixture",
}
FIXTURE = {"CIDim": 3, "CY": True, "Euler": -200}


def envelope(**fields):
    return {"ok": True, "release": RELEASE_TAG, "release_sha256": RELEASE_SHA256, **fields}


class Response:
    def __init__(self, value, status=200):
        self.value = value
        self.status = status

    def get(self):
        if self.status != 200:
            raise AssertionError("Error bodies must not be decoded")
        return self.value


class CloudClientTests(unittest.TestCase):
    def setUp(self):
        self.client = CloudCIPro.from_environment(ENV)
        self.addCleanup(self.client.close)
        session_patch = patch("py_cipro.cloud.WolframCloudSession")
        self.session_class = session_patch.start()
        self.addCleanup(session_patch.stop)
        self.session = self.session_class.return_value
        self.session.authorized.return_value = True

    def test_lazy_authenticated_api_and_typed_payload(self):
        self.session_class.assert_not_called()
        self.session.call.return_value = Response(json.dumps(envelope(properties=FIXTURE)).encode())
        self.assertEqual(self.client.properties(7890, ["CIDim", "CY", "Euler"]), FIXTURE)
        self.session.call.assert_called_once_with(
            (ENV["WOLFRAM_CLOUD_OWNER"], DEFAULT_ENDPOINT),
            {"operation": "properties", "record_id": "7890", "properties": "CIDim,CY,Euler", "dataset": ""},
        )
        self.session.start.assert_called_once()
        self.client.close()
        self.client.close()
        self.session.stop.assert_called_once()

    def test_invalid_url_and_payload_refused_without_network(self):
        for path in ("https://example.test/api", "py-cipro/../elsewhere", "py-cipro/x%2Fy", "py-cipro/x?key=y"):
            with self.subTest(path=path), self.assertRaises(CloudConfigurationError):
                CloudCIPro.from_environment({**ENV, ENDPOINT_ENV: path})
        for record, fields in ((True, ["Euler"]), (7891, ["Euler"]), (1, "CY"), (1, ["CIDim", "CIDim"]), (1, ["Exit"])):
            with self.subTest(record=record, fields=fields), self.assertRaises(ValueError):
                self.client.properties(record, fields)
        self.session_class.assert_not_called()

    def test_release_binding_and_scalar_types_fail_closed(self):
        for value in (
            b"not JSON",
            envelope(release_sha256="f" * 64, properties=FIXTURE),
            envelope(properties={"Euler": False}),
            envelope(properties={"Euler": -200, "CY": True}),
        ):
            with self.subTest(value=value), self.assertRaises(CloudProtocolError):
                self.session.call.return_value = Response(value)
                self.client.properties(7890, ["Euler"])

    def test_authentication_and_provider_errors_are_safe(self):
        unsafe = "opaque fixture credential-like remote text"
        self.session.start.side_effect = AuthenticationException(object(), unsafe)
        with self.assertRaises(CloudAuthenticationError) as result:
            self.client.health()
        self.assertNotIn(unsafe, str(result.exception))
        self.assertTrue(result.exception.__suppress_context__)
        self.session.stop.assert_called_once()
        self.session.start.side_effect = None
        self.session.call.return_value = Response(unsafe, status=403)
        with self.assertRaises(CloudAuthenticationError):
            self.client.health()
        self.session.call.return_value = Response(envelope(ok=False, error=unsafe))
        with self.assertRaises(CloudEvaluationError) as result:
            self.client.health()
        self.assertEqual(result.exception.code, "remote_rejected")
        self.assertNotIn(unsafe, str(result.exception))

    def test_timeout_and_logging_restore(self):
        threshold = logging.root.manager.disable

        def fail():
            logging.disable(logging.CRITICAL)
            raise requests.Timeout("hidden upstream detail")

        self.session.start.side_effect = fail
        with self.assertRaises(CloudUnavailableError) as result:
            self.client.health()
        self.assertNotIn("hidden upstream detail", str(result.exception))
        self.assertEqual(logging.root.manager.disable, threshold)

    def test_deploy_checks_cloud_owner_before_any_mutation(self):
        response = self.session.evaluate_wrap.return_value
        response.request_error = False
        response.get.return_value = ("someone-else@example.test", "uuid", "someone-else")
        with patch("py_cipro.cloud.files") as mock_files:
            mock_files.return_value.joinpath.return_value.read_text.return_value = "Function[{path,key},<||>]"
            with self.assertRaises(CloudAuthenticationError):
                self.client.deploy()
        self.session.evaluate_wrap.assert_called_once()

    def test_deploy_submits_pinned_function_with_typed_parameters(self):
        response = self.session.evaluate_wrap.return_value
        response.request_error = False
        response.get.side_effect = [
            (ENV["WOLFRAM_CLOUD_OWNER"], "uuid", "researcher"),
            envelope(endpoint_path=DEFAULT_ENDPOINT),
        ]
        with patch("py_cipro.cloud.files") as mock_files:
            mock_files.return_value.joinpath.return_value.read_text.return_value = "Function[{path,key},<||>]"
            self.assertEqual(self.client.deploy(), {"endpoint_path": DEFAULT_ENDPOINT})
        expression = self.session.evaluate_wrap.call_args_list[-1].args[0]
        serialized = export(expression, target_format="wl").decode()
        self.assertIn(f'"{DEFAULT_ENDPOINT}"', serialized)
        self.assertIn(f'"{ENV["WOLFRAM_CLOUD_KEY_NAME"]}"', serialized)
        self.assertNotIn(ENV["WOLFRAM_CLOUD_CONSUMER_SECRET"], serialized)


class CloudQualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.digests = dict(_dataset_digests())

    def test_each_dataset_and_geometry_checked_independently(self):
        self.assertEqual(set(self.digests), set(DATASETS))
        self.assertEqual(len(set(self.digests.values())), len(DATASETS))
        client = MagicMock(spec=CloudCIPro)
        client.health.return_value = {"kernel_version": "fixture", "system_id": "Linux-x86-64"}
        expected_euler = {record_id: euler for _, record_id, euler in CASES}
        client.properties.side_effect = lambda record_id, fields: {**FIXTURE, "Euler": expected_euler[record_id]}

        def dataset(name):
            if name == "Cicy4":
                raise CloudEvaluationError("dataset_load_failed")
            return {"dataset": name, "count": EXPECTED_COUNTS.get(name, 17), "member_sha256": self.digests[name]}

        client.dataset.side_effect = dataset
        report = qualify(client)
        self.assertEqual(report["status"], "failed")
        self.assertEqual(len(report["checks"]), len(DATASETS) + len(CASES))
        failed = [check for check in report["checks"] if not check["passed"]]
        self.assertEqual([(check["dataset"], check["code"]) for check in failed], [("Cicy4", "dataset_load_failed")])
        self.assertEqual([call.args[0] for call in client.dataset.call_args_list], list(DATASETS))

    def test_missing_credentials_are_unavailable_receipt(self):
        output = StringIO()
        with patch.dict("os.environ", clear=True), redirect_stdout(output):
            self.assertEqual(main(["qualify"]), 2)
        report = json.loads(output.getvalue())
        self.assertEqual(report["status"], "unavailable")
        self.assertEqual(report["code"], "configuration")

    def test_transport_is_tls_bound_and_does_not_follow_redirects(self):
        with _PrivateHTTPSession(120) as session, patch.object(requests.Session, "request") as request:
            for url in ("http://www.wolframcloud.com", "https://www.wolframcloud.com.evil.test", "https://www.wolframcloud.com@evil.test"):
                with self.subTest(url=url), self.assertRaises(CloudConfigurationError):
                    session.request("POST", url)
            request.assert_not_called()
            session.request("POST", "https://account.wolfram.com/auth/request-token", allow_redirects=True)
            request.assert_called_once_with(
                "POST", "https://account.wolfram.com/auth/request-token", timeout=(10, 120), allow_redirects=False,
            )
