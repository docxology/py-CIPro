"""Load the exact GitHub release asset and relocate its application paths."""

from hashlib import sha256
from importlib.resources import files
from pathlib import Path, PurePosixPath
from shutil import copyfileobj
from zipfile import ZipFile

RELEASE_TAG = "v1.0"
RELEASE_SHA256 = "39223db768893c958be776071bcbf86d0ef5692f92e1ab153ef1ce8d3440dd53"
APPLICATION_ROOT_SYMBOL = "CIPro`Private`$PyCIProApplicationRoot"


def prepare_application(root: Path) -> Path:
    """Extract to a fresh session directory and return its relocated CIPro.m."""
    archive = files("py_cipro").joinpath("vendor", "CIProPackage.zip")
    with archive.open("rb") as stream:
        digest = sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
        if digest.hexdigest() != RELEASE_SHA256:
            raise ValueError("Bundled CIPro release does not match its recorded SHA-256")
        stream.seek(0)
        with ZipFile(stream) as package:
            for entry in package.infolist():
                relative = PurePosixPath(entry.filename)
                if relative.is_absolute() or ".." in relative.parts or "\\" in entry.filename:
                    raise ValueError(f"Invalid CIPro archive member {entry.filename!r}")
                destination = root.joinpath(*relative.parts)
                if entry.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                else:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with package.open(entry) as source, destination.open("xb") as target:
                        copyfileobj(source, target)

    source = root / "CIPro.m"
    original = source.read_bytes()
    upstream_prefix = b'$UserBaseDirectory<>"/Applications/'
    if original.count(upstream_prefix) != 5:
        raise ValueError("CIPro application path declarations differ from the pinned release")
    # The extracted source alone is relocated. No user Wolfram directory is mutated.
    relocated_prefix = APPLICATION_ROOT_SYMBOL.encode("ascii") + b'<>"/'
    source.write_bytes(original.replace(upstream_prefix, relocated_prefix))
    return source
