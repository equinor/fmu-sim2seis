"""Elapsed-time run logging for fmu-sim2seis.

This module mirrors the logging design that has proven useful in ``fmu-pem``
(see :mod:`fmu.pem.pem_utilities.utils`): a dedicated logger that prefixes
every record with the package name and the wall-clock time elapsed since the
run started, so the user gets both progress information and a sense of the time
consumed by each step.

The ``fmu-pem`` implementation bakes the ``PEM`` label into a private
``logging.Formatter`` that reads a module-global start time, so it cannot be
re-labelled for ``sim2seis`` by a wrapper without reaching into pem internals.
Rather than duplicate that coupling, this module re-implements the same small,
generic machinery with a ``SIM2SEIS`` label and adds :func:`log_step`, a
context manager / decorator that times an individual step and reports its
duration.

Message routing follows pem's model:

* ``INFO`` / ``DEBUG`` records reach stdout only while a run log is active
  (i.e. between :func:`start_s2s_run_log` and :func:`stop_s2s_run_log`).
* ``WARNING`` and above always reach stderr, independent of the run log.
"""

import logging
import sys
import time
from collections.abc import Generator
from contextlib import contextmanager

_LABEL = "SIM2SEIS"


class _RunState:
    """Mutable holder for the active run log state.

    Kept as a single instance so the module functions can update the elapsed
    origin and the stdout handler without rebinding module globals.
    """

    start_time: float | None = None
    stdout_handler: logging.Handler | None = None


_state = _RunState()


def _format_elapsed(seconds: float) -> str:
    minutes, secs = divmod(seconds, 60)
    return f"{int(minutes)} min {secs:5.2f} sec"


class _ElapsedFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        level = "" if record.levelno == logging.INFO else f" {record.levelname}"
        if _state.start_time is None:
            return f"{_LABEL}{level}: {record.getMessage()}"
        elapsed = time.monotonic() - _state.start_time
        return f"{_LABEL} [{_format_elapsed(elapsed)}]{level}: {record.getMessage()}"


_S2S_FORMATTER = _ElapsedFormatter()

sim2seis_logger = logging.getLogger("fmu.sim2seis")
sim2seis_logger.setLevel(logging.WARNING)
sim2seis_logger.propagate = False

_stderr_handler = logging.StreamHandler(sys.stderr)
_stderr_handler.setFormatter(_S2S_FORMATTER)
_stderr_handler.setLevel(logging.WARNING)
sim2seis_logger.addHandler(_stderr_handler)

_logged_once: set[str] = set()


def start_s2s_run_log(level: int = logging.INFO) -> None:
    """Activate verbose sim2seis run logging.

    Anchors the elapsed-time origin and attaches a stdout handler for records
    below ``WARNING``. ``WARNING`` and above always reach stderr, independent of
    this call. Repeated calls are no-ops; call :func:`stop_s2s_run_log` first to
    re-anchor.
    """
    if _state.start_time is not None:
        return
    _state.start_time = time.monotonic()

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(_S2S_FORMATTER)
    stdout_handler.addFilter(lambda r: r.levelno < logging.WARNING)
    _state.stdout_handler = stdout_handler

    sim2seis_logger.setLevel(min(level, logging.WARNING))
    sim2seis_logger.addHandler(stdout_handler)


def stop_s2s_run_log() -> None:
    """Deactivate verbose sim2seis run logging.

    Detaches the stdout handler and resets the elapsed-time origin. The stderr
    handler for ``WARNING`` and above remains attached. No-op when
    :func:`start_s2s_run_log` was never called, so an embedding application's
    logger configuration is preserved.
    """
    if _state.start_time is None:
        return
    if _state.stdout_handler is not None:
        sim2seis_logger.removeHandler(_state.stdout_handler)
        _state.stdout_handler = None
    sim2seis_logger.setLevel(logging.WARNING)
    _state.start_time = None
    _logged_once.clear()


def s2s_log(message: str, level: int = logging.INFO) -> None:
    """Emit ``message`` on the sim2seis logger at ``level`` (default ``INFO``).

    ``INFO`` / ``DEBUG`` go to stdout only while :func:`start_s2s_run_log` is
    active. ``WARNING`` / ``ERROR`` / ``CRITICAL`` always go to stderr.
    """
    sim2seis_logger.log(level, message)


def s2s_log_once(message: str, level: int = logging.INFO) -> None:
    """Emit ``message`` at most once per run (deduplicated by message text).

    The seen-set is cleared by :func:`stop_s2s_run_log`, so a fresh run starts
    with an empty history.
    """
    if message in _logged_once:
        return
    _logged_once.add(message)
    sim2seis_logger.log(level, message)


@contextmanager
def log_step(step_name: str, level: int = logging.INFO) -> Generator[None, None, None]:
    """Time an individual step and log its start and duration.

    Usable both as a context manager::

        with log_step("seismic forward modelling"):
            ...

    and as a decorator (via :class:`contextlib.contextmanager`'s
    ``ContextDecorator`` behaviour)::

        @log_step("seismic forward modelling")
        def run(...):
            ...

    The messages are routed through :func:`s2s_log`, so they are only shown when
    a run log is active. The timer itself always runs; only the output is gated.
    """
    start = time.monotonic()
    s2s_log(f"{step_name}: started", level)
    try:
        yield
    finally:
        elapsed = time.monotonic() - start
        s2s_log(f"{step_name}: finished in {_format_elapsed(elapsed)}", level)
