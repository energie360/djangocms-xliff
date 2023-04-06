import logging
from typing import List

from cms.models import CMSPlugin, Page, Title
from django.utils.translation import gettext as _

from djangocms_xliff.exceptions import XliffImportError
from djangocms_xliff.settings import FIELD_IMPORTERS, UNIT_ID_METADATA_ID
from djangocms_xliff.types import Unit, XliffContext
from djangocms_xliff.utils import get_lang_name

logger = logging.getLogger(__name__)


def save_xliff_units_for_page(units: List[Unit], target_title_obj: Title) -> None:
    for unit in units:
        field_name = unit.field_name
        target = unit.target

        setattr(target_title_obj, field_name, target)

    target_title_obj.save()


def save_xliff_units_for_cms_plugins(units: List[Unit], plugin_id: str) -> None:
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
    page = xliff_context.page
    target_title_obj = page.get_title_obj(language=xliff_context.target_language)

    for plugin_id, units in xliff_context.grouped_units:
        if plugin_id == UNIT_ID_METADATA_ID:
            save_xliff_units_for_page(units, target_title_obj)
        else:
            save_xliff_units_for_cms_plugins(units, plugin_id)


def validate_page_with_xliff_context(page: Page, xliff_context: XliffContext, current_language: str):
    page_id = page.pk
    xliff_page_id = xliff_context.page_id
    if page_id != xliff_page_id:
        error_message = _('Selected page id: "%(page_id)s" is not the same as xliff page id: "%(xliff_page_id)s"')
        error_params = {
            "page_id": page_id,
            "xliff_page_id": xliff_page_id,
        }
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


def validate_xliff(page: Page, xliff_context: XliffContext, current_language: str) -> None:
    validate_units_max_lengths(xliff_context.units)
    validate_page_with_xliff_context(page, xliff_context, current_language)
