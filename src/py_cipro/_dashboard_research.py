"""Bind manuscript figures and fresh native calculations to the released archive."""

from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from importlib.resources import files
import json
from math import gcd
import re
from urllib.parse import parse_qsl

from ._native_errors import NativeUnsupportedError
from ._research_atlas import atlas_comparison
from ._research_bicubic import COEFFICIENTS, bicubic_study_row
from ._research_chern import polarized_invariants
from ._research_cubic import SIGNATURE_KEYS, _ambient_index_values, _valid_signature, cubic_signature
from ._research_integral import integral_invariants
from .catalog import _cicy3_source_rows, get_catalog


INTEGRAL_STUDY = "integral-invariants"
CUBIC_STUDY = "cubic-refinement"
INDEX_STUDY = "index-divisibility"
COVER_PREVIEW_NAME = "graphical-abstract.png"
FIGURE_STUDIES = ("chern-audit", "atlas-comparison", "bicubic-exact", INTEGRAL_STUDY)
STUDY_NAMES = (*FIGURE_STUDIES, CUBIC_STUDY)
STUDY_DATA = tuple(f"{name}.json" for name in (*STUDY_NAMES, INDEX_STUDY))
PDF_NAMES = (
    "manuscript.pdf",
    "graphical-abstract.pdf",
    "cicy3-atlas.pdf",
    "cicy3-structure.pdf",
    "cicy3-multiplicity.pdf",
    "line-bundle-cohomology.pdf",
    *(f"{name}.pdf" for name in FIGURE_STUDIES),
)
ANALYSIS_NAME = "manuscript-analysis.json"
PROVENANCE_NAME = "provenance.json"
COHOMOLOGY_KEYS = {"quintic": ("k",), "bicubic": ("a", "b")}


@dataclass(frozen=True)
class ResearchBundle:
    bodies: dict[str, bytes]
    analysis: dict
    provenance: dict
    studies: dict
    index_divisibility: dict


@lru_cache(maxsize=1)
def research_bundle():
    """Read packaged assets by fixed name and check them against their manifest."""
    directory = files("py_cipro").joinpath("research_data")
    asset_names = (ANALYSIS_NAME, *PDF_NAMES, COVER_PREVIEW_NAME, *STUDY_DATA)
    bodies = {name: directory.joinpath(name).read_bytes() for name in (*asset_names, PROVENANCE_NAME)}
    provenance = json.loads(bodies[PROVENANCE_NAME])
    digests = {name: sha256(bodies[name]).hexdigest() for name in asset_names}
    if provenance.get("assets_sha256") != digests:
        raise ValueError("The bundled research asset digests do not match their provenance.")
    cover_studies = provenance["cover"]["studies_sha256"]
    if not cover_studies or any(digests.get(f"{name}.json") != digest or digest is None
                                for name, digest in cover_studies.items()):
        raise ValueError("The bundled graphical abstract uses a different study record.")
    analysis = json.loads(bodies[ANALYSIS_NAME])
    if analysis.get("schema_version") != 1:
        raise ValueError("The bundled research analysis uses an unsupported schema.")
    studies = {name: json.loads(bodies[f"{name}.json"]) for name in STUDY_NAMES}
    bicubic = studies["bicubic-exact"]
    if (bicubic["native_receipt_sha256"] != digests[ANALYSIS_NAME]
            or bicubic["record"] != analysis["cohomology"]["bicubic"]["record"]):
        raise ValueError("The exact bicubic study uses a different native receipt.")
    if bicubic["coefficient_matrix"] != [list(row) for row in COEFFICIENTS]:
        raise ValueError("The exact bicubic study uses a different smooth member.")
    catalog = get_catalog()
    _verify_integral_study(studies[INTEGRAL_STUDY], catalog)
    cubic, integral = studies[CUBIC_STUDY], studies[INTEGRAL_STUDY]
    _verify_cubic_study(cubic, integral, digests[f"{INTEGRAL_STUDY}.json"], catalog)
    index_divisibility = json.loads(bodies[f"{INDEX_STUDY}.json"])
    _verify_index_divisibility(index_divisibility, cubic, integral, digests[f"{CUBIC_STUDY}.json"], catalog)
    return ResearchBundle(bodies, analysis, provenance, studies, index_divisibility)


def _integral_pair(row):
    return row["cubic_content"], row["chern_content"]


def _cubic_values(row):
    return tuple(row[key] for key in SIGNATURE_KEYS)


def _matching_integral_cells(cells, expected):
    reported = {_integral_pair(cell): (cell["count"], cell["record_ids"]) for cell in cells}
    return len(reported) == len(cells) and reported == {key: (len(ids), ids) for key, ids in expected.items()}


def _verify_integral_study(study, catalog):
    """Check the plotted cells and source records once when the retained assets are read."""
    nonproducts = (record for record in catalog.records if not record.product)
    sources = _cicy3_source_rows()
    joint = defaultdict(list)
    hodge = defaultdict(lambda: defaultdict(list))
    euler = defaultdict(lambda: defaultdict(list))
    for row, record in zip(study["rows"], nonproducts, strict=True):
        hodge_pair = (record.h11, record.h21)
        rank = len(record.ambient_dimensions)
        source = sources[record.id - 1]
        if (
            (row["id"], row["ambient_factors"], row["favourable"], tuple(row["hodge"]), row["euler"])
            != (record.id, rank, record.favourable, hodge_pair, record.euler)
            or tuple(row["c2"]) != source["C"][1] or len(row["hyperplane_indices"]) != rank
            or row["chern_content"] != gcd(*row["c2"])
            or type(row["cubic_content"]) is not int or row["cubic_content"] < 1
        ):
            raise ValueError("The integral-lattice study does not match the CICY3 source rows.")
        pair = _integral_pair(row)
        joint[pair].append(record.id)
        hodge[hodge_pair][pair].append(record.id)
        euler[record.euler][pair].append(record.id)
    if not _matching_integral_cells(study["joint"], joint):
        raise ValueError("The integral-lattice plot counts do not match the source rows.")
    summary = study["summary"]
    if (summary["records"], summary["joint_pairs"], summary["hodge_groups"], summary["euler_groups"],
        summary["split_hodge_groups"], summary["split_euler_groups"]) != (
        len(study["rows"]), len(joint), len(hodge), len(euler),
        sum(len(cells) > 1 for cells in hodge.values()),
        sum(len(cells) > 1 for cells in euler.values()),
    ):
        raise ValueError("The integral-lattice summary does not match the plotted cohorts.")
    for key, cohorts in (("hodge", hodge), ("euler", euler)):
        reported = {(tuple(group[key]) if key == "hodge" else group[key]): group["cells"] for group in study[key]}
        if (
            len(reported) != len(study[key]) or reported.keys() != cohorts.keys()
            or any(not _matching_integral_cells(reported[value], cells) for value, cells in cohorts.items())
        ):
            raise ValueError("The integral-lattice cohort counts do not match the source rows.")
    rows = {row["id"]: row for row in study["rows"]}
    for witness in study["witness"]:
        reference = rows[witness["id"]]
        record = catalog.record(witness["id"])
        if (
            any(witness[key] != value for key, value in reference.items())
            or record.ambient_dimensions != (witness["ambient_dimension"],)
            or record.configuration != (tuple(witness["degrees"]),)
        ):
            raise ValueError("The integral-lattice witness does not match its source record.")


def _verify_cubic_study(study, integral, integral_digest, catalog):
    """Bind the refined signatures, cohort counts, and witnesses to Figure 6's source rows."""
    if (
        study["schema_version"] != 1 or tuple(study["signature_order"]) != SIGNATURE_KEYS
        or study["integral_receipt_sha256"] != integral_digest
    ):
        raise ValueError("The cubic refinement uses a different ambient lattice receipt.")
    joint = Counter()
    signatures_by_hodge = defaultdict(set)
    old_pairs_by_hodge = defaultdict(set)
    refined_by_pair = defaultdict(set)
    refined_by_hodge_and_pair = defaultdict(set)
    by_id = {}
    for row, prior in zip(study["rows"], integral["rows"], strict=True):
        signature = _cubic_values(row)
        pair = _integral_pair(prior)
        if (
            row.keys() != {"id", *SIGNATURE_KEYS} or row["id"] != prior["id"]
            or (signature[0], signature[3]) != pair or not _valid_signature(signature)
        ):
            raise ValueError("A refined cubic signature does not match its integral-lattice row.")
        hodge = tuple(prior["hodge"])
        joint[signature] += 1
        signatures_by_hodge[hodge].add(signature)
        old_pairs_by_hodge[hodge].add(pair)
        refined_by_pair[pair].add(signature)
        refined_by_hodge_and_pair[hodge, pair].add(signature)
        by_id[row["id"]] = (row, prior)
    reported_joint = {tuple(cell["signature"]): cell["count"] for cell in study["joint"]}
    if len(reported_joint) != len(study["joint"]) or reported_joint != joint:
        raise ValueError("The cubic refinement counts do not match its source signatures.")
    expected_summary = {
        "records": len(by_id),
        "joint_pairs": len(refined_by_pair),
        "joint_quadruples": len(joint),
        "hodge_groups": len(signatures_by_hodge),
        "split_by_pair": sum(len(pairs) > 1 for pairs in old_pairs_by_hodge.values()),
        "split_by_quadruple": sum(len(signatures) > 1 for signatures in signatures_by_hodge.values()),
        "pair_cells_refined": sum(len(signatures) > 1 for signatures in refined_by_pair.values()),
        "hodge_pair_cells": len(refined_by_hodge_and_pair),
        "hodge_pair_cells_refined": sum(len(signatures) > 1 for signatures in refined_by_hodge_and_pair.values()),
        "hodge_groups_refined": sum(
            len(signatures) > len(old_pairs_by_hodge[hodge]) for hodge, signatures in signatures_by_hodge.items()
        ),
    }
    if study["summary"] != expected_summary:
        raise ValueError("The cubic refinement summary does not match its source signatures.")
    for key, differs in (("witness", "d2"), ("diagonal_witness", "d3")):
        first, second = study[key]
        shared = {"hodge", "euler", *SIGNATURE_KEYS} - {differs}
        if any(first[name] != second[name] for name in shared) or first[differs] == second[differs]:
            raise ValueError("The cubic witnesses do not exhibit the stated refinement.")
        for witness in (first, second):
            row, prior = by_id[witness["id"]]
            record = catalog.record(witness["id"])
            if (
                any(witness[name] != value for name, value in row.items())
                or any(witness[name] != prior[name] for name in ("hodge", "euler", "favourable", "c2"))
                or record.ambient_dimensions != tuple(witness["ambient_dimensions"])
                or record.configuration != tuple(tuple(degrees) for degrees in witness["configuration"])
            ):
                raise ValueError("The cubic witness does not match its archive record.")


def _verify_index_divisibility(study, cubic, integral, cubic_digest, catalog):
    """Bind the index receipt and comparison witnesses to the exact archive cohorts."""
    if (
        study["schema_version"] != 1 or study["dataset"] != catalog.dataset
        or study["cubic_refinement_sha256"] != cubic_digest
        or tuple(study["signature_order"]) != (*SIGNATURE_KEYS, "index_divisor")
    ):
        raise ValueError("The index-divisibility audit uses a different cubic refinement receipt.")
    divisors = Counter()
    joint = Counter()
    hodge_signatures = defaultdict(set)
    hodge_extended = defaultdict(set)
    by_id = {}
    for row, signature_row, lattice in zip(study["rows"], cubic["rows"], integral["rows"], strict=True):
        record_id, divisor = row["id"], row["index_divisor"]
        if (
            row.keys() != {"id", "index_divisor"} or record_id != signature_row["id"]
            or type(divisor) is not int or divisor < 1
            or any(index % divisor for index in lattice["hyperplane_indices"])
        ):
            raise ValueError("An index divisor does not match its ambient lattice row.")
        hodge = tuple(lattice["hodge"])
        signature = _cubic_values(signature_row)
        extended = (*signature, divisor)
        divisors[divisor] += 1
        joint[extended] += 1
        hodge_signatures[hodge].add(signature)
        hodge_extended[hodge].add(extended)
        by_id[record_id] = (divisor, signature, lattice)
    expected_distribution = [{"value": value, "count": count} for value, count in sorted(divisors.items())]
    expected_joint = [{"signature": list(signature), "count": count} for signature, count in sorted(joint.items())]
    summary = study["summary"]
    if (
        study["distribution"] != expected_distribution or study["joint"] != expected_joint
        or summary["records"] != len(by_id) or summary["nonunit_records"] != len(by_id) - divisors[1]
        or summary["signatures_before"] != cubic["summary"]["joint_quadruples"]
        or summary["signatures_after"] != len(joint)
        or summary["hodge_groups_refined"] != sum(
            len(hodge_extended[hodge]) > len(signatures) for hodge, signatures in hodge_signatures.items()
        )
    ):
        raise ValueError("The index-divisibility counts do not match the archived signatures.")
    first, second = study["witness"]
    if (
        (first["id"], second["id"]) != (7626, 7635)
        or any(first[key] != second[key] for key in ("hodge", "euler", "signature", "favourable"))
        or first["index_divisor"] == second["index_divisor"]
    ):
        raise ValueError("The index witnesses do not exhibit the stated comparison.")
    for witness in (first, second):
        record = catalog.record(witness["id"])
        divisor, signature, lattice = by_id[record.id]
        if (
            witness["index_divisor"] != divisor or tuple(witness["signature"]) != signature
            or any(witness[key] != lattice[key] for key in ("hodge", "euler", "favourable", "hyperplane_indices"))
            or record.ambient_dimensions != tuple(witness["ambient_dimensions"])
            or record.configuration != tuple(tuple(degrees) for degrees in witness["configuration"])
        ):
            raise ValueError("An index witness does not match its source record.")


def verify_catalog_binding(bundle, catalog):
    metadata = bundle.analysis["catalog"]
    if (
        (metadata["dataset"], metadata["release"], metadata["records"])
        != (catalog.dataset, catalog.release, len(catalog.records))
        or metadata["archive_sha256"] != catalog.sha256
        or metadata["dataset_sha256"] != catalog.member_sha256
        or bundle.provenance["archive_sha256"] != catalog.sha256
        or bundle.provenance["dataset_sha256"] != catalog.member_sha256
        or any(study["archive_sha256"] != catalog.sha256 or study["dataset_sha256"] != catalog.member_sha256
               for study in (*bundle.studies.values(), bundle.index_divisibility))
    ):
        raise ValueError("The bundled research analysis does not match the dashboard's Cicy3 archive.")


def _query_fields(query):
    if len(query) > 128:
        raise ValueError("The research selection is too long.")
    pairs = parse_qsl(query, keep_blank_values=True, strict_parsing=True, max_num_fields=7)
    fields = dict(pairs)
    if len(fields) != len(pairs):
        raise ValueError("Supply each research selection field once.")
    return fields


def _number(value):
    if not re.fullmatch(r"-?(0|[1-9][0-9]{0,4})", value):
        raise ValueError("Research selection coordinates must be integers.")
    return int(value)


def _flag(fields, key):
    if key not in fields:
        return None
    if fields[key] not in ("0", "1"):
        raise ValueError(f"{key} must be 0 or 1.")
    return fields[key] == "1"


def _atlas_selection(fields, records):
    if fields.keys() == {"h11", "h21"}:
        pair = (_number(fields["h11"]), _number(fields["h21"]))
        selected = [row.id for row in records if not row.product and (row.h11, row.h21) == pair]
        return selected, f"Hodge pair {pair}"
    if fields.keys() in ({"euler"}, {"euler", "product"}):
        euler = _number(fields["euler"])
        product = _flag(fields, "product")
        selected = [row.id for row in records if row.euler == euler and (product is None or row.product == product)]
        label = f"Euler characteristic {euler}"
        if product is not None:
            label += " · products" if product else " · non-products"
        return selected, label
    raise ValueError("Select a Hodge pair or an Euler characteristic.")


def _structure_selection(fields, records):
    if fields.keys() not in ({"factors"}, {"factors", "codimension"}, {"factors", "favourable"}):
        raise ValueError("Select the ambient factor count and optional codimension or favorability.")
    factors = _number(fields["factors"])
    if "codimension" in fields:
        codimension = _number(fields["codimension"])
        selected = [
            row.id for row in records
            if len(row.ambient_dimensions) == factors and len(row.configuration[0]) == codimension
        ]
        return selected, f"Configuration shape {factors} × {codimension}"
    favourable = _flag(fields, "favourable")
    selected = [
        row.id for row in records if not row.product and len(row.ambient_dimensions) == factors
        and (favourable is None or row.favourable == favourable)
    ]
    label = f"{factors} ambient factors · non-products"
    if favourable is not None:
        label += " · marked favorable" if favourable else " · not marked favorable"
    return selected, label


def _multiplicity_selection(fields, analysis, records):
    ranked = analysis["catalog"]["hodge_pairs"]
    if fields.keys() == {"rank"}:
        rank = _number(fields["rank"])
        if not 1 <= rank <= len(ranked):
            raise ValueError("Choose a Hodge-pair rank in the plotted range.")
        chosen, label = ranked[rank - 1:rank], f"Multiplicity rank {rank}"
    elif fields.keys() == {"through"}:
        through = _number(fields["through"])
        if not 1 <= through <= len(ranked):
            raise ValueError("Choose a Hodge-pair rank in the plotted range.")
        chosen, label = ranked[:through], f"Multiplicity ranks 1–{through}"
    elif fields.keys() in ({"min"}, {"min", "max"}):
        lower = _number(fields["min"])
        upper = _number(fields["max"]) if "max" in fields else None
        if lower < 1 or (upper is not None and upper < lower):
            raise ValueError("Choose a positive multiplicity range.")
        chosen = [pair for pair in ranked if lower <= pair["records"] and (upper is None or pair["records"] <= upper)]
        label = f"Hodge-pair multiplicity {lower}+" if upper is None else f"Hodge-pair multiplicity {lower}–{upper}"
    else:
        raise ValueError("Choose one Hodge-pair rank, prefix, or multiplicity range.")
    expected = {(row["h11"], row["h21"]): row["records"] for row in chosen}
    matches = [row for row in records if not row.product and (row.h11, row.h21) in expected]
    if Counter((row.h11, row.h21) for row in matches) != expected:
        raise ValueError("The plotted Hodge-pair counts do not match the bundled archive.")
    return [row.id for row in matches], label


def _chern_selection(fields, study):
    if fields.keys() not in ({"volume", "pairing"}, {"volume", "pairing", "modal"}):
        raise ValueError("Select a polarized degree and Chern pairing.")
    volume, pairing = _number(fields["volume"]), _number(fields["pairing"])
    modal = _flag(fields, "modal")
    hodge = study["summary"]["modal_hodge"]
    ids = [
        row["id"] for row in study["rows"]
        if not row["product"] and (not modal or row["hodge"] == hodge)
        and row["volume"] == volume and row["c2_polarized"] == pairing
    ]
    label = f"Polarized degree {volume} · Chern pairing {pairing}"
    if modal:
        label += f" · Hodge pair {tuple(hodge)}"
    return ids, label


def _atlas_comparison_selection(fields, records):
    if not fields:
        return [row.id for row in records if not row.product], "Atlas weighting · all non-products"
    if fields.keys() == {"euler"}:
        threshold = _number(fields["euler"])
        return (
            [row.id for row in records if not row.product and row.euler <= threshold],
            f"Atlas weighting · Euler characteristic ≤ {threshold}",
        )
    if fields.keys() in ({"factors"}, {"factors", "favourable"}):
        return _structure_selection(fields, records)
    raise ValueError("Select an Euler threshold, an ambient factor count, or the full weighting study.")


def _study_record(study, record_id):
    reference = next((row for row in study["rows"] if row["id"] == record_id), None)
    if reference is None:
        raise ValueError("Select an archived non-product CICY3 record from the study.")
    return reference


def _integral_selection(fields, study):
    if fields.keys() == {"record_id"}:
        record_id = _number(fields["record_id"])
        reference = _study_record(study, record_id)
        cubic, chern = _integral_pair(reference)
        return [record_id], f"Record {record_id} · cubic content {cubic} · Chern content {chern}"

    required = {"cubic_content", "chern_content"}
    if fields.keys() not in (required, required | {"h11", "h21"}, required | {"euler"}):
        raise ValueError("Select both lattice contents and optionally a Hodge pair or Euler characteristic.")
    cubic, chern = (_number(fields[key]) for key in ("cubic_content", "chern_content"))
    if cubic < 1 or chern < 0:
        raise ValueError("Cubic content must be positive and Chern content nonnegative.")
    label = f"Cubic content {cubic} · Chern content {chern}"
    cells = study["joint"]
    if "h11" in fields:
        hodge = [_number(fields["h11"]), _number(fields["h21"])]
        cells = next((group["cells"] for group in study["hodge"] if group["hodge"] == hodge), [])
        label += f" · Hodge pair {tuple(hodge)}"
    elif "euler" in fields:
        euler = _number(fields["euler"])
        cells = next((group["cells"] for group in study["euler"] if group["euler"] == euler), [])
        label += f" · Euler characteristic {euler}"
    ids = next((cell["record_ids"] for cell in cells if _integral_pair(cell) == (cubic, chern)), [])
    return ids, label


def _cubic_selection(fields, study, catalog):
    if fields.keys() == {"record_id"}:
        record_id = _number(fields["record_id"])
        reference = _study_record(study, record_id)
        return [record_id], f"Record {record_id} · cubic signature {_cubic_values(reference)}"

    required = set(SIGNATURE_KEYS)
    if fields.keys() not in (required, required | {"h11", "h21"}, required | {"euler"}):
        raise ValueError("Select all four cubic signature coordinates and optionally a Hodge pair or Euler value.")
    signature = tuple(_number(fields[key]) for key in SIGNATURE_KEYS)
    if min(signature[:3]) < 1 or signature[3] < 0:
        raise ValueError("Cubic signature coordinates must be positive, with a nonnegative Chern content.")
    ids = [row["id"] for row in study["rows"] if _cubic_values(row) == signature]
    label = f"Cubic signature {signature}"
    if "h11" in fields:
        hodge = tuple(_number(fields[key]) for key in ("h11", "h21"))
        records = (catalog.record(number) for number in ids)
        ids = [record.id for record in records if (record.h11, record.h21) == hodge]
        label += f" · Hodge pair {hodge}"
    elif "euler" in fields:
        euler = _number(fields["euler"])
        ids = [number for number in ids if catalog.record(number).euler == euler]
        label += f" · Euler characteristic {euler}"
    return ids, label


def record_selection(query, analysis, catalog, studies=None, index_divisibility=None):
    fields = _query_fields(query)
    figure = fields.pop("figure", None)
    if figure == "atlas":
        ids, label = _atlas_selection(fields, catalog.records)
    elif figure == "structure":
        ids, label = _structure_selection(fields, catalog.records)
    elif figure == "multiplicity":
        ids, label = _multiplicity_selection(fields, analysis, catalog.records)
    elif figure == "cohomology" and fields.keys() == {"geometry"} and fields["geometry"] in COHOMOLOGY_KEYS:
        name = fields["geometry"]
        record = catalog.record(analysis["cohomology"][name]["record"])
        ids, label = [record.id], f"{name.capitalize()} · cohomology sweep"
    elif figure == "chern-audit" and studies is not None:
        ids, label = _chern_selection(fields, studies[figure])
    elif figure == "atlas-comparison" and studies is not None:
        ids, label = _atlas_comparison_selection(fields, catalog.records)
    elif figure == "bicubic-exact" and not fields and studies is not None:
        record = catalog.record(studies[figure]["record"])
        ids, label = [record.id], "Bicubic · source configuration for the specified smooth member"
    elif figure == INTEGRAL_STUDY and studies is not None:
        ids, label = _integral_selection(fields, studies[figure])
    elif figure == CUBIC_STUDY and studies is not None:
        ids, label = _cubic_selection(fields, studies[figure], catalog)
    elif figure == INDEX_STUDY and fields.keys() == {"record_id"} and index_divisibility is not None:
        record_id = _number(fields["record_id"])
        reference = _study_record(index_divisibility, record_id)
        ids, label = [record_id], f'Record {record_id} · ambient index gcd {reference["index_divisor"]}'
    else:
        raise ValueError("Choose a valid manuscript figure selection.")
    return {"ids": ids, "matched": len(ids), "label": label}


def prepare_cohomology(payload, analysis, catalog):
    if not isinstance(payload, dict) or payload.get("figure") != "cohomology":
        raise ValueError("Select a cohomology sweep.")
    name = payload.get("geometry")
    if not isinstance(name, str) or name not in COHOMOLOGY_KEYS:
        raise ValueError("Select the quintic or bicubic geometry.")
    keys = COHOMOLOGY_KEYS[name]
    if payload.keys() != {"figure", "geometry", *keys} or any(type(payload[key]) is not int for key in keys):
        raise ValueError("Supply the integer charge coordinates for the selected geometry.")
    charges = [payload[key] for key in keys]
    sweep = analysis["cohomology"][name]
    row = next((row for row in sweep["rows"] if [row[key] for key in keys] == charges), None)
    if row is None:
        raise ValueError("Choose charges within the plotted manuscript sweep.")
    record = catalog.record(sweep["record"])
    geometry = {
        "Conf": record.configuration,
        "DimPs": record.ambient_dimensions,
        "LBS": [[charge] for charge in charges],
    }
    reference = {key: row[key] for key in ("index", "dimensions")}
    reference["status"] = row.get("status", "supported")
    return {
        "research": "cohomology", "geometry": geometry, "record_id": record.id,
        "charges": charges, "manuscript": reference,
    }


def _study_values(payload, keys):
    if payload.keys() != {"figure", *keys} or any(type(payload[key]) is not int for key in keys):
        raise ValueError("Supply only the integer coordinates for the selected study.")
    return tuple(payload[key] for key in keys)


def _atlas_comparison_result(analysis, selector):
    if not selector:
        return analysis["summary"]
    if "euler" in selector:
        collection, key = "euler_cdf", "euler"
        coordinate = selector["euler"]
    else:
        collection, key = "ambient_factor_groups", "ambient_factors"
        coordinate = selector["factors"]
    value = next((row for row in analysis[collection] if row[key] == coordinate), None)
    if value is None:
        raise ValueError("Choose a threshold or factor count within the plotted comparison.")
    return value


def prepare_research(payload, bundle, catalog):
    """Validate a public request before passing a fixed operation to the Python worker."""
    if not isinstance(payload, dict) or not isinstance(payload.get("figure"), str):
        raise ValueError("Select a manuscript figure for the calculation.")
    figure = payload["figure"]
    if figure == "cohomology":
        return prepare_cohomology(payload, bundle.analysis, catalog)
    if figure == INDEX_STUDY:
        (record_id,) = _study_values(payload, ("record_id",))
        row = _study_record(bundle.index_divisibility, record_id)
        lattice = _study_record(bundle.studies[INTEGRAL_STUDY], record_id)
        reference = {**row, "hyperplane_indices": lattice["hyperplane_indices"]}
        return {"research": figure, "record_id": record_id, "manuscript": reference}
    if figure not in STUDY_NAMES:
        raise ValueError("Choose an available manuscript study.")
    study = bundle.studies[figure]
    if figure == "chern-audit":
        (record_id,) = _study_values(payload, ("record_id",))
        if not 1 <= record_id <= len(catalog.records):
            raise ValueError("Select a record ID within the CICY3 archive.")
        reference = study["rows"][record_id - 1]
        if reference["id"] != record_id:
            raise ValueError("The Chern audit does not match the requested archive record.")
        return {
            "research": figure, "record_id": record_id,
            "manuscript": {key: reference[key] for key in ("volume", "c2_polarized", "index", "c2")},
        }
    if figure == "atlas-comparison":
        keys = tuple(payload.keys() - {"figure"})
        if keys not in ((), ("euler",), ("factors",)):
            raise ValueError("Select one plotted Euler threshold or ambient factor count.")
        selector = dict(zip(keys, _study_values(payload, keys), strict=True))
        return {"research": figure, "selector": selector, "manuscript": _atlas_comparison_result(study, selector)}
    if figure in (INTEGRAL_STUDY, CUBIC_STUDY):
        (record_id,) = _study_values(payload, ("record_id",))
        return {"research": figure, "record_id": record_id, "manuscript": _study_record(study, record_id)}
    a, b = _study_values(payload, ("a", "b"))
    reference = next((row for row in study["rows"] if (row["a"], row["b"]) == (a, b)), None)
    if reference is None:
        raise ValueError("Choose charges within the plotted smooth bicubic study.")
    return {"research": figure, "record_id": study["record"], "charges": [a, b], "manuscript": reference}


def recompute_study(payload):
    """Evaluate one exact study in the native worker with the pinned data and equation."""
    figure, manuscript = payload["research"], payload["manuscript"]
    identity = {"record_id": payload["record_id"]} if "record_id" in payload else {}
    if figure == "chern-audit":
        c2, volume, pairing, index = polarized_invariants(get_catalog().record(payload["record_id"]))
        result = {"volume": volume, "c2_polarized": pairing, "index": index, "c2": c2}
        source = "Exact ambient intersection contractions with the all-ones polarization."
    elif figure == "atlas-comparison":
        result = _atlas_comparison_result(atlas_comparison(get_catalog()), payload["selector"])
        source = "Exact rational weighting of the non-product CICY3 presentations."
    elif figure == "bicubic-exact":
        a, b = payload["charges"]
        result = bicubic_study_row(a, b, manuscript["native_supported"])
        source = "Exact rational ranks for the manuscript's specified smooth bicubic."
    elif figure == INTEGRAL_STUDY:
        record_id = payload["record_id"]
        record = get_catalog().record(record_id)
        result = integral_invariants(record, _cicy3_source_rows()[record_id - 1])
        source = "Exact ambient cubic and second Chern content with Riemann–Roch checks."
    elif figure == CUBIC_STUDY:
        result = cubic_signature(payload["record_id"])
        source = "Exact cubic signature from the archived configuration and ambient integral divisor lattice."
    elif figure == INDEX_STUDY:
        record_id = payload["record_id"]
        divisor, indices = _ambient_index_values(record_id)
        result = {"id": record_id, "index_divisor": divisor, "hyperplane_indices": indices}
        source = "Exact ambient Riemann–Roch indices and fixed divisor from the archived configuration."
    else:
        raise ValueError("Unknown manuscript study.")
    return {
        "backend": "python", "source": source, **identity,
        "result": result, "manuscript": manuscript, "matches_manuscript": result == manuscript,
    }


def recompute_cohomology(client, payload):
    """Run the same native methods used by the manuscript on a fresh geometry."""
    geometry = payload["geometry"]
    index = client.property(geometry, "IndLBS", Format="Short")
    if int(index) != index:
        raise ValueError("CIPro returned a non-integral line-bundle index.")
    index = int(index)
    details = {}
    try:
        native_dimensions = [row[0] for row in client.modify(geometry, "CohLBS", CohSum=False)]
    except NativeUnsupportedError as exc:
        dimensions = None
        status = "unsupported"
        details["reason"] = str(exc)[:800]
    else:
        dimensions = [int(value) for value in native_dimensions]
        if len(dimensions) != 4 or dimensions != native_dimensions or any(value < 0 for value in dimensions):
            raise ValueError("CIPro returned invalid threefold cohomology dimensions.")
        if len(payload["charges"]) == 1 or dimensions[1] or dimensions[2] or dimensions[0] and dimensions[3]:
            status = "supported"
        else:
            status = "h0_only" if dimensions[0] else "h3_only" if dimensions[3] else "acyclic"
    current = {"dimensions": dimensions, "index": index, "status": status}
    return {
        "backend": "python", "source": "CIPro v1.0 Python equivalent",
        "record_id": payload["record_id"], "charges": payload["charges"], **current, **details,
        "manuscript": payload["manuscript"], "matches_manuscript": current == payload["manuscript"],
    }
