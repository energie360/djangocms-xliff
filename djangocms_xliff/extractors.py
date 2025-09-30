import logging
from collections.abc import Callable, Generator
from contextlib import suppress
from typing import cast

from cms.extensions import extension_pool
from cms.models import (
    CMSPlugin,
    PageContent,
    Placeholder,
    PlaceholderRelationField,
    StaticPlaceholder,
)
from cms.templatetags.cms_tags import DeclaredPlaceholder
from cms.utils.placeholder import get_declared_placeholders_for_obj as _get_declared_placeholders_for_obj_original
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
from django.utils.translation import gettext
from djangocms_alias.models import AliasContent

from djangocms_xliff.exceptions import XliffExportError
from djangocms_xliff.settings import (
    FIELD_EXTRACTORS,
    FIELDS,
    METADATA_FIELDS,
    MODEL_METADATA_FIELDS,
    VALIDATORS,
)
from djangocms_xliff.types import Unit, XliffObj
from djangocms_xliff.utils import (
    get_plugin_id_for_extension_obj,
    get_plugin_id_for_metadata_obj,
    get_type_with_path,
    must_get_model_for_alias_content,
)

logger = logging.getLogger(__name__)


def has_translatable_type(field: Field) -> bool:
    return type(field) in [CharField, TextField, URLField, SlugField, *FIELDS]


def is_not_cms_default(name: str) -> bool:
    return name not in ["language", "path", "plugin_type", "rte"]


def has_no_choices(field: Field) -> bool:
    return getattr(field, "choices", None) is None


def is_field_to_translate(field: Field, instance: CMSPlugin) -> bool:
    default_validators = [
        has_translatable_type(field),
        is_not_cms_default(field.name),
        has_no_choices(field),
    ]
    validators = [validator(field, instance) for validator in VALIDATORS]
    return all(default_validators + validators)


def extract_units_from_plugin_instance(instance: CMSPlugin) -> list[Unit]:
    units = []

    for field in instance._meta.get_fields():
        field = cast(Field, field)

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
                    field_type=get_type_with_path(field),  # type: ignore
                    field_verbose_name=field.verbose_name,  # type: ignore
                    source=source,
                    max_length=field.max_length,
                )
            )
    return units


def extract_units_from_plugin(cms_plugin: CMSPlugin) -> list[Unit]:
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


def extract_units_from_placeholder(placeholder: Placeholder, language: str) -> list[Unit]:
    units = []

    cms_plugins = placeholder.get_plugins(language).filter(parent__isnull=True).order_by("position")

    for cms_plugin in cms_plugins:
        logger.debug(f"Plugin: {cms_plugin.pk}, type={cms_plugin.plugin_type}")
        units += extract_units_from_plugin(cms_plugin)
    return units


def get_declared_placeholders_for_obj(obj: XliffObj) -> list[DeclaredPlaceholder]:
    from cms.templatetags.cms_tags import DeclaredPlaceholder

    if isinstance(obj, AliasContent):
        return [DeclaredPlaceholder(slot=obj.name, inherit=False)]

    return _get_declared_placeholders_for_obj_original(obj=obj)


def get_page_content_placeholders(page_content: PageContent) -> Generator[Placeholder]:
    declared_placeholders_slots = [pl.slot for pl in get_declared_placeholders_for_obj(page_content)]
    logger.debug(f"Declared placeholders in page: {declared_placeholders_slots}")

    for declared_placeholders_slot in declared_placeholders_slots:
        yield page_content.placeholders.get(slot=declared_placeholders_slot)


def get_alias_placeholders(alias_content: AliasContent) -> Generator[Placeholder]:
    declared_placeholders_slots = [pl.slot for pl in get_declared_placeholders_for_obj(alias_content)]
    logger.debug(f"Alias placeholders in page: {declared_placeholders_slots}")

    for declared_placeholders_slot in declared_placeholders_slots:
        yield alias_content.placeholders.get(slot=declared_placeholders_slot)


def get_model_placeholders(obj: type[Model]):
    placeholders = []
    for field in obj._meta.fields:
        field_type = type(field)

        if field_type in [PlaceholderRelationField] or (
            field_type == OneToOneField and field.related_model == StaticPlaceholder
        ):
            placeholder = getattr(obj, field.name, None)
            if not placeholder:
                continue

            draft = getattr(placeholder, "draft", None)
            if draft:
                placeholders.append(draft)
            else:
                placeholders.append(placeholder)

    return placeholders


def get_placeholders(obj: XliffObj):
    if type(obj) is PageContent:
        return get_page_content_placeholders(obj)
    elif type(obj) is AliasContent:
        return get_alias_placeholders(obj)
    else:
        return get_model_placeholders(obj)  # type: ignore


def get_metadata_fields(obj: XliffObj) -> tuple[XliffObj, dict]:
    target_obj = obj

    if type(obj) is PageContent:
        fields = METADATA_FIELDS.copy()
    elif type(obj) is AliasContent:
        fields = METADATA_FIELDS.copy()
        target_obj = must_get_model_for_alias_content(obj)  # type: ignore
    else:
        fields = {f.name: f.verbose_name for f in obj._meta.fields}

    if target_obj is None:
        raise XliffExportError(gettext(f"Did not find metadata for obj: {type(obj)}"))

    model_metadata_fields = MODEL_METADATA_FIELDS.get(type(target_obj), {})
    if model_metadata_fields:
        included_fields = model_metadata_fields.get("include", {})
        for included_field, included_field_verbose_name in included_fields.items():
            fields[included_field] = included_field_verbose_name

        excluded_fields = model_metadata_fields.get("exclude", [])
        for excluded_field in excluded_fields:
            fields.pop(excluded_field, None)

    return target_obj, fields


def extract_metadata_from_obj(obj, language: str, plugin_id_func: Callable | None = None) -> list[Unit]:
    with translation.override(language):
        target_obj, fields = get_metadata_fields(obj)

        final_units = []

        for field_name, field_verbose_name in fields.items():
            # The slug for PageContent is not on the content, we need to lookup the PageUrl model
            if field_name == "slug" and type(obj) is PageContent:
                units = extract_units_from_obj_by_field_name(
                    obj=obj.page.get_url_obj(language),
                    field_name=field_name,
                    field_verbose_name=field_verbose_name,
                    plugin_id_func=plugin_id_func,
                )
            else:
                units = extract_units_from_obj_by_field_name(
                    obj=target_obj,
                    field_name=field_name,
                    field_verbose_name=field_verbose_name,
                    plugin_id_func=plugin_id_func,
                )

            final_units.extend(units)

        return final_units


def extract_units_from_obj_by_field_name(
    obj: XliffObj,
    field_name: str,
    field_verbose_name: str,
    plugin_id_func: Callable | None = None,
) -> list[Unit]:
    plugin_id = plugin_id_func(obj) if plugin_id_func else get_plugin_id_for_metadata_obj(obj)

    target_obj_field = obj._meta.get_field(field_name)

    if not is_field_to_translate(target_obj_field, obj):  # type: ignore
        return []

    source = target_obj_field.value_from_object(obj)
    if not source:
        return []

    target_obj_field_type = type(target_obj_field)
    if target_obj_field_type in FIELD_EXTRACTORS:
        return FIELD_EXTRACTORS[target_obj_field_type](instance=obj, field=target_obj_field, source=source)

    return [
        Unit(
            plugin_id=plugin_id,
            plugin_type=obj._meta.object_name or "",
            plugin_name=obj._meta.verbose_name or "",
            field_name=target_obj_field.name,
            field_type=get_type_with_path(target_obj_field),  # type: ignore
            field_verbose_name=field_verbose_name,
            source=target_obj_field.value_from_object(obj),
            max_length=target_obj_field.max_length,
        )
    ]


def extract_extension_data_from_page(obj: XliffObj, language: str) -> list[Unit]:
    obj = cast(PageContent, obj)
    page = obj.page

    with translation.override(language):
        units = []
        title_extensions = extension_pool.page_content_extensions
        for title_extension_class in title_extensions:
            with suppress(title_extension_class.DoesNotExist):
                instance = title_extension_class.objects.get(
                    extended_object__page=page,
                    extended_object__language=language,
                )
                units.extend(
                    extract_metadata_from_obj(
                        obj=instance,
                        language=language,
                        plugin_id_func=get_plugin_id_for_extension_obj,
                    )
                )

        # In rare cases it makes sense to use translated fields on page extensions
        for page_extension_class in extension_pool.page_extensions:
            with suppress(page_extension_class.DoesNotExist):
                instance = page_extension_class.objects.get(extended_object=page)
                units.extend(
                    extract_metadata_from_obj(
                        obj=instance,
                        language=language,
                        plugin_id_func=get_plugin_id_for_extension_obj,
                    )
                )

        return units


def extract_units_from_obj(
    obj: XliffObj,
    language: str,
    include_metadata=True,
    allow_empty_plugins=False,
) -> list[Unit]:
    plugin_units = []

    for placeholder in get_placeholders(obj):
        logger.debug(
            f"Placeholder: {placeholder.pk}, is_static={placeholder.is_static}, "
            f"is_editable={placeholder.is_editable}, label={placeholder.get_label()}"
        )
        plugin_units.extend(extract_units_from_placeholder(placeholder, language))

    if not allow_empty_plugins and len(plugin_units) == 0:
        raise XliffExportError(gettext("No plugins found. You need to copy plugins from an existing page"))

    metadata_units = []
    if include_metadata:
        metadata_units.extend(extract_metadata_from_obj(obj=obj, language=language))

    extension_data_units = []
    if type(obj) is PageContent:
        extension_data_units.extend(extract_extension_data_from_page(obj, language))

    return [*metadata_units, *extension_data_units, *plugin_units]
