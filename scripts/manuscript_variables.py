"""Bind authored manuscript tokens to package registries and analysis receipts."""

from hashlib import sha256
from importlib.metadata import version
import json
from math import isfinite
from pathlib import Path
import re
import subprocess
import tomllib
from types import SimpleNamespace

from check_intersections import configuration_euler
from py_cipro import FUNCTIONS, MODIFICATIONS, PROPERTIES
from py_cipro._dashboard_examples import EXAMPLES
from py_cipro._native import NATIVE_FUNCTIONS, NATIVE_MODIFICATIONS, NATIVE_PROPERTIES
from py_cipro._release import RELEASE_COMMIT
from py_cipro._research_chern import polarized_invariants
from py_cipro.catalog import get_catalog


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def package_record(root, catalog):
    with (root / "pyproject.toml").open("rb") as metadata:
        project = tomllib.load(metadata)["project"]
    registries = (
        ("Public functions", FUNCTIONS, NATIVE_FUNCTIONS),
        ("Property keys", PROPERTIES, NATIVE_PROPERTIES),
        ("Modification keys", MODIFICATIONS, NATIVE_MODIFICATIONS),
    )
    examples = tuple(
        {name for example_kind, name in EXAMPLES if example_kind == kind}
        for kind in ("function", "property", "modification")
    )
    for (surface, released, native), cases in zip(registries, examples, strict=True):
        if not set(native) <= set(released) or set(native) != set(cases):
            raise ValueError(f"Registry and example inventory mismatch for {surface}")
    return {
        "name": project["name"],
        "version": project["version"],
        "license": project["license"],
        "requires_python": project["requires-python"],
        "dependencies": project["dependencies"],
        "console_scripts": project["scripts"],
        "method_surfaces": [
            {
                "surface": name,
                "released": len(released),
                "python": len(native),
                "wolfram_only": len(released) - len(native),
                "dashboard_examples": len(cases),
            }
            for (name, released, native), cases in zip(registries, examples, strict=True)
        ],
        "upstream": {
            "repository": "JamesGray-Physics/CIPro",
            "tag": catalog.release,
            "commit": RELEASE_COMMIT,
            "archive_sha256": catalog.sha256,
            "member_sha256": catalog.member_sha256,
        },
    }


def analysis_records(root, catalog):
    paths = {
        "archive": "data/cicy3-summary.json",
        "analytic_checks": "data/analytic-checks.json",
        "figure_analysis": "data/manuscript-analysis.json",
        "chern_audit": "data/chern-audit.json",
        "atlas_comparison": "data/atlas-comparison.json",
        "bicubic_exact": "data/bicubic-exact.json",
        "integral_invariants": "data/integral-invariants.json",
    }
    records = {name: load_json(root / path) for name, path in paths.items()}
    archive = records["archive"]
    checks = records["analytic_checks"]
    figures = records["figure_analysis"]["catalog"]
    if (
        archive["archive_sha256"] != catalog.sha256
        or archive["dataset_sha256"] != catalog.member_sha256
        or checks["dataset_sha256"] != catalog.member_sha256
        or archive["record_count"] != len(catalog.records)
        or checks["configuration_euler"]["groups"]["all"] != len(catalog.records)
        or figures["archive_sha256"] != catalog.sha256
        or figures["dataset_sha256"] != catalog.member_sha256
        or figures["records"] != len(catalog.records)
        or figures["products"] != archive["product_count"]
        or figures["nonproduct_hodge_pairs"] != archive["non_product_hodge_pair_count"]
        or figures["favourable_nonproduct_records"] + figures["favourable_product_records"] != archive["favourable_count"]
        or any(
            records[name]["dataset_sha256"] != catalog.member_sha256
            or records[name]["archive_sha256"] != catalog.sha256
            for name in ("chern_audit", "atlas_comparison", "bicubic_exact", "integral_invariants")
        )
        or records["bicubic_exact"]["native_receipt_sha256"]
        != sha256((root / paths["figure_analysis"]).read_bytes()).hexdigest()
        or records["integral_invariants"]["summary"]["records"]
        != len(catalog.records) - archive["product_count"]
        or records["integral_invariants"]["summary"]["hodge_groups"]
        != archive["non_product_hodge_pair_count"]
    ):
        raise ValueError("Archive summary and exact checks must bind the current release and population")
    return records, paths


def add_revision_variables(variables, records):
    chern = records["chern_audit"]["summary"]
    if chern["matched_records"] != chern["records"] or chern["records"] != records["archive"]["record_count"]:
        raise ValueError("The Chern audit must cover every archive record")
    variables["CHERN_MODAL_H11"], variables["CHERN_MODAL_H21"] = chern["modal_hodge"]
    for name, value in chern.items():
        if name != "modal_hodge":
            variables["CHERN_" + name.upper()] = (
                str(value) if name.endswith(("_id", "_volume", "_contraction", "_index")) else value
            )

    atlas = records["atlas_comparison"]["manuscript_values"]
    if any(not re.fullmatch(r"ATLAS_[A-Z0-9_]+", name) or name in variables for name in atlas):
        raise ValueError("Atlas manuscript values must use unique ATLAS_ tokens")
    variables.update(atlas)

    integral = records["integral_invariants"]["manuscript_values"]
    if any(not re.fullmatch(r"INTEGRAL_[A-Z0-9_]+", name) or name in variables for name in integral):
        raise ValueError("Integral invariants must use unique INTEGRAL_ tokens")
    variables.update(integral)

    exact = records["bicubic_exact"]["summary"]
    if (exact["points"] != exact["native_index_matches"]
        or exact["points"] != exact["native_supported_matches"] + exact["native_unsupported_resolved"]):
        raise ValueError("The exact bicubic audit must account for every plotted charge")
    for token, key in {
        "POINTS": "points",
        "SUPPORTED_MATCHES": "native_supported_matches",
        "INDEX_MATCHES": "native_index_matches",
        "UNSUPPORTED_RESOLVED": "native_unsupported_resolved",
        "MIXED_NONZERO": "mixed_nonzero",
        "JUMPING_POINTS": "jumping_points",
        "MAX_PAIRED_EXCESS": "max_paired_excess",
        "MAX_TOTAL": "max_intermediate_total",
        "WITNESS_PAIRED_EXCESS": "witness_paired_excess",
    }.items():
        variables["BICUBIC_EXACT_" + token] = exact[key]


def literature_comparison(variables):
    """Recompute the published split examples using the manuscript conventions."""
    presentations = {
        "original": ((2, 1, 3), ((2, 0, 1), (1, 1, 0), (0, 1, 3))),
        "split": ((1, 2, 1, 3), ((1, 1, 0, 0), (1, 1, 0, 1), (1, 0, 1, 0), (0, 0, 1, 3))),
    }
    split_evidence = {}
    for name, (dimensions, degrees) in presentations.items():
        record = SimpleNamespace(id=name, ambient_dimensions=dimensions, configuration=degrees)
        _, volume, pairing, sections = polarized_invariants(record)
        euler = configuration_euler(record)
        if euler != -90:
            raise ValueError(f"The published configuration {name} must have Euler characteristic -90")
        columns = "r|" + "r" * len(degrees[0])
        rows = r"\\".join("&".join(map(str, (dimension, *row)))
                          for dimension, row in zip(dimensions, degrees, strict=True))
        matrix = rf"\left[\begin{{array}}{{{columns}}}{rows}\end{{array}}\right]"
        for key, value in (
            ("MATRIX", matrix), ("VOLUME", volume), ("PAIRING", pairing), ("SECTIONS", sections),
        ):
            variables[f"LITERATURE_{name.upper()}_{key}"] = value
        split_evidence[name] = {
            "ambient_dimensions": dimensions, "configuration": degrees, "euler": euler,
            "volume": volume, "c2_pairing": pairing, "sections": sections,
        }
    variables["LITERATURE_SPLIT_EULER"] = split_evidence["split"]["euler"]
    lower_bound = 2590
    variables["LITERATURE_CICY_TOPOLOGY_LOWER_BOUND"] = lower_bound
    return {
        "ineffective_split": {
            "citation": "anderson-fibrations", "section": "2.1.2", "presentations": split_evidence,
        },
        "cicy_topology_lower_bound": {"citation": "he-candelas-count", "value": lower_bound},
    }


def add_figure_variables(variables, analysis):
    archive = analysis["catalog"]
    shape = archive["modal_shape"]
    quintic = analysis["cohomology"]["quintic"]
    bicubic = analysis["cohomology"]["bicubic"]
    if (
        quintic["points"] != quintic["cohomology_matches"]
        or quintic["points"] != quintic["index_matches"]
        or bicubic["points"] != bicubic["index_matches"]
        or bicubic["points"] != bicubic["supported"] + bicubic["unsupported"]
        or bicubic["supported"] != bicubic["h0_only"] + bicubic["h3_only"] + bicubic["acyclic"]
        or bicubic["supported"] != bicubic["supported_index_and_duality_matches"]
    ):
        raise ValueError("Line-bundle verification counts do not cover their claimed domains")
    variables.update({
        "SINGLETON_PAIR_COUNT": archive["singleton_pairs"],
        "TOP10_PAIR_RECORDS": archive["top10_records"],
        "PAIRS_TO_HALF": archive["pairs_to_half"],
        "MODAL_AMBIENT_FACTORS": shape["factors"],
        "MODAL_CODIMENSION": shape["codimension"],
        "MODAL_SHAPE_RECORDS": shape["records"],
        "NONPRODUCT_ZERO_EULER": archive["nonproduct_zero_euler"],
        "FAVOURABLE_NONPRODUCT_PERCENT": (
            f"{archive['favourable_nonproduct_records'] / archive['nonproduct_records']:.1%}"
        ),
        "BICUBIC_CHARGE_LIMIT": bicubic["charge_range_per_axis"][1],
        "BICUBIC_GRID_SIZE": bicubic["points"],
        "BICUBIC_SUPPORTED": bicubic["supported"],
        "BICUBIC_UNSUPPORTED": bicubic["unsupported"],
        "BICUBIC_H0_ONLY": bicubic["h0_only"],
        "BICUBIC_H3_ONLY": bicubic["h3_only"],
        "BICUBIC_ACYCLIC": bicubic["acyclic"],
        "QUINTIC_CHARGE_LIMIT": quintic["charge_range"][1],
        "QUINTIC_CHARGE_POINTS": quintic["points"],
    })


def fixture_rows(checks):
    rows = []
    for name, fixture in checks["fixtures"].items():
        hodge = f"({fixture['h11']}, {fixture['h21']})"
        c2 = ", ".join(map(str, fixture["c2_against_hyperplanes"]))
        triples = ", ".join(
            f"$d_{{{''.join(map(str, triple['indices']))}}}={triple['integral']}$"
            for triple in fixture["triple_intersections"] if triple["integral"]
        )
        rows.append(f"| {name.capitalize()} | {fixture['record']} | {hodge} | {fixture['euler']} | {c2} | {triples} |")
    return "\n".join(rows)


def as_text(value):
    if type(value) is int:
        return f"{value:,}"
    if type(value) is float and isfinite(value):
        return f"{value:,.12g}"
    if isinstance(value, str) and value.strip():
        return value
    raise ValueError(f"Empty or invalid manuscript variable value {value!r}")


def workflow_rows(root, software):
    rows = [
        f"| `{script}` | `{name}` |"
        for script, name in software["console_scripts"].items()
    ]
    for label, path in (
        ("Exact intersection audit", "scripts/check_intersections.py"),
        ("Atlas and charge-grid figures", "scripts/render_figures.py"),
        ("Chern and polarized index audit", "scripts/chern_audit.py"),
        ("Archive weighting comparisons", "scripts/atlas_comparison.py"),
        ("Exact bicubic cohomology", "scripts/bicubic_exact.py"),
        ("Integral divisor-lattice audit", "scripts/integral_invariants.py"),
        ("Cover graphical abstract", "scripts/render_graphical_abstract.py"),
        ("Manuscript hydration", "scripts/z_generate_manuscript_variables.py"),
    ):
        if not (root / path).is_file():
            raise ValueError(f"Missing manuscript workflow entry point {path}")
        rows.append(f"| {label} | `{path}` |")
    return "\n".join(rows)


def build_variables(root):
    catalog = get_catalog()
    software = package_record(root, catalog)
    analysis, paths = analysis_records(root, catalog)
    archive = analysis["archive"]
    checks = analysis["analytic_checks"]
    euler = archive["euler"]
    surfaces = software["method_surfaces"]
    totals = {
        key: sum(row[key] for row in surfaces)
        for key in ("released", "python", "wolfram_only", "dashboard_examples")
    }
    table = "\n".join(
        f"| {row['surface']} | {row['released']} | {row['python']} | {row['wolfram_only']} |"
        for row in surfaces
    )
    source_commit = subprocess.check_output(
        ["git", "rev-parse", "--verify", "HEAD"], cwd=root, stdin=subprocess.DEVNULL, text=True
    ).strip()
    variables = {
        "PACKAGE_NAME": software["name"],
        "PACKAGE_VERSION": software["version"],
        "PACKAGE_LICENSE": software["license"],
        "PYTHON_REQUIRES": software["requires_python"],
        "SOURCE_SHORT_COMMIT": source_commit[:12],
        "TEMPLATE_VERSION": version("research-project-template"),
        "UPSTREAM_TAG": catalog.release,
        "UPSTREAM_SHORT_COMMIT": RELEASE_COMMIT[:12],
        "ARCHIVE_SHORT_SHA256": catalog.sha256[:12],
        "CICY3_ARCHIVE_SHORT_SHA256": catalog.sha256[:12],
        "CICY3_MEMBER_SHORT_SHA256": catalog.member_sha256[:12],
        "RELEASED_TOTAL": totals["released"],
        "NATIVE_TOTAL": totals["python"],
        "WOLFRAM_ONLY_TOTAL": totals["wolfram_only"],
        "DASHBOARD_EXAMPLES": totals["dashboard_examples"],
        "METHOD_TABLE_ROWS": table,
        "SCRIPT_TABLE_ROWS": workflow_rows(root, software),
        "CICY3_RECORDS": archive["record_count"],
        "CICY3_CY_ROWS": len(catalog.records),
        "CICY3_NONPRODUCT_ROWS": archive["record_count"] - archive["product_count"],
        "CICY3_PRODUCT_ROWS": archive["product_count"],
        "CICY3_FAVOURABLE_ROWS": archive["favourable_count"],
        "HODGE_PAIR_COUNT": archive["hodge_pair_count"],
        "NONPRODUCT_HODGE_PAIR_COUNT": archive["non_product_hodge_pair_count"],
        "EULER_MIN": euler["min"],
        "EULER_MAX": euler["max"],
        "EULER_MEDIAN": euler["median"],
        "EULER_MODE": euler["mode"],
        "EULER_MODE_COUNT": euler["mode_count"],
        "EULER_VALUE_COUNT": euler["value_count"],
        "EULER_ZERO_COUNT": euler["zero_count"],
        "EULER_IDENTITY_CHECKS": euler["hodge_identity_matches"],
        "CICY3_TRUNCATED_RING_EULER_MATCHES": checks["configuration_euler"]["groups"]["all"],
        "QUINTIC_RECORD_ID": str(checks["fixtures"]["quintic"]["record"]),
        "BICUBIC_RECORD_ID": str(checks["fixtures"]["bicubic"]["record"]),
        "QUINTIC_EULER": checks["fixtures"]["quintic"]["euler"],
        "BICUBIC_EULER": checks["fixtures"]["bicubic"]["euler"],
        "FIXTURE_TABLE_ROWS": fixture_rows(checks),
    }
    for area, row in zip(("FUNCTIONS", "PROPERTIES", "MODIFICATIONS"), surfaces, strict=True):
        variables[f"NATIVE_{area}"] = row["python"]
        variables[f"RELEASED_{area}"] = row["released"]
    add_figure_variables(variables, analysis["figure_analysis"])
    add_revision_variables(variables, analysis)
    literature = literature_comparison(variables)
    formatted = {name: as_text(value) for name, value in variables.items()}
    evidence_paths = [
        "pyproject.toml",
        "manuscript/config.yaml",
        "src/py_cipro/_catalog.py",
        "src/py_cipro/_native.py",
        "src/py_cipro/_research_atlas.py",
        "src/py_cipro/_research_bicubic.py",
        "src/py_cipro/_research_chern.py",
        "src/py_cipro/_research_integral.py",
        "src/py_cipro/_research_integral.py",
        "src/py_cipro/_dashboard_examples.py",
        "src/py_cipro/_release.py",
        "src/py_cipro/catalog.py",
        "scripts/check_intersections.py",
        "scripts/chern_audit.py",
        "scripts/atlas_comparison.py",
        "scripts/bicubic_exact.py",
        "scripts/integral_invariants.py",
        "scripts/manuscript_analysis.py",
        "scripts/manuscript_variables.py",
        "scripts/render_figures.py",
        "scripts/render_graphical_abstract.py",
        "scripts/z_generate_manuscript_variables.py",
        *paths.values(),
    ]
    evidence = {
        "schema_version": "py-cipro-manuscript-evidence/v1",
        "source_commit": source_commit,
        "template_version": variables["TEMPLATE_VERSION"],
        "software": software,
        "analysis": paths,
        "literature": literature,
        "figures_sha256": {
            path.name: sha256(path.read_bytes()).hexdigest()
            for path in sorted((root / "manuscript" / "figures").glob("*.png"))
        },
        "inputs_sha256": {source: sha256((root / source).read_bytes()).hexdigest() for source in evidence_paths},
    }
    return formatted, evidence


def validate_tokens(root: Path, variables: dict[str, str]):
    """Require every authored token to have a nonempty computed value."""
    pattern = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")
    for path in sorted((root / "manuscript").glob("*.md")):
        keys = set(pattern.findall(path.read_text(encoding="utf-8")))
        missing = keys - variables.keys()
        if missing:
            raise ValueError(f"{path.name} lacks generated variables: {', '.join(sorted(missing))}")
