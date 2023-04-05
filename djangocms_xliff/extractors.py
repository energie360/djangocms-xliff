import logging
from functools import partial
from typing import Generator, List

from cms.models import CMSPlugin, Page, Placeholder, StaticPlaceholder
from django.db.models import CharField, Field, SlugField, TextField, URLField
from django.utils.translation import gettext as _

from djangocms_xliff.exceptions import XliffExportError
from djangocms_xliff.settings import (
    FIELD_EXTRACTORS,
    FIELDS,
    UNIT_ID_METADATA_ID,
    VALIDATORS,
)
from djangocms_xliff.types import Unit
from djangocms_xliff.utils import get_type_with_path

logger = logging.getLogger(__name__)


def has_translatable_type(field: Field) -> bool:
    return type(field) in [CharField, TextField, URLField, SlugField, *FIELDS]


def is_not_cms_default(name: str) -> bool:
    return name not in ["language", "path", "plugin_type"]


def has_no_choices(field: Field) -> bool:
    return field.choices is None


def is_field_to_translate(field: Field, instance: CMSPlugin) -> bool:
    default_validators = [
        has_translatable_type(field),
        is_not_cms_default(field.name),
        has_no_choices(field),
    ]
    validators = [validator(field, instance) for validator in VALIDATORS]
    return all(default_validators + validators)


def extract_units_from_plugin_instance(instance: CMSPlugin) -> List[Unit]:
    units = []

    for field in instance._meta.fields:
        if not is_field_to_translate(field, instance):
            continue

        source = getattr(instance, field.name, None)
        if not source:
            continue

        field_type = type(field)
        if field_type in FIELD_EXTRACTORS:
            units.extend(FIELD_EXTRACTORS[field_type](instance=instance, field=field, source=source))
        else:
            units.append(
                Unit(
                    plugin_id=str(instance.pk),
                    plugin_type=instance.plugin_type,
                    plugin_name=instance.get_plugin_name(),
                    field_name=field.name,
                    field_type=get_type_with_path(field),
                    field_verbose_name=field.verbose_name,
                    source=source,
                    max_length=field.max_length,
                )
            )
    return units


def extract_units_from_plugin(cms_plugin: CMSPlugin) -> List[Unit]:
    # Get the real DB instance of the given plugin.
    instance, _ = cms_plugin.get_plugin_instance()

    if not instance:
        return []

    # Extract the translation units from the plugin.
    units = extract_units_from_plugin_instance(instance=instance)

    # Extract the units from all child plugins too.
    for child_plugin in instance.get_children().order_by("position"):
        units += extract_units_from_plugin(child_plugin)

    return units


def extract_units_from_placeholder(placeholder: Placeholder, language: str) -> List[Unit]:
    units = []
    for cms_plugin in placeholder.get_child_plugins(language).order_by("position"):
        logger.debug(f"Plugin: {cms_plugin.pk}, type={cms_plugin.plugin_type}")
        units += extract_units_from_plugin(cms_plugin)
    return units


def get_declared_page_placeholders(page: Page) -> Generator[Placeholder, None, None]:
    declared_placeholders_slots = [pl.slot for pl in page.get_declared_placeholders()]
    logger.debug(f"Declared placeholders in page: {declared_placeholders_slots}")

    declared_static_placeholders = [pl.slot for pl in page.get_declared_static_placeholders({})]
    logger.debug(f"Static placeholders in page: {declared_static_placeholders}")

    for declared_placeholders_slot in declared_placeholders_slots:
        yield page.placeholders.get(slot=declared_placeholders_slot)

    for declared_static_placeholder in declared_static_placeholders:
        yield StaticPlaceholder.objects.get(code=declared_static_placeholder).draft


def extract_page_metadata(page: Page, language: str) -> List[Unit]:
    metadata_fields = {
        "title": _("Title"),
        "slug": _("Slug"),
        "menu_title": _("Menu Title"),
        "page_title": _("Page Title"),
        "meta_description": _("Description meta tag"),
    }

    page_unit = partial(
        Unit, plugin_id=UNIT_ID_METADATA_ID, plugin_type=UNIT_ID_METADATA_ID, plugin_name=UNIT_ID_METADATA_ID
    )

    title = page.get_title_obj(language=language)

    units = []
    for metadata_field, metadata_field_description in metadata_fields.items():
        title_field = title._meta.get_field(metadata_field)

        if not is_field_to_translate(title_field, title):
            continue

        title_field_name = title_field.name

        source = getattr(title, title_field_name, None)
        if not source:
            continue

        units.append(
            page_unit(
                field_name=title_field_name,
                field_type=get_type_with_path(title_field),
                field_verbose_name=metadata_field_description,
                source=source,
                max_length=title_field.max_length,
            )
        )

    return units


def extract_units_from_page(page: Page, language: str, include_metadata: bool = True) -> List[Unit]:
    plugin_units = []

    for placeholder in get_declared_page_placeholders(page):
        logger.debug(
            f"Placeholder: {placeholder.pk}, is_static={placeholder.is_static}, "
            f"is_editable={placeholder.is_editable}, label={placeholder.get_label()}"
        )
        plugin_units.extend(extract_units_from_placeholder(placeholder, language))

    if len(plugin_units) == 0:
        raise XliffExportError(_("No plugins found. You need to copy plugins from an existing page"))

    page_units = []
    if include_metadata:
        page_units.extend(extract_page_metadata(page, language))

    return [*page_units, *plugin_units]
