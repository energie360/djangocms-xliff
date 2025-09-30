import logging

from cms.models import CMSPlugin, PageUrl
from django.contrib.contenttypes.models import ContentType
from django.utils import translation
from django.utils.translation import gettext
from djangocms_alias.models import AliasContent

from djangocms_xliff.exceptions import XliffImportError
from djangocms_xliff.settings import (
    FIELD_IMPORTERS,
    UNIT_ID_DELIMITER,
    UNIT_ID_EXTENSION_DATA_ID,
    UNIT_ID_METADATA_ID,
)
from djangocms_xliff.types import Unit, XliffContext, XliffObj
from djangocms_xliff.utils import (
    get_lang_name,
    get_obj,
    map_units_by_plugin_id,
    must_get_model_for_alias_content,
)

logger = logging.getLogger(__name__)


def save_xliff_units_for_metadata(units: list[Unit], target_language: str) -> None:
    with translation.override(target_language):
        for unit in units:
            _, content_type_id, instance_id = unit.plugin_id.split(UNIT_ID_DELIMITER)
            obj = get_obj(int(content_type_id), instance_id)

            if type(obj) is PageUrl and unit.field_name == "slug":
                # Slug is not on the PageContent so we need to handle it differently
                path = obj.page.get_path_for_slug(unit.target, target_language)
                obj.page.update_urls(language=target_language, path=path)

            elif type(obj) is AliasContent:
                obj = must_get_model_for_alias_content(obj)

            if obj is None:
                raise XliffImportError(gettext("Did not find metadata for obj: %(obj_type)s") % {"obj_type": type(obj)})

            target = unit.target
            setattr(obj, unit.field_name, target)
            obj.save()  # type: ignore


def save_xliff_units_for_cms_plugin(units: list[Unit], plugin_id: str) -> None:
    try:
        cms_plugin = CMSPlugin.objects.get(pk=plugin_id)
    except CMSPlugin.DoesNotExist:
        logger.debug(f"Found plugin with id: {plugin_id} in xliff, but not in database")
        return

    instance, _ = cms_plugin.get_plugin_instance()

    for unit in units:
        field_name = unit.field_name
        target = unit.target

        if unit.field_type in FIELD_IMPORTERS:
            instance = FIELD_IMPORTERS[unit.field_type](instance=instance, unit=unit)
        else:
            setattr(instance, field_name, target)

    instance.save()  # type: ignore


def save_xliff_context(xliff_context: XliffContext) -> None:
    for plugin_id, units in xliff_context.grouped_units:
        if plugin_id.startswith(UNIT_ID_METADATA_ID):
            save_xliff_units_for_metadata(units, xliff_context.target_language)
        elif plugin_id.startswith(UNIT_ID_EXTENSION_DATA_ID):
            save_xliff_units_for_metadata(units, xliff_context.target_language)
        else:
            save_xliff_units_for_cms_plugin(units, plugin_id)


def validate_page_with_xliff_context(xliff_context: XliffContext, current_language: str) -> None:
    xliff_target_language = xliff_context.target_language
    if xliff_target_language != current_language:
        error_message = gettext(
            'Current page language: "%(page_language)s" is not the same as '
            'xliff target language: "%(xliff_target_language)s"'
        )
        error_params = {
            "page_language": get_lang_name(current_language),
            "xliff_target_language": get_lang_name(xliff_target_language),
        }
        raise XliffImportError(error_message % error_params)


def validate_units_max_lengths(units: list[Unit]):
    for unit in units:
        if unit.is_max_length_exceeded():
            error_message = gettext(
                'Text in "%(field_name)s" with content "%(target)s" has too many characters. '
                "Should be %(max_length)s, but is %(target_length)s"
            )
            error_params = {
                "field_name": unit.field_verbose_name,
                "target": unit.target,
                "max_length": unit.max_length,
                "target_length": unit.target_length,
            }
            raise XliffImportError(error_message % error_params)


def validate_tool_id(obj: XliffObj, xliff_context: XliffContext) -> None:
    content_type_id = ContentType.objects.get_for_model(obj).pk
    obj_id = obj.pk

    if content_type_id != xliff_context.content_type_id and obj_id != xliff_context.obj_id:
        error_message = gettext(
            "Current page with content type id: %(content_type_id)s and obj id: %(obj_id)s is not the same as "
            "xliff content type id: %(xliff_content_type_id)s and obj id: %(xliff_obj_id)s. "
            "You can only import to the same page you exported from."
        )
        error_params = {
            "content_type_id": content_type_id,
            "obj_id": obj_id,
            "xliff_content_type_id": xliff_context.content_type_id,
            "xliff_obj_id": xliff_context.obj_id,
        }
        raise XliffImportError(error_message % error_params)


def validate_xliff(obj: XliffObj, xliff_context: XliffContext, current_language: str) -> None:
    validate_units_max_lengths(xliff_context.units)
    validate_page_with_xliff_context(xliff_context, current_language)
    validate_tool_id(obj, xliff_context)


def compare_units(
    units_to_import: list[Unit],
    units_from_database: list[Unit],
) -> list[Unit]:
    units_to_import_by_plugin = map_units_by_plugin_id(units_to_import)
    units_from_database_by_plugin = map_units_by_plugin_id(units_from_database)

    final_units: list[Unit] = []

    for plugin_id, import_units in units_to_import_by_plugin.items():
        logger.debug(f"Comparing units for plugin with id: {plugin_id}")

        if plugin_id not in units_from_database_by_plugin:
            logger.debug(f"Found plugin with id: {plugin_id} in xliff, but not in database")
            continue

        database_units = units_from_database_by_plugin[plugin_id]
        if len(database_units) != len(import_units):
            logger.debug(
                f"Found {len(import_units)} units for plugin with id: {plugin_id} in xliff, "
                f"but {len(database_units)} in database",
            )

        database_units_by_field_name = {unit.field_name: unit for unit in database_units}

        for import_unit in import_units:
            logger.debug(f'Comparing field "{import_unit.plugin_name}"."{import_unit.field_name}"')
            if import_unit.field_name not in database_units_by_field_name:
                logger.debug(
                    f'Found field "{import_unit.plugin_name}"."{import_unit.field_name}" in xliff, but not in database'
                )
                continue

            database_unit = database_units_by_field_name[import_unit.field_name]

            if import_unit.target == database_unit.source:
                logger.debug(
                    f'Field "{import_unit.plugin_name}"."{import_unit.field_name}" has same text in xliff and database'
                )
                continue

            final_units.append(import_unit)

    return final_units
