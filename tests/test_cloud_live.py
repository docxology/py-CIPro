"""Opt-in qualification through the real private Wolfram Cloud API and dashboard."""

from http import HTTPStatus
from http.client import HTTPConnection
import json
import os
from threading import Thread
import unittest

from py_cipro.dashboard import DashboardServer


@unittest.skipUnless(
    os.environ.get("PY_CIPRO_RUN_CLOUD_LIVE") == "1",
    "set PY_CIPRO_RUN_CLOUD_LIVE=1 with configured credentials to run live cloud tests",
)
class LiveCloudDashboardTests(unittest.TestCase):
    def test_browser_api_uses_the_deployed_ci_pro(self):
        with DashboardServer(0, cloud=True) as server:
            thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01})
            thread.start()
            try:
                status, body = self.request(server, "GET", "/api/kernel")
                self.assertEqual(status, HTTPStatus.OK, body)
                self.assertEqual(body["provider"], "cloud", body)
                self.assertIs(body["enabled"], True, body)

                status, archived = self.request(server, "GET", "/api/record?id=7890")
                self.assertEqual(status, HTTPStatus.OK, archived)
                self.assertEqual(archived["configuration"], [[5]])

                status, live = self.request(server, "POST", "/api/compute", {
                    "record_id": 7890,
                    "properties": ["CIDim", "CY", "Euler"],
                })
                self.assertEqual(status, HTTPStatus.OK, live)
                self.assertEqual(live["source"], "CIPro v1.0 in Wolfram Cloud")
                self.assertEqual(live["properties"], {"CIDim": 3, "CY": True, "Euler": -200})
                self.assertIs(live["properties"]["CY"], True)
            finally:
                server.shutdown()
                thread.join()

    @staticmethod
    def request(server, method, path, payload=None):
        connection = HTTPConnection("127.0.0.1", server.server_port, timeout=180)
        try:
            headers = {"Origin": f"http://127.0.0.1:{server.server_port}"}
            if payload is not None:
                headers["Content-Type"] = "application/json"
            connection.request(method, path, json.dumps(payload) if payload is not None else None, headers)
            response = connection.getresponse()
            return response.status, json.loads(response.read())
        finally:
            connection.close()
