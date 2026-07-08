"""Unit tests for the SIM2SEIS elapsed-time run logger.

These exercise the user-facing behaviour of
:mod:`fmu.sim2seis.utilities.run_log`: stdout/stderr routing gated by the run
log state, elapsed-time formatting, exception rendering, and the ``log_step``
start/finish messages.

The ``INFO``/``DEBUG`` stdout handler is created at
:func:`start_s2s_run_log` time, so it picks up pytest's ``capsys`` replacement
of ``sys.stdout`` and is asserted through ``capsys``. The ``WARNING``+ stderr
handler is created once at import time, so its stream is redirected onto an
in-memory buffer by the :func:`stderr_buffer` fixture instead.
"""

import io
import logging

import pytest

from fmu.sim2seis.utilities import (
    log_step,
    run_log as _run_log,
    s2s_log,
    s2s_log_once,
    start_s2s_run_log,
    stop_s2s_run_log,
)
from fmu.sim2seis.utilities.run_log import _format_elapsed


@pytest.fixture(autouse=True)
def _clean_run_log_state():
    """Ensure every test starts and ends with the run log deactivated."""
    stop_s2s_run_log()
    yield
    stop_s2s_run_log()


@pytest.fixture
def stderr_buffer(monkeypatch):
    """Redirect the module's stderr handler onto an in-memory buffer."""
    buffer = io.StringIO()
    monkeypatch.setattr(_run_log._stderr_handler, "stream", buffer)
    return buffer


def test_info_is_silent_when_run_log_inactive(capsys):
    s2s_log("hello")
    captured = capsys.readouterr()
    assert captured.out == ""


def test_info_reaches_stdout_only_when_active(capsys, stderr_buffer):
    start_s2s_run_log()
    s2s_log("progress message")
    assert "progress message" in capsys.readouterr().out
    assert stderr_buffer.getvalue() == ""


def test_stdout_routing_stops_after_stop(capsys):
    start_s2s_run_log()
    stop_s2s_run_log()
    s2s_log("should not appear")
    assert capsys.readouterr().out == ""


def test_warning_always_reaches_stderr_when_inactive(capsys, stderr_buffer):
    s2s_log("danger", level=logging.WARNING)
    assert "danger" in stderr_buffer.getvalue()
    assert capsys.readouterr().out == ""


def test_warning_reaches_stderr_when_active(capsys, stderr_buffer):
    start_s2s_run_log()
    s2s_log("danger", level=logging.WARNING)
    assert "danger" in stderr_buffer.getvalue()
    assert "danger" not in capsys.readouterr().out


def test_active_output_has_elapsed_prefix(capsys):
    start_s2s_run_log()
    s2s_log("timed")
    line = capsys.readouterr().out.strip()
    assert line.startswith("SIM2SEIS [")
    assert "min" in line and "sec" in line
    assert line.endswith(": timed")


def test_inactive_warning_has_no_elapsed_prefix(stderr_buffer):
    s2s_log("oops", level=logging.WARNING)
    assert stderr_buffer.getvalue().strip() == "SIM2SEIS WARNING: oops"


def test_exc_info_is_rendered(stderr_buffer):
    try:
        raise ValueError("boom")
    except ValueError:
        logging.getLogger("fmu.sim2seis").error("failed", exc_info=True)
    err = stderr_buffer.getvalue()
    assert "failed" in err
    assert "Traceback" in err
    assert "ValueError: boom" in err


def test_log_once_deduplicates(capsys):
    start_s2s_run_log()
    s2s_log_once("only once")
    s2s_log_once("only once")
    assert capsys.readouterr().out.count("only once") == 1


def test_log_once_resets_after_stop(capsys):
    start_s2s_run_log()
    s2s_log_once("repeatable")
    first = capsys.readouterr().out
    stop_s2s_run_log()
    start_s2s_run_log()
    s2s_log_once("repeatable")
    second = capsys.readouterr().out
    assert "repeatable" in first
    assert "repeatable" in second


def test_log_step_emits_start_and_finish(capsys):
    start_s2s_run_log()
    with log_step("my step"):
        pass
    out = capsys.readouterr().out
    assert "my step: started" in out
    assert "my step: finished in" in out


def test_log_step_finishes_on_exception(capsys):
    start_s2s_run_log()
    with pytest.raises(RuntimeError), log_step("failing step"):
        raise RuntimeError("stop")
    out = capsys.readouterr().out
    assert "failing step: started" in out
    assert "failing step: finished in" in out


def test_format_elapsed():
    assert _format_elapsed(0) == "0 min  0.00 sec"
    assert _format_elapsed(65.5) == "1 min  5.50 sec"
