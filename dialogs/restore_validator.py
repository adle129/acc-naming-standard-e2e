"""FR-13 name for the Restore files page. New tests use RestoreFilesPage."""

from pages.restore_files_page import RESTORE_FILES_HEADING, RestoreFilesPage

# Kept so existing imports from this module still resolve.
RestoreValidator = RestoreFilesPage

__all__ = ["RESTORE_FILES_HEADING", "RestoreFilesPage", "RestoreValidator"]
