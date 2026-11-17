"""Read the pinned Cicy3 source member as data, with no Wolfram evaluation."""

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
import json
import re
from types import MappingProxyType

from ._release import RELEASE_SHA256, RELEASE_TAG, open_release

MEMBER = "CIProData/Cicy3"
MEMBER_SHA256 = "e6e61888281efc7bf4d0d1bd76b62c18c764f1028f17924b9ffe8edce9d6ec17"
RECORD_COUNT = 7890
_HEADER = "CIPro`CILoad="
_RECORD = re.compile(
    r'\s*<\|"Num"\s*->\s*(?P<id>[1-9][0-9]*),\s*'
    r'"Conf"\s*->\s*(?P<matrix>\{\{[0-9\s,{}]+\}\}),\s*'
    r'"Euler"\s*->\s*(?P<euler>-?[0-9]+),\s*'
    r'"H11"\s*->\s*(?P<h11>[0-9]+),\s*"H21"\s*->\s*(?P<h21>[0-9]+),\s*'
    r'"C"\s*->\s*(?P<chern>\{[-0-9\s,{}]+\}),\s*"GVBasic"\s*->\s*(?P<gv>\{[-0-9\s,{}]*\}),\s*'
    r'"Favour"\s*->\s*(?P<favourable>True|False),\s*'
    r'"IsProduct"\s*->\s*(?P<product>True|False),\s*'
    r'"KahlerPos"\s*->\s*(?P<kahler>True|False),\s*"IsSchoen"\s*->\s*(?P<schoen>True|False)\|>'
)
_BRACES = str.maketrans("{}", "[]")


@dataclass(frozen=True)
class Record:
    """One released configuration with archived invariants and derived ambient dimensions."""

    id: int
    h11: int
    h21: int
    euler: int
    favourable: bool
    product: bool
    configuration: tuple[tuple[int, ...], ...]
    ambient_dimensions: tuple[int, ...]

    def summary(self) -> dict:
        return {
            "id": self.id,
            "h11": self.h11,
            "h21": self.h21,
            "euler": self.euler,
            "favourable": self.favourable,
            "product": self.product,
        }


@dataclass(frozen=True)
class Catalog:
    """Cicy3 records in release order and their byte-level provenance."""

    records: tuple[Record, ...]
    dataset: str = "Cicy3"
    release: str = RELEASE_TAG
    sha256: str = RELEASE_SHA256
    member_sha256: str = MEMBER_SHA256

    def record(self, number: int) -> Record:
        """Get a record by its one-based archived Num key."""
        if type(number) is not int or not 1 <= number <= len(self.records):
            raise KeyError(number)
        return self.records[number - 1]


def _immutable(value):
    return tuple(_immutable(element) for element in value) if isinstance(value, list) else value


def _parse_catalog(text: str, *, source_rows: list | None = None) -> Catalog:
    text = text.strip()
    if not text.startswith(_HEADER):
        raise ValueError("Unexpected Cicy3 archive header")
    text = text[len(_HEADER):].strip()
    if not text.startswith("{") or not text.endswith("}"):
        raise ValueError("Cicy3 archive must contain a list of records")
    body = text[1:-1].strip()
    records = []
    offset = 0
    while offset < len(body):
        match = _RECORD.match(body, offset)
        number = len(records) + 1
        if match is None or int(match["id"]) != number:
            raise ValueError(f"Invalid Cicy3 record or archive order at {number}")
        matrix = tuple(tuple(row) for row in json.loads(match["matrix"].translate(_BRACES)))
        ambient = tuple(sum(row) - 1 for row in matrix)
        h11, h21, euler = (int(match[field]) for field in ("h11", "h21", "euler"))
        codimension = len(matrix[0])
        if (
            not codimension
            or any(len(row) != codimension for row in matrix)
            or min(ambient) < 1
            or sum(ambient) - codimension != 3
            or euler != 2 * (h11 - h21)
        ):
            raise ValueError(f"Inconsistent Cicy3 geometry or Euler characteristic at {number}")
        records.append(Record(
            id=number,
            h11=h11,
            h21=h21,
            euler=euler,
            favourable=match["favourable"] == "True",
            product=match["product"] == "True",
            configuration=matrix,
            ambient_dimensions=ambient,
        ))
        if source_rows is not None:
            source_rows.append(MappingProxyType({
                "Num": number,
                "Conf": matrix,
                "Euler": euler,
                "H11": h11,
                "H21": h21,
                "C": _immutable(json.loads(match["chern"].translate(_BRACES))),
                "GVBasic": _immutable(json.loads(match["gv"].translate(_BRACES))),
                "Favour": match["favourable"] == "True",
                "IsProduct": match["product"] == "True",
                "KahlerPos": match["kahler"] == "True",
                "IsSchoen": match["schoen"] == "True",
            }))
        offset = match.end()
        if offset < len(body):
            if body[offset] != "," or offset + 1 == len(body):
                raise ValueError(f"Invalid Cicy3 record separator after {number}")
            offset += 1
    if len(records) != RECORD_COUNT:
        raise ValueError(f"Expected {RECORD_COUNT} Cicy3 records, found {len(records)}")
    return Catalog(tuple(records))


def _read_member() -> str:
    with open_release() as package:
        data = package.read(MEMBER)
    if sha256(data).hexdigest() != MEMBER_SHA256:
        raise ValueError("Cicy3 member does not match its recorded SHA-256")
    return data.decode("ascii")


@lru_cache(maxsize=1)
def get_catalog() -> Catalog:
    """Load and validate the bundled textual threefold catalog."""
    return _parse_catalog(_read_member())


@lru_cache(maxsize=1)
def _cicy3_source_rows() -> tuple:
    rows = []
    _parse_catalog(_read_member(), source_rows=rows)
    return tuple(rows)
