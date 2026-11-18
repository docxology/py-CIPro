"""Verify loopback HTTP routes, native workers, and the Wolfram call boundary."""

from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from http.client import HTTPConnection
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from threading import Thread
from time import monotonic
import unittest
from unittest.mock import patch

from py_cipro import CIPro, Evaluation, ambient_index_divisor, cubic_signature, wl
from py_cipro._dashboard_research import recompute_study
from py_cipro.dashboard import DashboardServer, MAX_COMPUTE_BODY, MAX_LAB_BODY, NATIVE_TIMEOUT


QUINTIC = {"record_id": 7890, "properties": ["Euler", "CIDim", "CY"]}
QUINTIC_VALUES = {"Euler": -200, "CIDim": 3, "CY": True}


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.server = self.start_server()
        self.origin = f"http://127.0.0.1:{self.server.server_port}"

    def start_server(self):
        server = DashboardServer(0)
        self.addCleanup(server.server_close)
        thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01})
        thread.start()
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        return server

    def request(self, method, path, body=None, *, server=None, timeout=5, **headers):
        port = (server or self.server).server_port
        connection = HTTPConnection("127.0.0.1", port, timeout=timeout)
        try:
            connection.request(method, path, body=body, headers=headers)
            response = connection.getresponse()
            return response.status, response.getheaders(), response.read()
        finally:
            connection.close()

    def post(self, body, path="/api/compute", **headers):
        headers.setdefault("Content-Type", "application/json")
        if not isinstance(body, (bytes, str)):
            body = json.dumps(body)
        return self.request("POST", path, body, **headers)

    def test_assets_and_archive(self):
        for route, media in (
            ("/", "text/html"),
            ("/styles.css", "text/css"),
            ("/explorer.js", "text/javascript"),
            ("/method-lab.js", "text/javascript"),
        ):
            with self.subTest(route=route):
                status, headers, body = self.request("GET", route)
                self.assertEqual(status, 200)
                self.assertTrue(body)
                self.assertIn(("X-Content-Type-Options", "nosniff"), headers)
                self.assertIn(("Content-Type", f"{media}; charset=utf-8"), headers)
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

    def test_default_and_explicit_native_compute(self):
        status, _, payload = self.request("GET", "/api/kernel")
        self.assertEqual((status, json.loads(payload)), (200, {
            "enabled": True, "default_backend": "python", "backends": ["python", "wolfram", "auto"],
        }))
        with patch.object(self.server.kernel, "call_result") as kernel_call:
            for backend in (None, "python", "auto"):
                with self.subTest(backend=backend):
                    body = dict(QUINTIC) if backend is None else {**QUINTIC, "backend": backend}
                    status, _, payload = self.post(body, Origin=self.origin)
                    self.assertEqual(status, 200)
                    self.assertEqual(json.loads(payload), {
                        "source": "CIPro v1.0 Python equivalent", "backend": "python", "properties": QUINTIC_VALUES,
                    })
            kernel_call.assert_not_called()

    def test_packaged_manuscript_and_figure_assets(self):
        status, _, data = self.request("GET", "/api/research/provenance")
        self.assertEqual(status, 200)
        provenance = json.loads(data)
        self.assertGreaterEqual(provenance["manuscript_pages"], 22)
        self.assertEqual(provenance["manuscript_author"], "Daniel Friedman")
        self.assertTrue(provenance["cover"]["alt_text"])
        self.assertEqual(provenance["archive_sha256"], self.server.catalog.sha256)
        self.assertEqual(provenance["dataset_sha256"], self.server.catalog.member_sha256)
        self.assertEqual(set(provenance["figures"]), {
            "chern-audit", "cicy3-atlas", "cicy3-structure", "cicy3-multiplicity",
            "atlas-comparison", "line-bundle-cohomology", "bicubic-exact", "integral-invariants",
        })
        self.assertEqual(len(provenance["assets_sha256"]), 18)
        self.assertIn("graphical-abstract.pdf", provenance["assets_sha256"])
        self.assertIn("graphical-abstract.png", provenance["assets_sha256"])
        self.assertIn("cubic-refinement.json", provenance["assets_sha256"])
        self.assertEqual(set(provenance["cover"]["studies_sha256"]), {
            "integral-invariants", "cubic-refinement", "index-divisibility",
        })
        for name, digest in provenance["assets_sha256"].items():
            route = "/api/research" if name == "manuscript-analysis.json" else f"/research/{name}"
            with self.subTest(route=route):
                status, headers, body = self.request("GET", route)
                self.assertEqual(status, 200)
                self.assertEqual(sha256(body).hexdigest(), digest)
                if name.endswith(".pdf"):
                    self.assertTrue(body.startswith(b"%PDF-"))
                    self.assertIn(("Content-Type", "application/pdf"), headers)
                    self.assertIn(("Content-Disposition", f'inline; filename="{name}"'), headers)
                    head_status, head_headers, head_body = self.request("HEAD", route)
                    self.assertEqual((head_status, head_body), (200, b""))
                    self.assertIn(("Content-Length", str(len(body))), head_headers)
                if name.endswith(".png"):
                    self.assertTrue(body.startswith(b"\x89PNG\r\n\x1a\n"))
                    self.assertIn(("Content-Type", "image/png"), headers)
        self.assertEqual(self.request("GET", "/research/other.pdf")[0], 404)

    def test_extended_studies_use_exact_manuscript_data_and_catalogue_cohorts(self):
        status, _, body = self.request("GET", "/api/research/studies")
        self.assertEqual(status, 200)
        studies = json.loads(body)
        self.assertEqual(set(studies), {
            "chern-audit", "atlas-comparison", "bicubic-exact", "integral-invariants", "cubic-refinement",
        })
        for name, study in studies.items():
            status, _, body = self.request("GET", f"/research/{name}.json")
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body), study)

        records = self.server.catalog.records
        expected = {
            "figure=chern-audit&volume=270&pairing=144&modal=1": [
                row["id"] for row in studies["chern-audit"]["rows"]
                if not row["product"] and row["hodge"] == [9, 21]
                and row["volume"] == 270 and row["c2_polarized"] == 144
            ],
            "figure=atlas-comparison&euler=-58": [
                row.id for row in records if not row.product and row.euler <= -58
            ],
            "figure=atlas-comparison&factors=7&favourable=1": [
                row.id for row in records if not row.product and row.favourable and len(row.configuration) == 7
            ],
            "figure=atlas-comparison": [row.id for row in records if not row.product],
            "figure=bicubic-exact": [7884],
        }
        for query, ids in expected.items():
            with self.subTest(query=query):
                status, _, body = self.request("GET", f"/api/research/records?{query}")
                self.assertEqual(status, 200)
                result = json.loads(body)
                self.assertEqual(result["ids"], ids)
                self.assertEqual(result["matched"], len(ids))
        self.assertIn(1258, expected["figure=chern-audit&volume=270&pairing=144&modal=1"])
        for query in ("figure=chern-audit&volume=270", "figure=atlas-comparison&factors=1&euler=0",
                      "figure=bicubic-exact&geometry=quintic"):
            self.assertEqual(self.request("GET", f"/api/research/records?{query}")[0], 400)

    def test_extended_studies_rerun_in_python(self):
        route = "/api/research/rerun"
        with patch.object(self.server.kernel, "call_result") as wolfram:
            for payload, expected in (
                ({"figure": "chern-audit", "record_id": 1258}, {
                    "volume": 270, "c2_polarized": 144, "index": 57,
                }),
                ({"figure": "atlas-comparison", "euler": -58}, {
                    "euler": -58, "record_count_le": 1516, "pair_count_le": 146,
                }),
                ({"figure": "atlas-comparison", "factors": 7}, {"ambient_factors": 7}),
                ({"figure": "atlas-comparison"}, {
                    "median_euler": {"presentation": -40, "equal_pair": -62},
                }),
                ({"figure": "bicubic-exact", "a": 3, "b": -3}, {
                    "h": [0, 7, 7, 0], "generic_h": [0, 0, 0, 0], "index": 0,
                    "rank_h2": 3, "paired_excess": 7,
                }),
            ):
                with self.subTest(payload=payload):
                    status, _, body = self.post(payload, route, Origin=self.origin)
                    self.assertEqual(status, 200, body)
                    response = json.loads(body)
                    self.assertEqual(response["backend"], "python")
                    self.assertTrue(response["matches_manuscript"])
                    self.assertEqual(response["result"], response["manuscript"])
                    self.assertEqual({key: response["result"][key] for key in expected}, expected)
            wolfram.assert_not_called()
        for payload in (
            {"figure": "chern-audit", "record_id": True},
            {"figure": "chern-audit", "record_id": 7891},
            {"figure": "atlas-comparison", "euler": -999},
            {"figure": "atlas-comparison", "factors": 7, "backend": "wolfram"},
            {"figure": "bicubic-exact", "a": 9, "b": 0},
            {"figure": "bicubic-exact", "a": 3, "b": -3, "matrix": []},
        ):
            self.assertEqual(self.post(payload, route)[0], 400, payload)
        self.assertEqual(self.post({"figure": "atlas-comparison"}, route, Origin="https://example.invalid")[0], 403)

    def test_integral_heatmap_selects_exact_archive_ids(self):
        status, _, body = self.request("GET", "/research/integral-invariants.json")
        self.assertEqual(status, 200)
        rows = json.loads(body)["rows"]
        pair = [row for row in rows if (row["cubic_content"], row["chern_content"]) == (1, 4)]
        route = "/api/research/records?figure=integral-invariants&"
        for query, ids in (
            ("cubic_content=1&chern_content=4", [row["id"] for row in pair]),
            ("cubic_content=1&chern_content=4&h11=9&h21=21", [
                row["id"] for row in pair if row["hodge"] == [9, 21]
            ]),
            ("cubic_content=1&chern_content=4&euler=-24", [
                row["id"] for row in pair if row["euler"] == -24
            ]),
            ("record_id=7878", [7878]),
            ("cubic_content=99&chern_content=99", []),
        ):
            with self.subTest(query=query):
                status, _, body = self.request("GET", route + query)
                data = json.loads(body)
                self.assertEqual(status, 200, data)
                self.assertEqual(data["ids"], ids)
                self.assertEqual(data["matched"], len(ids))
        product = next(record.id for record in self.server.catalog.records if record.product)
        for invalid in (
            "cubic_content=1",
            "cubic_content=1&chern_content=4&h11=9",
            "cubic_content=1&chern_content=-1",
            "cubic_content=1&chern_content=4&cubic_content=1",
            f"record_id={product}",
        ):
            self.assertEqual(self.request("GET", route + invalid)[0], 400, invalid)

    def test_integral_reruns_use_the_selected_source_geometry(self):
        route = "/api/research/rerun"
        with patch.object(self.server.kernel, "call_result") as wolfram:
            for number, dimensions, configuration, hodge, pair, c2, indices in (
                (7878, [5], [[3, 3]], [1, 73], (9, 54), [54], [6]),
                (7879, [6], [[3, 2, 2]], [1, 73], (12, 60), [60], [7]),
                (1258, None, None, [9, 21], (1, 12), [24, 24, 24, 36, 36], [2, 2, 2, 3, 3]),
            ):
                with self.subTest(record_id=number):
                    status, _, body = self.request("GET", f"/api/record?id={number}")
                    self.assertEqual(status, 200)
                    archived = json.loads(body)
                    if dimensions is not None:
                        self.assertEqual(archived["ambient_dimensions"], dimensions)
                        self.assertEqual(archived["configuration"], configuration)
                    status, _, body = self.post({"figure": "integral-invariants", "record_id": number}, route,
                                                Origin=self.origin)
                    self.assertEqual(status, 200, body)
                    response = json.loads(body)
                    self.assertEqual(response["backend"], "python")
                    self.assertEqual(response["record_id"], number)
                    self.assertTrue(response["matches_manuscript"])
                    self.assertEqual(response["result"], response["manuscript"])
                    self.assertEqual(response["result"], {
                        "id": number,
                        "ambient_factors": len(archived["ambient_dimensions"]),
                        "favourable": archived["favourable"],
                        "hodge": hodge,
                        "euler": archived["euler"],
                        "cubic_content": pair[0],
                        "chern_content": pair[1],
                        "c2": c2,
                        "hyperplane_indices": indices,
                    })
            wolfram.assert_not_called()
        product_id = next(record.id for record in self.server.catalog.records if record.product)
        for invalid in (True, 0, 7891, product_id):
            self.assertEqual(self.post({"figure": "integral-invariants", "record_id": invalid}, route)[0], 400)
        self.assertEqual(self.post({"figure": "integral-invariants", "record_id": 7878, "backend": "wolfram"},
                                   route)[0], 400)

    def test_integral_worker_compares_only_after_recomputation(self):
        reference = {"cubic_content": 1, "chern_content": 1}
        result = recompute_study({"research": "integral-invariants", "record_id": 7878, "manuscript": reference})
        self.assertEqual(result["result"]["cubic_content"], 9)
        self.assertEqual(result["result"]["chern_content"], 54)
        self.assertEqual(result["manuscript"], reference)
        self.assertFalse(result["matches_manuscript"])

    def test_cubic_refinement_drilldown_preserves_the_selected_scope(self):
        route = "/api/research/records?figure=cubic-refinement"
        signature = "&d1=1&d2=2&d3=2&dp=4"
        cases = (
            (signature, 1408, None),
            (signature + "&h11=5&h21=53", 3, [7701, 7705, 7741]),
            (signature + "&euler=-96", 14, None),
            ("&record_id=6232", 1, [6232]),
            ("&d1=2&d2=2&d3=4&dp=4&h11=4&h21=32", 1, [6232]),
        )
        for query, count, expected in cases:
            with self.subTest(query=query):
                status, _, body = self.request("GET", route + query)
                self.assertEqual(status, 200, body)
                response = json.loads(body)
                self.assertEqual(response["matched"], count)
                if expected is not None:
                    self.assertEqual(response["ids"], expected)
                if query.endswith("&euler=-96"):
                    self.assertTrue(all(self.server.catalog.record(number).euler == -96 for number in response["ids"]))
        for query in (
            "&d1=1&d2=2&d3=2",
            signature + "&h11=5",
            signature + "&h11=5&h21=53&euler=-96",
            signature + "&dp=4",
            signature + "&record_id=7741",
            "&d1=1&d2=2&d3=2&dp=-4",
        ):
            self.assertEqual(self.request("GET", route + query)[0], 400)

    def test_cubic_signature_and_python_worker_match_both_witness_pairs(self):
        route = "/api/research/rerun"
        witnesses = {
            7702: (1, 1, 2, 4),
            7741: (1, 2, 2, 4),
            6177: (2, 2, 2, 4),
            6232: (2, 2, 4, 4),
        }
        with patch.object(self.server.kernel, "call_result") as wolfram:
            for number, (d1, d2, d3, dp) in witnesses.items():
                with self.subTest(record_id=number):
                    expected = {"id": number, "d1": d1, "d2": d2, "d3": d3, "dp": dp}
                    self.assertEqual(cubic_signature(number), expected)
                    status, _, body = self.post({"figure": "cubic-refinement", "record_id": number}, route,
                                                Origin=self.origin)
                    self.assertEqual(status, 200, body)
                    response = json.loads(body)
                    self.assertEqual(response["record_id"], number)
                    self.assertEqual(response["backend"], "python")
                    self.assertEqual(response["result"], expected)
                    self.assertEqual(response["manuscript"], expected)
                    self.assertTrue(response["matches_manuscript"])
            wolfram.assert_not_called()
        product = next(record.id for record in self.server.catalog.records if record.product)
        for invalid in (True, 0, 7891, "7702", 7702.0, product):
            with self.subTest(record_id=invalid), self.assertRaises(ValueError):
                cubic_signature(invalid)
            self.assertEqual(self.post({"figure": "cubic-refinement", "record_id": invalid}, route)[0], 400)

        stale = {"id": 7741, "d1": 1, "d2": 1, "d3": 2, "dp": 4}
        replay = recompute_study({"research": "cubic-refinement", "record_id": 7741, "manuscript": stale})
        self.assertEqual(replay["result"]["d2"], 2)
        self.assertFalse(replay["matches_manuscript"])

    def test_public_ambient_index_divisor_recomputes_both_matched_records(self):
        self.assertEqual(ambient_index_divisor(7626), 2)
        self.assertEqual(ambient_index_divisor(7635), 1)
        self.assertEqual(cubic_signature(7626)["d3"], cubic_signature(7635)["d3"])
        product = next(record.id for record in self.server.catalog.records if record.product)
        for invalid in (False, 0, "7626", product):
            with self.subTest(record_id=invalid), self.assertRaises(ValueError):
                ambient_index_divisor(invalid)

    def test_research_mark_selection_returns_exact_archive_ids(self):
        records = self.server.catalog.records
        examples = {
            "figure=atlas&h11=1&h21=101": [7890],
            "figure=atlas&euler=0&product=1": [row.id for row in records if row.product and row.euler == 0],
            "figure=atlas&euler=0": [row.id for row in records if row.euler == 0],
            "figure=structure&factors=7&codimension=8": [
                row.id for row in records if len(row.configuration) == 7 and len(row.configuration[0]) == 8
            ],
            "figure=structure&factors=7&favourable=1": [
                row.id for row in records if not row.product and row.favourable and len(row.configuration) == 7
            ],
            "figure=multiplicity&rank=1": [row.id for row in records if not row.product and (row.h11, row.h21) == (9, 21)],
            "figure=cohomology&geometry=bicubic": [7884],
        }
        for query, expected in examples.items():
            with self.subTest(query=query):
                status, _, body = self.request("GET", f"/api/research/records?{query}")
                self.assertEqual(status, 200)
                payload = json.loads(body)
                self.assertEqual(payload["ids"], expected)
                self.assertEqual(payload["matched"], len(expected))
                self.assertTrue(payload["label"])
        for invalid in ("figure=atlas&euler=0&euler=1", "figure=atlas&euler=0&product=unknown",
                        "figure=structure&factors=seven", "figure=multiplicity&rank=0"):
            self.assertEqual(self.request("GET", f"/api/research/records?{invalid}")[0], 400)

    def test_research_reruns_native_cohomology_and_reports_unsupported_dimensions(self):
        route = "/api/research/rerun"
        examples = (
            ({"geometry": "quintic", "k": 5}, 7890, 125, [125, 0, 0, 0], "supported"),
            ({"geometry": "bicubic", "a": 1, "b": -1}, 7884, 0, [0, 0, 0, 0], "acyclic"),
            ({"geometry": "bicubic", "a": -8, "b": 1}, 7884, 63, None, "unsupported"),
        )
        with patch.object(self.server.kernel, "call_result") as kernel_call:
            for charges, record_id, index, dimensions, state in examples:
                with self.subTest(charges=charges):
                    status, _, body = self.post({"figure": "cohomology", **charges}, route, Origin=self.origin)
                    self.assertEqual(status, 200)
                    result = json.loads(body)
                    self.assertEqual((result["backend"], result["record_id"]), ("python", record_id))
                    self.assertEqual((result["index"], result["dimensions"], result["status"]), (index, dimensions, state))
                    self.assertTrue(result["matches_manuscript"])
            kernel_call.assert_not_called()
        payload = {"figure": "cohomology", "geometry": "quintic", "k": 5}
        self.assertEqual(self.post(payload, route, Origin="https://example.invalid")[0], 403)
        self.assertEqual(self.post({**payload, "k": 11}, route)[0], 400)
        self.assertEqual(self.post({**payload, "k": True}, route)[0], 400)

    def test_wolfram_default_remains_lazy(self):
        with patch("py_cipro._client.WolframLanguageSession") as session, DashboardServer(0, kernel=True) as server:
            self.assertEqual(server.default_backend, "wolfram")
            session.assert_not_called()

    def test_compute_validation(self):
        self.assertEqual(self.post(QUINTIC, Origin="https://example.invalid")[0], 403)
        self.assertEqual(self.post(QUINTIC, Host="example.invalid")[0], 421)
        self.assertEqual(self.post(QUINTIC, **{"Content-Type": "text/plain"})[0], 415)
        self.assertEqual(self.post(" " * (MAX_COMPUTE_BODY + 1))[0], 413)
        for body in (
            '{"record_id":true,"properties":["Euler"]}',
            '{"record_id":0,"properties":["Euler"]}',
            '{"record_id":7890,"properties":["Euler","Euler"]}',
            '{"record_id":7890,"properties":["DefEqs"]}',
            '{"record_id":7890,"record_id":1,"properties":["Euler"]}',
            '{"record_id":7890,"properties":[{}]}',
            '{"record_id":7890,"properties":["Euler"],"backend":null}',
            '{"record_id":7890,"properties":["Euler"],"backend":"cloud"}',
            '{"record_id":7890,"properties":["Euler"],"extra":true}',
        ):
            with self.subTest(body=body):
                self.assertEqual(self.post(body)[0], 400)

    def test_explicit_kernel_call_and_busy_gate(self):
        body = {**QUINTIC, "backend": "wolfram"}
        evaluation = Evaluation(QUINTIC_VALUES, True, (), (), None, None)
        with patch.object(self.server.kernel, "call_result", return_value=evaluation) as kernel_call:
            status, _, payload = self.post(body, Origin=self.origin)
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(payload), {
                "source": "CIPro v1.0 Wolfram kernel", "backend": "wolfram", "properties": QUINTIC_VALUES,
            })
            kernel_call.assert_called_once_with(
                "CIProp", {"Conf": ((5,),), "DimPs": (4,)}, QUINTIC["properties"], backend="wolfram", Format="Medium",
            )
            with self.server.compute_lock:
                self.assertEqual(self.post(QUINTIC)[0], 409)

    def test_wolfram_missing_does_not_prevent_native_compute(self):
        with TemporaryDirectory() as directory:
            with CIPro(kernel=Path(directory) / "missing", backend="auto") as kernel:
                with patch.object(self.server, "kernel", kernel):
                    status, _, payload = self.post({**QUINTIC, "backend": "wolfram"})
                    self.assertEqual(status, 503)
                    self.assertIn("activated Wolfram kernel", json.loads(payload)["error"])
                    self.assertEqual(self.post(QUINTIC)[0], 200)

    def test_method_inventory_and_all_native_example_routes(self):
        status, _, payload = self.request("GET", "/api/methods")
        self.assertEqual(status, 200)
        methods = json.loads(payload)["methods"]
        self.assertEqual(len(methods), 162)
        self.assertEqual(len({(item["kind"], item["name"]) for item in methods}), 162)
        native = [item for item in methods if item["native"]]
        self.assertEqual(len(native), 148)
        self.assertTrue(all(item["runnable"] and item["example"] is not None for item in native))
        self.assertTrue(all(not item["runnable"] and item["example"] is None for item in methods if not item["native"]))
        servers = [self.server, *(self.start_server() for _ in range(3))]
        deadline = monotonic() + 180

        def replay(server, examples):
            results = []
            origin = f"http://127.0.0.1:{server.server_port}"
            for item in examples:
                payload = {"kind": item["kind"], "name": item["name"], "backend": "python", **item["example"]}
                remaining = deadline - monotonic()
                if remaining <= 0:
                    raise TimeoutError(f"Dashboard example replay exceeded 180 seconds before {item['name']}.")
                status, _, body = self.post(payload, "/api/run", server=server, timeout=min(10, remaining), Origin=origin)
                results.append((item, status, json.loads(body)))
            return results

        with patch.object(CIPro, "call_result") as kernel_call, ThreadPoolExecutor(max_workers=len(servers)) as pool:
            runs = [pool.submit(replay, server, native[index::len(servers)]) for index, server in enumerate(servers)]
            for run in runs:
                for item, status, result in run.result():
                    with self.subTest(kind=item["kind"], name=item["name"]):
                        self.assertEqual(status, 200, result)
                        self.assertEqual(result["backend"], "python")
                        self.assertIn("result", result)
            kernel_call.assert_not_called()

    def test_lab_request_validation(self):
        base = {"kind": "function", "name": "CICheck", "args": [{"Conf": [[5]]}], "options": {}}
        self.assertEqual(self.post(base, "/api/run", Origin="https://example.invalid")[0], 403)
        self.assertEqual(self.post(" " * (MAX_LAB_BODY + 1), "/api/run")[0], 413)
        for bad in (
            {**base, "name": "DeleteData"},
            {**base, "kind": "property"},
            {**base, "kind": "property", "name": "Euler", "args": []},
            {**base, "args": {}},
            {**base, "options": {"backend": "wolfram"}},
            {**base, "name": "Data", "args": ["Cicy4", 1]},
            {**base, "args": [{"$unknown": "invalid"}]},
        ):
            with self.subTest(payload=bad):
                self.assertEqual(self.post(bad, "/api/run")[0], 400)

    def test_auto_fallback_decodes_original_symbolic_tags_for_wolfram(self):
        geometry = {"Conf": [[2]], "DimPs": [1], "LBS": [[0]], "AmbCoords": [[{"$symbol": "a"}, {"$symbol": "b"}]]}
        body = {"kind": "modification", "name": "CohLBS", "args": [geometry], "options": {"Modulus": 3}}
        evaluation = Evaluation(((1,),), True, (), ("example output",), None, None)
        with patch.object(self.server.kernel, "call_result", return_value=evaluation) as kernel_call:
            status, _, _ = self.post({**body, "backend": "python"}, "/api/run")
            self.assertEqual(status, 422)
            kernel_call.assert_not_called()
            status, _, payload = self.post({**body, "backend": "auto"}, "/api/run")
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(payload), {
                "backend": "wolfram", "source": "CIPro v1.0 Wolfram kernel", "result": [[1]], "output": ["example output"],
            })
            decoded = {**geometry, "AmbCoords": [[getattr(wl, "Global`a"), getattr(wl, "Global`b")]]}
            kernel_call.assert_called_once_with("CIMod", decoded, "CohLBS", backend="wolfram", Modulus=3)

    def test_worker_timeout_releases_busy_gate_and_auto_does_not_fall_back(self):
        with patch.object(self.server.kernel, "call_result") as kernel_call:
            expired = subprocess.TimeoutExpired(cmd="worker", timeout=NATIVE_TIMEOUT)
            with patch("py_cipro.dashboard.subprocess.run", side_effect=expired):
                status, _, payload = self.post({**QUINTIC, "backend": "auto"})
                self.assertEqual(status, 504)
                self.assertIn("exceeded", json.loads(payload)["error"])
            kernel_call.assert_not_called()
        self.assertFalse(self.server.compute_lock.locked())
        self.assertEqual(self.post(QUINTIC)[0], 200)
