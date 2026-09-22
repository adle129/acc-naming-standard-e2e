"""FR-11: step-level logging can diagnose a failure without a rerun."""

from __future__ import annotations

from pathlib import Path

import pytest

from utils.logger import (
    configure_logging,
    reset_logging,
    set_screenshot_path,
    set_test_name,
    step,
    step_scope,
)

pytestmark = pytest.mark.framework

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def _isolated_logger(tmp_path: Path) -> Path:
    reset_logging()
    log_path = configure_logging(log_dir=tmp_path)
    set_test_name("test_upload_delete_restore")
    yield log_path
    reset_logging()


def _read(log_path: Path) -> str:
    return log_path.read_text(encoding="utf-8")


def test_successful_step_writes_pipe_line(_isolated_logger: Path) -> None:
    @step("fill Project = {value}")
    def fill_project(value: str) -> str:
        return value

    assert fill_project("hw472") == "hw472"
    text = _read(_isolated_logger)
    assert "INFO" in text
    assert "test_upload_delete_restore" in text
    assert "STEP 1" in text
    assert "fill Project = hw472" in text
    assert "OK" in text
    assert "ms" in text


def test_failed_step_is_diagnosable_from_the_log(_isolated_logger: Path) -> None:
    set_screenshot_path("reports/screenshots/test_upload_delete_restore.png")

    @step("expect banner hidden")
    def expect_banner_hidden() -> None:
        raise AssertionError("banner still visible")

    with pytest.raises(AssertionError, match="banner still visible"):
        expect_banner_hidden()

    text = _read(_isolated_logger)
    assert "ERROR" in text
    assert "STEP 1" in text
    assert "expect banner hidden" in text
    assert "FAIL" in text
    assert "AssertionError: banner still visible" in text
    assert "screenshot: reports/screenshots/test_upload_delete_restore.png" in text


def test_step_redacts_password_arguments(_isolated_logger: Path) -> None:
    @step("login as {username} password={password}")
    def login(username: str, password: str) -> None:
        return None

    login("reviewer@example.com", "super-secret")
    text = _read(_isolated_logger)
    assert "reviewer@example.com" in text
    assert "super-secret" not in text
    assert "password=***" in text


def test_step_scope_logs_ok_and_fail(_isolated_logger: Path) -> None:
    with step_scope("open files page"):
        pass
    with pytest.raises(RuntimeError, match="boom"):
        with step_scope("click Upload"):
            raise RuntimeError("boom")

    text = _read(_isolated_logger)
    assert "open files page" in text
    assert "click Upload" in text
    assert "RuntimeError: boom" in text


def test_file_handler_keeps_debug_start_lines(_isolated_logger: Path) -> None:
    @step("pick Type = {value}")
    def pick_type(value: str) -> None:
        return None

    pick_type("CA")
    text = _read(_isolated_logger)
    assert "DEBUG" in text
    assert "START" in text
    assert "pick Type = CA" in text


def test_logger_module_has_no_sleeps() -> None:
    source = (ROOT / "utils" / "logger.py").read_text(encoding="utf-8")
    assert "time.sleep" not in source
    assert "wait_for_timeout" not in source
