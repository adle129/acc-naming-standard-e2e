"""FR-13 name for the Upload files page. New tests use UploadFilesPage."""

from pages.upload_files_page import UPLOAD_FILES_HEADING, UploadFilesPage

# Kept so existing imports from this module still resolve.
UploadValidator = UploadFilesPage

__all__ = ["UPLOAD_FILES_HEADING", "UploadFilesPage", "UploadValidator"]
