import logging
from contextlib import suppress
from functools import partial
from typing import Generator, List, Tuple, Type

from cms.extensions import extension_pool
from cms.models import CMSPlugin, Page, Placeholder, PlaceholderField, StaticPlaceholder
from django.db.models import (
    CharField,
    Field,
    Model,
    OneToOneField,
    SlugField,
    TextField,
    URLField,
)
from django.utils import translation
from django.utils.translation import gettext as _

from djangocms_xliff.exceptions import XliffExportError
from djangocms_xliff.settings import (
    FIELD_EXTRACTORS,
    FIELDS,
    MODEL_METADATA_FIELDS,
    TITLE_METADATA_FIELDS,
    UNIT_ID_METADATA_ID,
    VALIDATORS,
)
from djangocms_xliff.types import Unit, XliffObj
from djangocms_xliff.utils import get_plugin_id_for_extension_obj, get_type_with_path

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

        source = field.value_from_object(instance)
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


def get_model_placeholders(obj: Type[Model]):
    placeholders = []
    for field in obj._meta.fields:
        field_type = type(field)

        if field_type == PlaceholderField or (field_type == OneToOneField and field.related_model == StaticPlaceholder):
            placeholder = getattr(obj, field.name)
            if placeholder:
                placeholders.append(placeholder.draft)
    return placeholders


def get_placeholders(obj: XliffObj):
    if type(obj) == Page:
        return get_declared_page_placeholders(obj)
    else:
        return get_model_placeholders(obj)


def get_metadata_fields(obj: XliffObj) -> Tuple[XliffObj, dict]:
    obj_type = type(obj)

    if obj_type == Page:
        fields = TITLE_METADATA_FIELDS
        target_obj = obj.get_title_obj()
    else:
        fields = {f.name: f.verbose_name for f in obj._meta.fields}
        target_obj = obj

    excluded_fields = MODEL_METADATA_FIELDS.get(obj_type, {}).get("exclude", [])
    for excluded_field in excluded_fields:
        fields.pop(excluded_field, None)

    return target_obj, fields


def extract_metadata_from_obj(
    obj: XliffObj, language: str, plugin_id: str, plugin_type: str, plugin_name: str
) -> List[Unit]:
    with translation.override(language):
        target_obj, fields = get_metadata_fields(obj)

        model_unit = partial(Unit, plugin_id=plugin_id, plugin_type=plugin_type, plugin_name=plugin_name)

        units = []
        for field_name, field_verbose_name in fields.items():
            target_obj_field = target_obj._meta.get_field(field_name)

            if not is_field_to_translate(target_obj_field, target_obj):
                continue

            source = target_obj_field.value_from_object(target_obj)
            if not source:
                continue

            target_obj_field_type = type(target_obj_field)
            if target_obj_field_type in FIELD_EXTRACTORS:
                units.extend(
                    FIELD_EXTRACTORS[target_obj_field_type](instance=target_obj, field=target_obj_field, source=source)
                )
            else:
                units.append(
                    model_unit(
                        field_name=target_obj_field.name,
                        field_type=get_type_with_path(target_obj_field),
                        field_verbose_name=field_verbose_name,
                        source=target_obj_field.value_from_object(target_obj),
                        max_length=target_obj_field.max_length,
                    )
                )
        return units


def extract_extension_data_from_obj(obj, language: str) -> List[Unit]:
    plugin_id = get_plugin_id_for_extension_obj(obj)
    return extract_metadata_from_obj(
        obj=obj,
        language=language,
        plugin_id=plugin_id,
        plugin_type=obj._meta.object_name,
        plugin_name=obj._meta.verbose_name,
    )


def extract_extension_data_from_page(obj: XliffObj, language: str) -> List[Unit]:
    with translation.override(language):
        units = []
        for title_extension_class in extension_pool.title_extensions:
            with suppress(title_extension_class.DoesNotExist):
                instance = title_extension_class.objects.get(
                    extended_object__page=obj, extended_object__language=language
                )
                units.extend(extract_extension_data_from_obj(obj=instance, language=language))

        # In rare cases it makes sense to use translated fields on page extensions
        for page_extension_class in extension_pool.page_extensions:
            with suppress(page_extension_class.DoesNotExist):
                instance = page_extension_class.objects.get(extended_object=obj)
                units.extend(extract_extension_data_from_obj(obj=instance, language=language))

        return units


def extract_units_from_obj(obj: XliffObj, language: str, include_metadata=True) -> List[Unit]:
    plugin_units = []

    for placeholder in get_placeholders(obj):
        logger.debug(
            f"Placeholder: {placeholder.pk}, is_static={placeholder.is_static}, "
            f"is_editable={placeholder.is_editable}, label={placeholder.get_label()}"
        )
        plugin_units.extend(extract_units_from_placeholder(placeholder, language))

    if len(plugin_units) == 0:
        raise XliffExportError(_("No plugins found. You need to copy plugins from an existing page"))

    metadata_units = []
    if include_metadata:
        metadata_units.extend(
            extract_metadata_from_obj(
                obj=obj,
                language=language,
                plugin_id=UNIT_ID_METADATA_ID,
                plugin_type=UNIT_ID_METADATA_ID,
                plugin_name=UNIT_ID_METADATA_ID,
            )
        )

    extension_data_units = []
    if type(obj) == Page:
        extension_data_units.extend(extract_extension_data_from_page(obj, language))

    return [*metadata_units, *extension_data_units, *plugin_units]
