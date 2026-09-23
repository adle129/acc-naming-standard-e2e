"""Step-level logging and the @step decorator (FR-11)."""

from __future__ import annotations

import functools
import inspect
import logging
import os
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from typing import Any, TypeVar

REPO_ROOT = Path(__file__).resolve().parents[1]
LOGGER_NAME = "acc_e2e"
LOG_DIR_NAME = "logs"
LOG_FILE_PREFIX = "run_"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
LOG_FILE_STAMP_FORMAT = "%Y%m%d_%H%M%S_%f"
DURATION_SUFFIX = "ms"
STEP_ID_PREFIX = "STEP"
STEP_RESULT_OK = "OK"
STEP_RESULT_FAIL = "FAIL"
STEP_RESULT_START = "START"
SECRET_MASK = "***"
SCREENSHOT_PREFIX = "screenshot: "
MISSING_FIELD = "-"
PHASE_COLUMN = "RUN"
PHASE_TEST_START = "TEST START {name}"
PHASE_TEST_END = "TEST END {name}"
PHASE_TEST_NAME = "TEST NAME {name}"
PHASE_CONFIG = "config: {details}"
PHASE_PYTEST = "pytest: headed={headed} slowmo={slowmo} reruns={reruns}"
PHASE_CASE = "TEST CASE {suite}/{row_id} - {description}"
NODE_PARAM_OPEN = "["
PHASE_SESSION_AUTH_REUSE = "session auth: reuse {file}"
PHASE_SESSION_AUTH_LOGIN = "session auth: login then write {file}"
PHASE_PREPARE = "prepare: open Files, open folder, sweep leftover generated uploads"
PHASE_CLEANUP = "cleanup: delete leftover Files-list rows"
PHASE_CLEANUP_NAMES = "cleanup names: {names}"
PHASE_CLEANUP_NONE = "none"
CASE_STEP_COLUMN = "CASE"
CASE_STEP = "Step {number} - {action}"
PYTEST_CURRENT_TEST_ENV = "PYTEST_CURRENT_TEST"
SECRET_PARAM_NAMES = frozenset(
    {
        "password",
        "password_token",
        "token",
        "key",
        "fernet_key",
        "acc_password",
        "acc_fernet_key",
    }
)

_test_name: ContextVar[str] = ContextVar("acc_e2e_test_name", default="")
_step_index: ContextVar[int] = ContextVar("acc_e2e_step_index", default=0)
_screenshot_path: ContextVar[str] = ContextVar("acc_e2e_screenshot", default="")
_configured = False

F = TypeVar("F", bound=Callable[..., Any])


class StepFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        step = getattr(record, "step", MISSING_FIELD)
        action = getattr(record, "action", record.getMessage())
        result = getattr(record, "step_result", MISSING_FIELD)
        duration = getattr(record, "duration_ms", MISSING_FIELD)
        extra = getattr(record, "step_extra", "")
        line = (
            f"{timestamp} | {record.levelname:<5} | {current_test_name()} | "
            f"{step} | {action} | {result} | {duration}"
        )
        if extra:
            line = f"{line} | {extra}"
        return line


def short_test_name() -> str:
    """Return the pytest function name without a browser parameter suffix.

    Returns:
        For example test_upload_delete_restore, not test_upload_delete_restore[chromium].
    """
    name = current_test_name()
    # Playwright parametrization appends [chromium]; the case name stops before that.
    bracket = name.find(NODE_PARAM_OPEN)
    if bracket == -1:
        return name
    return name[:bracket]


def current_test_name() -> str:
    name = _test_name.get()
    if name:
        return name
    raw = os.environ.get(PYTEST_CURRENT_TEST_ENV, "")
    if raw:
        node = raw.split(" ", 1)[0]
        return node.rsplit("::", 1)[-1]
    return "-"


def set_test_name(name: str) -> None:
    _test_name.set(name)
    _step_index.set(0)


def set_screenshot_path(path: str | Path | None) -> None:
    _screenshot_path.set("" if path is None else str(path))


def get_logger() -> logging.Logger:
    return logging.getLogger(LOGGER_NAME)


def configure_logging(
    *,
    log_dir: Path | None = None,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
) -> Path:
    """Create one log file per run: logs/run_<timestamp>.log."""
    global _configured
    directory = REPO_ROOT / LOG_DIR_NAME if log_dir is None else Path(log_dir)
    directory.mkdir(parents=True, exist_ok=True)
    log_path = directory / f"{LOG_FILE_PREFIX}{datetime.now().strftime(LOG_FILE_STAMP_FORMAT)}.log"

    logger = get_logger()
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    formatter = StepFormatter()
    console = logging.StreamHandler()
    console.setLevel(console_level)
    console.setFormatter(formatter)
    logger.addHandler(console)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    _configured = True
    return log_path


def log_phase(action: str, *, result: str = MISSING_FIELD) -> None:
    """Write a lifecycle line that does not consume a STEP number.

    Args:
        action: What happened, for example TEST START or a config summary.
        result: START / OK / FAIL, or "-" when the line is informational.
    """
    _ensure_configured()
    # RUN stays in the step column so a reviewer can filter setup from UI steps.
    get_logger().info("", extra=_extra(PHASE_COLUMN, action, result, MISSING_FIELD))


def log_case_step(number: int, action: str) -> None:
    """Write a sample-case step line before the matching test code.

    Args:
        number: Sample-case step number, for example 3.
        action: What this block does. No URL or secret.
    """
    _ensure_configured()
    # CASE is not STEP n, so POM clicks and business steps stay distinct.
    text = CASE_STEP.format(number=number, action=action)
    get_logger().info("", extra=_extra(CASE_STEP_COLUMN, text, MISSING_FIELD, MISSING_FIELD))


def log_case(*, suite: str, row_id: str, description: str, attributes: str) -> None:
    """Write which JSON case this test loaded.

    Args:
        suite: Suite file stem, for example acceptance.
        row_id: Row id inside that file.
        description: Case description from the JSON row.
        attributes: One-line field summary with no secrets.
    """
    # Description stays in the action column; field values go in the extra column.
    action = PHASE_CASE.format(suite=suite, row_id=row_id, description=description)
    _ensure_configured()
    get_logger().info("", extra=_extra(PHASE_COLUMN, action, MISSING_FIELD, MISSING_FIELD, attributes))


@contextmanager
def phase_scope(action: str) -> Iterator[None]:
    """Time a prepare or cleanup block and write START then OK or FAIL.

    Args:
        action: Lifecycle label, for example PHASE_PREPARE.
    """
    _ensure_configured()
    started = time.perf_counter()
    # INFO so the console shows prepare/cleanup starting, not only the file.
    get_logger().info("", extra=_extra(PHASE_COLUMN, action, STEP_RESULT_START, MISSING_FIELD))
    try:
        yield
    except Exception as exc:
        _emit_phase(action, STEP_RESULT_FAIL, started, error=exc)
        raise
    _emit_phase(action, STEP_RESULT_OK, started)


def _emit_phase(
    action: str,
    result: str,
    started: float,
    *,
    error: BaseException | None = None,
) -> None:
    """Write the closing RUN line for a timed prepare or cleanup block.

    Args:
        action: Same label as the matching START line.
        result: OK or FAIL.
        started: perf_counter value from the start of the block.
        error: Exception to append when the block failed.
    """
    duration_ms = f"{int((time.perf_counter() - started) * 1000)}{DURATION_SUFFIX}"
    extras: list[str] = []
    if error is not None:
        extras.append(f"{type(error).__name__}: {error}")
    level = logging.ERROR if result == STEP_RESULT_FAIL else logging.INFO
    get_logger().log(
        level,
        "",
        extra=_extra(PHASE_COLUMN, action, result, duration_ms, " | ".join(extras)),
    )


def reset_logging() -> None:
    global _configured
    logger = get_logger()
    for handler in logger.handlers:
        handler.close()
    logger.handlers.clear()
    _configured = False
    set_test_name("")
    set_screenshot_path(None)


def step(description: str) -> Callable[[F], F]:
    """Wrap a page-object action and emit one step line."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            action = _render_action(description, func, args, kwargs)
            return _run_step(action, func, args, kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


@contextmanager
def step_scope(description: str) -> Iterator[None]:
    """Context-manager form of @step for ad-hoc blocks."""
    _ensure_configured()
    started = time.perf_counter()
    step_id = _next_step_id()
    get_logger().debug("", extra=_extra(step_id, description, STEP_RESULT_START, MISSING_FIELD))
    try:
        yield
    except Exception as exc:
        _emit_step(step_id, description, STEP_RESULT_FAIL, started, error=exc)
        raise
    _emit_step(step_id, description, STEP_RESULT_OK, started)


def _ensure_configured() -> None:
    if not _configured:
        configure_logging()


def _run_step(action: str, func: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
    _ensure_configured()
    started = time.perf_counter()
    step_id = _next_step_id()
    get_logger().debug("", extra=_extra(step_id, action, STEP_RESULT_START, MISSING_FIELD))
    try:
        result = func(*args, **kwargs)
    except Exception as exc:
        _emit_step(step_id, action, STEP_RESULT_FAIL, started, error=exc)
        raise
    _emit_step(step_id, action, STEP_RESULT_OK, started)
    return result


def _emit_step(
    step_id: str,
    action: str,
    result: str,
    started: float,
    *,
    error: BaseException | None = None,
) -> None:
    duration_ms = f"{int((time.perf_counter() - started) * 1000)}{DURATION_SUFFIX}"
    extras: list[str] = []
    if error is not None:
        extras.append(f"{type(error).__name__}: {error}")
    screenshot = _screenshot_path.get()
    if result == STEP_RESULT_FAIL and screenshot:
        extras.append(f"{SCREENSHOT_PREFIX}{screenshot}")
    level = logging.ERROR if result == STEP_RESULT_FAIL else logging.INFO
    get_logger().log(
        level,
        "",
        extra=_extra(step_id, action, result, duration_ms, " | ".join(extras)),
    )


def _extra(
    step_id: str,
    action: str,
    result: str,
    duration_ms: str,
    extra: str = "",
) -> dict[str, str]:
    return {
        "step": step_id,
        "action": action,
        "step_result": result,
        "duration_ms": duration_ms,
        "step_extra": extra,
    }


def _next_step_id() -> str:
    index = _step_index.get() + 1
    _step_index.set(index)
    return f"{STEP_ID_PREFIX} {index}"


def _render_action(description: str, func: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    try:
        bound = inspect.signature(func).bind_partial(*args, **kwargs)
        bound.apply_defaults()
    except TypeError:
        return description
    values = {}
    for name, value in bound.arguments.items():
        if name == "self":
            continue
        if name.lower() in SECRET_PARAM_NAMES:
            values[name] = SECRET_MASK
        else:
            values[name] = value
    try:
        return description.format(**values)
    except (KeyError, IndexError, ValueError):
        return description
