from django.contrib.contenttypes.models import ContentType

from djangocms_xliff.extractors import extract_units_from_obj
from djangocms_xliff.renderer import render_xliff_document
from djangocms_xliff.types import ExportPage, XliffContext, XliffObj
from djangocms_xliff.utils import (
    get_path,
    get_xliff_export_file_name,
    get_xliff_version,
)


def convert_obj_to_xliff_context(obj: XliffObj, source_language: str, target_language: str) -> XliffContext:
    content_type_id = ContentType.objects.get_for_model(obj).pk
    return XliffContext(
        source_language=source_language,
        target_language=target_language,
        content_type_id=content_type_id,
        obj_id=obj.id,
        path=get_path(obj=obj, language=target_language),
        units=extract_units_from_obj(obj, target_language),
    )


def export_content_as_xliff(
    obj: XliffObj,
    source_language: str,
    target_language: str,
    version: str = "1.2",
) -> ExportPage:
    xliff_version = get_xliff_version(version)
    context = convert_obj_to_xliff_context(obj, source_language, target_language)
    content = render_xliff_document(xliff_version, context)
    file_name = get_xliff_export_file_name(obj=obj, target_language=target_language)
    return content, file_name
