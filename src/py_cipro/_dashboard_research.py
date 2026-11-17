"""Bind manuscript figures and fresh native calculations to the released archive."""

from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from importlib.resources import files
import json
import re
from urllib.parse import parse_qsl

from ._native_errors import NativeUnsupportedError


PDF_NAMES = (
    "manuscript.pdf",
    "cicy3-atlas.pdf",
    "cicy3-structure.pdf",
    "cicy3-multiplicity.pdf",
    "line-bundle-cohomology.pdf",
)
ANALYSIS_NAME = "manuscript-analysis.json"
PROVENANCE_NAME = "provenance.json"
COHOMOLOGY_KEYS = {"quintic": ("k",), "bicubic": ("a", "b")}


@dataclass(frozen=True)
class ResearchBundle:
    bodies: dict[str, bytes]
    analysis: dict
    provenance: dict


@lru_cache(maxsize=1)
def research_bundle():
    """Read packaged assets by fixed name and check them against their manifest."""
    directory = files("py_cipro").joinpath("research_data")
    bodies = {name: directory.joinpath(name).read_bytes() for name in (
        ANALYSIS_NAME, PROVENANCE_NAME, *PDF_NAMES,
    )}
    provenance = json.loads(bodies[PROVENANCE_NAME])
    digests = {name: sha256(bodies[name]).hexdigest() for name in (ANALYSIS_NAME, *PDF_NAMES)}
    if provenance.get("assets_sha256") != digests:
        raise ValueError("The bundled research asset digests do not match their provenance.")
    analysis = json.loads(bodies[ANALYSIS_NAME])
    if analysis.get("schema_version") != 1:
        raise ValueError("The bundled research analysis uses an unsupported schema.")
    return ResearchBundle(bodies, analysis, provenance)


def verify_catalog_binding(bundle, catalog):
    metadata = bundle.analysis["catalog"]
    if (
        (metadata["dataset"], metadata["release"], metadata["records"])
        != (catalog.dataset, catalog.release, len(catalog.records))
        or metadata["archive_sha256"] != catalog.sha256
        or metadata["dataset_sha256"] != catalog.member_sha256
        or bundle.provenance["archive_sha256"] != catalog.sha256
        or bundle.provenance["dataset_sha256"] != catalog.member_sha256
    ):
        raise ValueError("The bundled research analysis does not match the dashboard's Cicy3 archive.")


def _query_fields(query):
    if len(query) > 128:
        raise ValueError("The research selection is too long.")
    pairs = parse_qsl(query, keep_blank_values=True, strict_parsing=True, max_num_fields=5)
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


def record_selection(query, analysis, catalog):
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
    else:
        raise ValueError("Choose an atlas, structure, multiplicity, or cohomology selection.")
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
