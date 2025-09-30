from itertools import groupby
from typing import Any

from cms.models import PageContent
from cms.utils.i18n import get_language_object
from django.contrib.contenttypes.models import ContentType
from django.utils import translation
from django.utils.timezone import localtime, now
from djangocms_alias.models import AliasContent

from djangocms_xliff.exceptions import XliffConfigurationError, XliffError
from djangocms_xliff.settings import (
    TEMPLATES_FOLDER_EXPORT,
    UNIT_ID_DELIMITER,
    UNIT_ID_EXTENSION_DATA_ID,
    UNIT_ID_METADATA_ID,
    XLIFF_NAMESPACES,
    XliffVersion,
    get_model_for_alias_content,
)
from djangocms_xliff.types import Unit, XliffObj

type CMSContentType = PageContent | AliasContent


def get_xliff_version(version: str) -> XliffVersion:
    try:
        return XliffVersion(version)
    except ValueError as e:
        raise XliffConfigurationError(f'Unsupported xliff version: "{version}"') from e


def get_xliff_namespaces(version: XliffVersion) -> dict[str, str]:
    try:
        return XLIFF_NAMESPACES[version]
    except KeyError as e:
        raise XliffConfigurationError(f"Namespace for xliff version: {version.value} does not exist") from e


def get_xliff_xml_namespaces(version: XliffVersion) -> dict[str, str]:
    xml_namespaces = {}
    for name, url in get_xliff_namespaces(version).items():
        xml_namespaces["xmlns" if name == "" else f"xmlns:{name}"] = url
    return xml_namespaces


def get_xliff_export_template_name(version: XliffVersion) -> str:
    return f"{TEMPLATES_FOLDER_EXPORT}/v{version.value}.xliff"


def get_xliff_export_file_name(obj: XliffObj, target_language: str, delimiter="_") -> str:
    path = get_path(obj=obj, language=target_language)
    parts = [part for part in path.split("/") if part][1:]
    name = "_".join(parts)
    date_str = localtime(now()).strftime("%y%m%d%H%M%S")
    return f"{name}{delimiter}{target_language}{delimiter}{date_str}.xliff"


def get_versioning_obj_by_id(model: CMSContentType, obj_id: int) -> PageContent:
    try:
        return model.admin_manager.get(id=obj_id)
    except PageContent.DoesNotExist as e:
        raise XliffError(f"{model} with id: {obj_id} does not exist") from e


def get_obj(content_type_id: int, obj_id: Any) -> XliffObj:
    model = ContentType.objects.get_for_id(content_type_id).model_class()
    if not model:
        raise XliffError(f"ContentType Lookup for content_type_id {content_type_id} with obj_id {obj_id} failed")

    if model in [PageContent, AliasContent]:
        return get_versioning_obj_by_id(model=model, obj_id=obj_id)  # type: ignore

    try:
        return model.objects.get(pk=obj_id)
    except model.DoesNotExist as e:
        raise XliffError(f"{model._meta.verbose_name} with id: {obj_id} does not exist") from e


def get_latest_obj_by_version[T: CMSContentType](obj: T, language: str) -> T:
    model = obj.__class__
    try:
        filter_kwargs: dict = {"language": language}

        if type(obj) is PageContent:
            filter_kwargs["page"] = obj.page
        elif type(obj) is AliasContent:
            filter_kwargs["alias"] = obj.alias
        else:
            raise XliffError(f"get_latest_obj_by_version does not support model: {model}")

        return model.admin_manager.latest_content(**filter_kwargs).get()
    except model.DoesNotExist as e:
        raise XliffError(f"Did not find latest version for {type(obj)}: {obj.pk}") from e


def must_get_model_for_alias_content(obj: AliasContent) -> XliffObj:
    if get_model_for_alias_content is None:
        raise XliffConfigurationError(
            "You have xliff content for alias content, but no get_model_for_alias_content() handler is configured"
        )

    try:
        model = get_model_for_alias_content(obj.alias)
        if model is None:
            raise XliffError(f"Did not find model for alias content with id: {obj.pk}")
        return model
    except AttributeError as e:
        raise XliffConfigurationError(f"Model {type(obj)} is used as AliasContent but has no alias relation") from e


def get_path(obj: XliffObj, language: str) -> str:
    if type(obj) is AliasContent:
        model = must_get_model_for_alias_content(obj)
        return model.get_absolute_url(language) or ""  # type: ignore

    with translation.override(language):
        return obj.get_absolute_url() or ""  # type: ignore


def group_units_by_plugin_id(units: list[Unit]) -> list[tuple[str, list[Unit]]]:
    return [(plugin_id, list(units)) for plugin_id, units in groupby(units, lambda u: u.plugin_id)]


def map_units_by_plugin_id(units: list[Unit]) -> dict[str, list[Unit]]:
    return {plugin_id: list(units) for plugin_id, units in groupby(units, lambda u: u.plugin_id)}


def get_type_with_path(cls: type) -> str:
    typ = type(cls)
    return f"{typ.__module__}.{typ.__name__}"


def get_lang_name(search_code: str) -> str:
    return get_language_object(search_code)["name"]


def get_metadata_fields_for_model(obj: XliffObj) -> dict[str, str]:
    from djangocms_xliff.settings import MODEL_METADATA_FIELDS

    obj_type = type(obj)
    try:
        return MODEL_METADATA_FIELDS[obj_type]
    except KeyError as e:
        raise XliffError(f"Can't find model {obj_type} in MODEL_METADATA_FIELDS config") from e


def get_plugin_id_for_extension_obj(obj) -> str:
    content_type_id = ContentType.objects.get_for_model(obj).pk
    return get_unit_id_format(UNIT_ID_EXTENSION_DATA_ID, str(content_type_id), str(obj.pk))


def get_plugin_id_for_metadata_obj(obj) -> str:
    content_type_id = ContentType.objects.get_for_model(obj).pk
    return get_unit_id_format(UNIT_ID_METADATA_ID, str(content_type_id), str(obj.pk))


def get_unit_id_format(*fields: Any) -> str:
    return UNIT_ID_DELIMITER.join(map(str, fields))
