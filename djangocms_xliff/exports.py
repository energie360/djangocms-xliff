from cms.models import Page

from djangocms_xliff.extractors import extract_units_from_page
from djangocms_xliff.renderer import render_xliff_document
from djangocms_xliff.types import ExportPage, XliffContext
from djangocms_xliff.utils import (
    get_draft_page,
    get_xliff_export_file_name,
    get_xliff_version,
)


def convert_page_to_xliff_context(page: Page, source_language: str, target_language: str) -> XliffContext:
    return XliffContext(
        source_language=source_language,
        target_language=target_language,
        page_id=page.pk,
        page_path=page.get_path(target_language),
        units=extract_units_from_page(page, target_language),
    )


def export_page_as_xliff(
    page_id: int,
    source_language: str,
    target_language: str,
    version: str = "1.2",
) -> ExportPage:
    xliff_version = get_xliff_version(version)
    page = get_draft_page(page_id)
    context = convert_page_to_xliff_context(page, source_language, target_language)
    content = render_xliff_document(xliff_version, context)
    file_name = get_xliff_export_file_name(page=page, target_language=target_language)
    return content, file_name
