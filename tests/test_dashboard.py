"""Verify the live HTTP routes and the guarded CIPro call boundary."""

from contextlib import redirect_stderr
from http.client import HTTPConnection
from io import StringIO
import json
import os
from threading import Thread
import unittest
from unittest.mock import patch

from py_cipro.cloud import CloudAuthenticationError, CloudCIPro, CloudError
from py_cipro.dashboard import DashboardServer, main


class FakeCIPro:
    def __init__(self):
        self.calls = []

    def property(self, geometry, keys):
        self.calls.append((geometry, keys))
        return {"CIDim": 3, "CY": True, "Euler": -200}

    def close(self):
        pass


class FakeCloudCIPro:
    def __init__(self):
        self.calls = []

    def properties(self, record_id, keys):
        self.calls.append((record_id, keys))
        return {"CIDim": 3, "CY": True, "Euler": -200}

    def close(self):
        pass


class DashboardTests(unittest.TestCase):
    def start_server(self, **options):
        self.server = DashboardServer(0, **options)
        self.addCleanup(self.server.server_close)
        self.thread = Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.01})
        self.thread.start()
        self.addCleanup(self.thread.join)
        self.addCleanup(self.server.shutdown)

    def request(self, method, path, body=None, **headers):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=2)
        try:
            connection.request(method, path, body=body, headers=headers)
            response = connection.getresponse()
            return response.status, response.getheaders(), response.read()
        finally:
            connection.close()

    def post(self, body, **headers):
        headers.setdefault("Content-Type", "application/json")
        return self.request("POST", "/api/compute", body, **headers)

    def test_assets_and_archive(self):
        self.start_server()
        for route in ("/", "/styles.css", "/explorer.js"):
            with self.subTest(route=route):
                status, headers, body = self.request("GET", route)
                self.assertEqual(status, 200)
                self.assertTrue(body)
                self.assertIn(("X-Content-Type-Options", "nosniff"), headers)
        status, _, payload = self.request("GET", "/api/catalog")
        archive = json.loads(payload)
        self.assertEqual(status, 200)
        self.assertEqual(archive["dataset"], "Cicy3")
        self.assertEqual(len(archive["records"]), 7890)
        status, _, payload = self.request("GET", "/api/record?id=7890")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(payload)["configuration"], [[5]])
        self.assertEqual(self.request("GET", "/api/record?id=7891")[0], 404)
        self.assertEqual(self.request("GET", "/api/record?id=1&id=2")[0], 400)

    def test_compute_status_and_validation(self):
        self.start_server()
        status, _, payload = self.request("GET", "/api/kernel")
        self.assertEqual((status, json.loads(payload)), (200, {"enabled": False, "provider": "archive"}))
        request = '{"record_id":7890,"properties":["Euler","CIDim","CY"]}'
        self.assertEqual(self.post(request)[0], 503)
        self.assertEqual(self.post(request, Origin="https://example.invalid")[0], 403)
        self.assertEqual(self.post(request, Host="example.invalid")[0], 421)
        self.assertEqual(self.post(request, **{"Content-Type": "text/plain"})[0], 415)
        self.assertEqual(self.post(" " * 1025)[0], 413)
        for body in (
            '{"record_id":true,"properties":["Euler"]}',
            '{"record_id":0,"properties":["Euler"]}',
            '{"record_id":7890,"properties":["Euler","Euler"]}',
            '{"record_id":7890,"properties":["DefEqs"]}',
            '{"record_id":7890,"record_id":1,"properties":["Euler"]}',
            '{"record_id":7890,"properties":[{}]}',
            '{"record_id":7890,"properties":["Euler"],"extra":true}',
        ):
            with self.subTest(body=body):
                self.assertEqual(self.post(body)[0], 400)

    def test_selected_kernel_call_and_busy_gate(self):
        kernel = FakeCIPro()
        body = '{"record_id":7890,"properties":["Euler","CIDim","CY"]}'
        with patch("py_cipro.dashboard.CIPro", return_value=kernel):
            self.start_server(kernel=True)
        origin = f"http://127.0.0.1:{self.server.server_port}"
        status, _, payload = self.request("GET", "/api/kernel")
        self.assertEqual((status, json.loads(payload)), (200, {"enabled": True, "provider": "local"}))
        status, _, payload = self.post(body, Origin=origin)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(payload), {
            "source": "CIPro v1.0 Wolfram kernel",
            "properties": {"Euler": -200, "CIDim": 3, "CY": True},
        })
        self.assertEqual(kernel.calls, [({"Conf": ((5,),), "DimPs": (4,)}, ["Euler", "CIDim", "CY"])])
        with self.server.compute_lock:
            self.assertEqual(self.post(body)[0], 409)

    def test_selected_cloud_call_forwards_only_record_id_and_allowed_keys(self):
        cloud = FakeCloudCIPro()
        body = '{"record_id":7890,"properties":["Euler","CIDim","CY"]}'
        with patch.object(CloudCIPro, "from_environment", return_value=cloud):
            self.start_server(cloud=True)
        status, _, payload = self.request("GET", "/api/kernel")
        self.assertEqual((status, json.loads(payload)), (200, {"enabled": True, "provider": "cloud"}))
        self.assertEqual(cloud.calls, [])
        self.assertEqual(self.post(body, Origin="https://example.invalid")[0], 403)
        self.assertEqual(self.post('{"record_id":7890,"properties":["Get"]}')[0], 400)
        self.assertEqual(cloud.calls, [])
        status, _, payload = self.post(body)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(payload), {
            "source": "CIPro v1.0 in Wolfram Cloud",
            "properties": {"Euler": -200, "CIDim": 3, "CY": True},
        })
        self.assertEqual(cloud.calls, [(7890, ["Euler", "CIDim", "CY"])])
        with self.server.compute_lock:
            self.assertEqual(self.post(body)[0], 409)

    def test_missing_cloud_setup_preserves_archive_and_disables_compute(self):
        with patch.dict(os.environ, {}, clear=True):
            self.start_server(cloud=True)
        status, _, payload = self.request("GET", "/api/kernel")
        response = json.loads(payload)
        self.assertEqual(status, 200)
        self.assertEqual(response["provider"], "cloud")
        self.assertFalse(response["enabled"])
        self.assertIn("WOLFRAM_CLOUD", response["error"])
        self.assertEqual(self.request("GET", "/api/record?id=7890")[0], 200)
        status, _, payload = self.post('{"record_id":7890,"properties":["Euler"]}')
        self.assertEqual((status, json.loads(payload)), (503, {"error": response["error"]}))

    def test_cloud_failures_keep_the_underlying_transport_error_private(self):
        cloud = FakeCloudCIPro()
        with patch.object(CloudCIPro, "from_environment", return_value=cloud):
            self.start_server(cloud=True)
        body = '{"record_id":7890,"properties":["Euler"]}'
        for error, expected_status in (
            (CloudAuthenticationError("Wolfram Cloud authorization failed."), 503),
            (CloudError("Wolfram Cloud evaluation failed."), 502),
        ):
            with self.subTest(error=type(error)), patch.object(cloud, "properties", side_effect=error):
                error.__cause__ = RuntimeError("private transport diagnostic")
                status, _, payload = self.post(body)
                self.assertEqual(status, expected_status)
                self.assertEqual(json.loads(payload), {"error": str(error)})
                self.assertNotIn(b"private transport diagnostic", payload)

    def test_cli_rejects_two_providers(self):
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as failure:
            main(["--kernel", "--cloud"])
        self.assertEqual(failure.exception.code, 2)
