from itertools import groupby
from typing import Dict, List, Tuple, Type

from cms.models import Page
from cms.utils.i18n import get_language_object
from django.contrib.contenttypes.models import ContentType
from django.utils import translation
from django.utils.timezone import localtime, now

from djangocms_xliff.exceptions import XliffConfigurationError, XliffError
from djangocms_xliff.settings import (
    TEMPLATES_FOLDER_EXPORT,
    UNIT_ID_DELIMITER,
    UNIT_ID_EXTENSION_DATA_ID,
    XLIFF_NAMESPACES,
    XliffVersion,
)
from djangocms_xliff.types import Unit, XliffObj


def get_xliff_version(version: str) -> XliffVersion:
    try:
        return XliffVersion(version)
    except ValueError:
        raise XliffConfigurationError(f'Unsupported xliff version: "{version}"')


def get_xliff_namespaces(version: XliffVersion) -> Dict[str, str]:
    try:
        return XLIFF_NAMESPACES[version]
    except KeyError:
        raise XliffConfigurationError(f"Namespace for xliff version: {version.value} does not exist")


def get_xliff_xml_namespaces(version: XliffVersion) -> Dict[str, str]:
    xml_namespaces = {}
    for name, url in get_xliff_namespaces(version).items():
        xml_namespaces["xmlns" if name == "" else f"xmlns:{name}"] = url
    return xml_namespaces


def get_xliff_export_template_name(version: XliffVersion) -> str:
    return f"{TEMPLATES_FOLDER_EXPORT}/v{version.value}.xliff"


def get_xliff_export_file_name(obj: XliffObj, target_language: str, delimiter="_") -> str:
    path = obj.get_absolute_url()
    parts = [part for part in path.split("/") if part][1:]
    name = "_".join(parts)
    date_str = localtime(now()).strftime("%y%m%d%H%M%S")
    return f"{name}{delimiter}{target_language}{delimiter}{date_str}.xliff"


def get_draft_page_by_id(page_id: int) -> Page:
    try:
        page = Page.objects.get(pk=page_id)
        return get_draft_page(page=page)
    except Page.DoesNotExist:
        raise XliffError(f"Page with id: {page_id} does not exist")


def get_draft_page(page: Page) -> Page:
    if page.publisher_is_draft:
        return page

    raise XliffError(
        "Page is not a draft. You probably want to use a draft instead of a published page. "
        f"Draft page id would be: {page.publisher_public.id}"
    )


def get_obj(content_type_id: int, obj_id: int) -> XliffObj:
    model = ContentType.objects.get_for_id(content_type_id).model_class()
    if not model:
        raise XliffError(f"ContentType Lookup for content_type_id {content_type_id} with obj_id {obj_id} failed")

    if model == Page:
        return get_draft_page_by_id(obj_id)

    try:
        return model.objects.get(id=obj_id)
    except model.DoesNotExist:
        raise XliffError(f"{model._meta.verbose_name} with id: {obj_id} does not exist")


def get_path(obj: XliffObj, language: str) -> str:
    if type(obj) == Page:
        return obj.get_path(language)

    with translation.override(language):
        return obj.get_absolute_url()


def group_units_by_plugin_id(units: List[Unit]) -> List[Tuple[str, List[Unit]]]:
    return [(plugin_id, list(units)) for plugin_id, units in groupby(units, lambda u: u.plugin_id)]


def get_type_with_path(cls: Type) -> str:
    typ = type(cls)
    return f"{typ.__module__}.{typ.__name__}"


def get_lang_name(search_code: str) -> str:
    return get_language_object(search_code)["name"]


def get_metadata_fields_for_model(obj: XliffObj) -> Dict[str, str]:
    from djangocms_xliff.settings import MODEL_METADATA_FIELDS

    obj_type = type(obj)
    try:
        return MODEL_METADATA_FIELDS[obj_type]
    except KeyError:
        raise XliffError(f"Can't find model {obj_type} in MODEL_METADATA_FIELDS config")


def get_plugin_id_for_extension_obj(obj) -> str:
    content_type_id = ContentType.objects.get_for_model(obj).id
    return UNIT_ID_DELIMITER.join([UNIT_ID_EXTENSION_DATA_ID, str(content_type_id), str(obj.id)])
