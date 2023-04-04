from itertools import groupby
from typing import List, Tuple, Type

from cms.models import Page
from cms.utils.i18n import get_language_object
from django.utils.timezone import localtime, now

from djangocms_xliff.exceptions import XliffConfigurationError, XliffError
from djangocms_xliff.settings import (
    TEMPLATES_FOLDER_EXPORT,
    XLIFF_NAMESPACES,
    XliffVersion,
)
from djangocms_xliff.types import Unit


def get_xliff_version(version: str) -> XliffVersion:
    try:
        return XliffVersion(version)
    except ValueError:
        raise XliffConfigurationError(f'Unsupported xliff version: "{version}"')


def get_xliff_namespaces(version: XliffVersion) -> dict:
    try:
        return XLIFF_NAMESPACES[version]
    except KeyError:
        raise XliffConfigurationError(f"Namespace for xliff version: {version.value} does not exist")


def get_xliff_xml_namespaces(version: XliffVersion) -> dict:
    xml_namespaces = {}
    for name, url in get_xliff_namespaces(version).items():
        xml_namespaces["xmlns" if name == "" else f"xmlns:{name}"] = url
    return xml_namespaces


def get_xliff_export_template_name(version: XliffVersion) -> str:
    return f"{TEMPLATES_FOLDER_EXPORT}/v{version.value}.xliff"


def get_xliff_export_file_name(page: Page, target_language: str, delimiter="_") -> str:
    path = page.get_absolute_url()
    parts = [part for part in path.split("/") if part][1:]
    name = "_".join(parts)
    date_str = localtime(now()).strftime("%y%m%d%H%M%S")
    return f"{name}{delimiter}{target_language}{delimiter}{date_str}.xliff"


def get_draft_page(page_id: int) -> Page:
    try:
        page = Page.objects.get(id=page_id)
        if not page.publisher_is_draft:
            raise XliffError(
                "Page is not a draft. You probably want to use a draft instead of a published page. "
                f"Draft page id would be: {page.publisher_public.pk}"
            )
        return page
    except Page.DoesNotExist:
        raise XliffError(f"Page with id: {page_id} does not exist")


def group_units_by_plugin_id(units: List[Unit]) -> List[Tuple[str, List[Unit]]]:
    return [(plugin_id, list(units)) for plugin_id, units in groupby(units, lambda u: u.plugin_id)]


def get_type_with_path(cls: Type) -> str:
    typ = type(cls)
    return f"{typ.__module__}.{typ.__name__}"


def get_lang_name(search_code: str) -> str:
    return get_language_object(search_code)["name"]
