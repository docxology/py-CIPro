"""Verify the live HTTP routes and the guarded CIPro call boundary."""

from http.client import HTTPConnection
import json
from threading import Thread
import unittest
from unittest.mock import patch

from py_cipro.dashboard import DashboardServer


class FakeCIPro:
    def __init__(self):
        self.calls = []

    def property(self, geometry, keys):
        self.calls.append((geometry, keys))
        return {"CIDim": 3, "CY": True, "Euler": -200}

    def close(self):
        pass


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.server = DashboardServer(0)
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
        status, _, payload = self.request("GET", "/api/kernel")
        self.assertEqual((status, json.loads(payload)), (200, {"enabled": False}))
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
        origin = f"http://127.0.0.1:{self.server.server_port}"
        with patch.object(self.server, "kernel", kernel):
            status, _, payload = self.post(body, Origin=origin)
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(payload), {
                "source": "CIPro v1.0 Wolfram kernel",
                "properties": {"Euler": -200, "CIDim": 3, "CY": True},
            })
            self.assertEqual(kernel.calls, [({"Conf": ((5,),), "DimPs": (4,)}, ["Euler", "CIDim", "CY"])])
            with self.server.compute_lock:
                self.assertEqual(self.post(body)[0], 409)
