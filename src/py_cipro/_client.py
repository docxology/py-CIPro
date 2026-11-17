"""A persistent Wolfram kernel session for the upstream CIPro package."""

import os
from concurrent.futures import TimeoutError as FutureTimeoutError
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import RLock
from typing import Any

from wolframclient.evaluation import WolframLanguageSession
from wolframclient.exception import WolframKernelException
from wolframclient.language import wl
from wolframclient.language.expression import WLSymbol

from ._catalog import FUNCTIONS, MODIFICATIONS, PROPERTIES
from ._release import APPLICATION_ROOT_SYMBOL, prepare_application


@dataclass(frozen=True)
class Evaluation:
    """The kernel value, diagnostics and exact serialized Wolfram expression."""

    value: Any
    success: bool
    messages: tuple[str, ...]
    output: tuple[str, ...]
    wxf: bytes
    failure: str | None


class CIProError(RuntimeError):
    """Base class for CIPro wrapper errors."""


class KernelUnavailable(CIProError):
    """A Wolfram kernel could not start or respond."""


class EvaluationError(CIProError):
    """A Wolfram evaluation returned a failure status or emitted messages."""

    def __init__(self, detail: Evaluation):
        self.detail = detail
        message = "\n".join(detail.messages) or detail.failure or str(detail.value)
        super().__init__(f"Wolfram evaluation failed: {message}")


def _symbol(name: str):
    return getattr(wl, name)


def _read_evaluation(response) -> Evaluation:
    value = response.result
    failed = isinstance(value, WLSymbol) and value.name in {
        "$Failed", "System`$Failed", "$Aborted", "System`$Aborted",
    }
    return Evaluation(
        value=value,
        success=bool(response.success) and not failed,
        messages=tuple(response.messages or ()),
        output=tuple(response.output or ()),
        wxf=response.wxf,
        failure=response.failure,
    )


class CIPro:
    """Run the released CIPro code in an activated local Wolfram kernel.

    Reuse a client for related calls to preserve CIPro's kernel caches and options.
    Closing a client removes its temporary package and session-local datasets.
    """

    functions = tuple(sorted(FUNCTIONS))
    properties = PROPERTIES
    modifications = MODIFICATIONS

    def __init__(
        self,
        kernel: str | os.PathLike[str] | None = None,
        *,
        startup_timeout: float = 180,
        evaluation_timeout: float | None = 600,
    ):
        kernel = kernel or os.environ.get("WOLFRAM_KERNEL")
        self._kernel = os.fspath(kernel) if kernel is not None else None
        self._startup_timeout = startup_timeout
        self._evaluation_timeout = evaluation_timeout
        self._lock = RLock()
        self._session = None
        self._workspace = None
        self.startup: Evaluation | None = None

    def __enter__(self):
        return self.start()

    def __exit__(self, *_):
        self.close()

    def start(self):
        """Start the kernel and verify the released property and modification registries."""
        with self._lock:
            if self._session is not None:
                return self
            session = None
            self.startup = None
            try:
                session = WolframLanguageSession(
                    kernel=self._kernel,
                    inputform_string_evaluation=False,
                    wxf_bytes_evaluation=False,
                    STARTUP_TIMEOUT=self._startup_timeout,
                )
                session.start(timeout=self._startup_timeout)
            except (OSError, FutureTimeoutError, WolframKernelException) as exc:
                if session is not None:
                    session.terminate()
                raise KernelUnavailable(
                    "An activated Wolfram kernel is required. Set WOLFRAM_KERNEL to "
                    "the WolframKernel executable or pass kernel= explicitly."
                ) from exc

            self._session = session
            try:
                self._workspace = TemporaryDirectory(prefix="py-cipro-")
                root = Path(self._workspace.name).resolve()
                source = prepare_application(root)
                verify = wl.And(
                    wl.AssociationQ(_symbol("CIPro`DataInfo")),
                    wl.SameQ(
                        wl.Sort(wl.Keys(_symbol("CIPro`Private`CIProMod"))),
                        wl.Sort(PROPERTIES),
                    ),
                    wl.SameQ(
                        wl.Sort(wl.Keys(_symbol("CIPro`Private`CIModMod"))),
                        wl.Sort(MODIFICATIONS),
                    ),
                    *(
                        wl.Greater(wl.Length(wl.DownValues(_symbol(f"CIPro`{name}"))), 0)
                        for name in self.functions
                    ),
                )
                expression = wl.CompoundExpression(
                    wl.Set(_symbol(APPLICATION_ROOT_SYMBOL), str(root)),
                    wl.Get(str(source)),
                    verify,
                )
                response = session.evaluate_wrap_future(expression).result(
                    timeout=self._startup_timeout,
                )
                self.startup = _read_evaluation(response)
                if self.startup.value is not True:
                    raise EvaluationError(self.startup)
            except FutureTimeoutError as exc:
                self.close()
                raise KernelUnavailable("Loading the CIPro package exceeded startup_timeout.") from exc
            except BaseException:
                self.close()
                raise
            return self

    def close(self):
        """Terminate the owned kernel before removing its extracted application."""
        with self._lock:
            try:
                if self._session is not None:
                    self._session.terminate()
            finally:
                self._session = None
                if self._workspace is not None:
                    self._workspace.cleanup()
                    self._workspace = None

    def evaluate_result(self, expression) -> Evaluation:
        """Evaluate a Wolfram expression, retaining messages and print output."""
        with self._lock:
            self.start()
            try:
                response = self._session.evaluate_wrap_future(expression).result(
                    timeout=self._evaluation_timeout,
                )
                return _read_evaluation(response)
            except FutureTimeoutError as exc:
                self.close()
                raise KernelUnavailable(
                    "CIPro evaluation exceeded evaluation_timeout and its kernel was closed."
                ) from exc
            except WolframKernelException as exc:
                self.close()
                raise KernelUnavailable("The Wolfram kernel stopped responding.") from exc

    def evaluate(self, expression):
        """Evaluate an expression and raise on a Wolfram failure or message."""
        return _checked(self.evaluate_result(expression))

    def call_result(self, name: str, /, *args, **options) -> Evaluation:
        """Invoke an upstream CIPro head and return its value and diagnostics."""
        if name not in FUNCTIONS:
            raise ValueError(f"Unknown callable CIPro symbol {name!r}")
        rules = (wl.Rule(key, value) for key, value in options.items())
        return self.evaluate_result(_symbol(f"CIPro`{name}")(*args, *rules))

    def call(self, name: str, /, *args, **options):
        """Invoke an upstream CIPro head, returning the kernel value."""
        return _checked(self.call_result(name, *args, **options))

    def property(self, geometry, keys, /, **options):
        """Call upstream CIProp with one key or a list of keys."""
        return self.call("CIProp", geometry, keys, **options)

    def modify(self, geometry, key, /, **options):
        """Call upstream CIMod with one modification key."""
        return self.call("CIMod", geometry, key, **options)

    def __getattr__(self, name):
        if name in FUNCTIONS:
            return partial(self.call, name)
        raise AttributeError(name)

    def __dir__(self):
        return sorted(set(super().__dir__()) | set(FUNCTIONS))


def _checked(detail: Evaluation):
    if not detail.success:
        raise EvaluationError(detail)
    return detail.value
