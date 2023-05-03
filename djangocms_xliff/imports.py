import logging
from typing import List

from cms.models import CMSPlugin, Page
from django.utils import translation
from django.utils.translation import gettext as _

from djangocms_xliff.exceptions import XliffImportError
from djangocms_xliff.settings import (
    FIELD_IMPORTERS,
    UNIT_ID_DELIMITER,
    UNIT_ID_EXTENSION_DATA_ID,
    UNIT_ID_METADATA_ID,
)
from djangocms_xliff.types import Unit, XliffContext, XliffObj
from djangocms_xliff.utils import get_lang_name, get_obj

logger = logging.getLogger(__name__)


def save_xliff_units_for_metadata(units: List[Unit], obj: XliffObj, target_language: str) -> None:
    with translation.override(target_language):
        if type(obj) == Page:
            obj = obj.get_title_obj()

        for unit in units:
            field_name = unit.field_name
            target = unit.target

            setattr(obj, field_name, target)

        obj.save()


def save_xliff_units_for_extension_data(units: List[Unit], target_language: str) -> None:
    with translation.override(target_language):
        for unit in units:
            content_type_id, instance_id, field_name = unit.field_name.split(UNIT_ID_DELIMITER)
            obj = get_obj(int(content_type_id), int(instance_id))

            target = unit.target
            setattr(obj, field_name, target)
            obj.save()


def save_xliff_units_for_cms_plugin(units: List[Unit], plugin_id: str) -> None:
    try:
        cms_plugin = CMSPlugin.objects.get(pk=plugin_id)
    except CMSPlugin.DoesNotExist:
        logger.debug(f"Found plugin with id: {plugin_id} in xliff, but not in database")
        return

    instance, plugin = cms_plugin.get_plugin_instance()

    for unit in units:
        field_name = unit.field_name
        target = unit.target

        if unit.field_type in FIELD_IMPORTERS:
            instance = FIELD_IMPORTERS[unit.field_type](instance=instance, unit=unit)
        else:
            setattr(instance, field_name, target)

    instance.save()


def save_xliff_context(xliff_context: XliffContext) -> None:
    for plugin_id, units in xliff_context.grouped_units:
        if plugin_id == UNIT_ID_METADATA_ID:
            save_xliff_units_for_metadata(units, xliff_context.obj, xliff_context.target_language)
        elif plugin_id.startswith(UNIT_ID_EXTENSION_DATA_ID):
            save_xliff_units_for_extension_data(units, xliff_context.target_language)
        else:
            save_xliff_units_for_cms_plugin(units, plugin_id)


def validate_page_with_xliff_context(obj: XliffObj, xliff_context: XliffContext, current_language: str):
    obj_id = obj.id
    xliff_obj_id = xliff_context.obj_id
    if obj_id != xliff_obj_id:
        error_message = _('Selected page id: "%(obj_id)s" is not the same as xliff page id: "%(xliff_obj_id)s"')
        error_params = {"obj_id": obj_id, "xliff_obj_id": xliff_obj_id}
        raise XliffImportError(error_message % error_params)

    xliff_target_language = xliff_context.target_language
    if xliff_target_language != current_language:
        error_message = _(
            'Current page language: "%(page_language)s" is not the same as '
            'xliff target language: "%(xliff_target_language)s"'
        )
        error_params = {
            "page_language": get_lang_name(current_language),
            "xliff_target_language": get_lang_name(xliff_target_language),
        }
        raise XliffImportError(error_message % error_params)


def validate_units_max_lengths(units: List[Unit]):
    for unit in units:
        if unit.is_max_length_exceeded():
            error_message = _(
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


def validate_xliff(obj: XliffObj, xliff_context: XliffContext, current_language: str) -> None:
    validate_units_max_lengths(xliff_context.units)
    validate_page_with_xliff_context(obj, xliff_context, current_language)
